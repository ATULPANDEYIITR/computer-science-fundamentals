"use strict";

/*
 * Operating-system security policy engine.
 *
 * This implementation focuses on event-driven access decisions, capability
 * checks, role-based authorization, policy composition, session expiry,
 * and audit correlation. It models security decisions in memory and does
 * not modify actual operating-system accounts or file permissions.
 */

const crypto = require("node:crypto");

const Permission = Object.freeze({
  READ: 1,
  WRITE: 2,
  EXECUTE: 4,
});

const Sensitivity = Object.freeze({
  PUBLIC: "public",
  INTERNAL: "internal",
  CONFIDENTIAL: "confidential",
  RESTRICTED: "restricted",
});

class SecurityError extends Error {
  constructor(message, code) {
    super(message);
    this.name = "SecurityError";
    this.code = code;
  }
}

class AuditTrail {
  #events = [];
  #sequence = 0;

  append(event) {
    this.#events.push(Object.freeze({
      sequence: ++this.#sequence,
      timestamp: new Date().toISOString(),
      ...event,
    }));
  }

  get events() {
    return this.#events.map((event) => ({ ...event }));
  }

  findDenied() {
    return this.#events.filter((event) => event.decision === "DENY");
  }

  countByReason() {
    const counts = new Map();
    for (const event of this.#events) {
      if (event.decision !== "DENY") continue;
      counts.set(event.reason, (counts.get(event.reason) || 0) + 1);
    }
    return Object.fromEntries(counts);
  }
}

class SecurityDirectory {
  #users = new Map();
  #sessions = new Map();
  #resources = new Map();
  #roles = new Map();
  #policies = new Map();

  constructor(audit = new AuditTrail()) {
    this.audit = audit;
  }

  addRole(name, permissions) {
    if (!name || this.#roles.has(name)) {
      throw new SecurityError("Invalid or duplicate role.", "ROLE_INVALID");
    }
    this.#roles.set(name, new Set(permissions));
  }

  addUser({ id, password, roles = [], enabled = true }) {
    if (!id || typeof password !== "string" || password.length < 12) {
      throw new SecurityError(
        "User ID and a password of at least 12 characters are required.",
        "USER_INVALID",
      );
    }
    if (this.#users.has(id)) {
      throw new SecurityError("User already exists.", "USER_DUPLICATE");
    }
    for (const role of roles) {
      if (!this.#roles.has(role)) {
        throw new SecurityError(`Unknown role: ${role}`, "ROLE_UNKNOWN");
      }
    }

    const salt = crypto.randomBytes(16);
    const passwordHash = crypto.scryptSync(password, salt, 64);

    this.#users.set(id, {
      id,
      salt,
      passwordHash,
      roles: new Set(roles),
      enabled,
      failedAttempts: 0,
      lockedUntil: 0,
    });
  }

  addResource({ id, owner, sensitivity, requiredPermissions = [] }) {
    if (!id || this.#resources.has(id) || !this.#users.has(owner)) {
      throw new SecurityError(
        "Resource ID must be unique and owner must exist.",
        "RESOURCE_INVALID",
      );
    }
    if (!Object.values(Sensitivity).includes(sensitivity)) {
      throw new SecurityError("Invalid sensitivity classification.", "SENSITIVITY_INVALID");
    }

    this.#resources.set(id, Object.freeze({
      id,
      owner,
      sensitivity,
      requiredPermissions: Object.freeze([...requiredPermissions]),
    }));
  }

  setPolicy(resourceId, userId, effect) {
    if (!this.#resources.has(resourceId) || !this.#users.has(userId)) {
      throw new SecurityError("Policy references an unknown identity or resource.", "POLICY_INVALID");
    }
    if (!["ALLOW", "DENY"].includes(effect)) {
      throw new SecurityError("Policy effect must be ALLOW or DENY.", "POLICY_EFFECT_INVALID");
    }
    this.#policies.set(`${userId}:${resourceId}`, effect);
  }

  #record(userId, action, resourceId, decision, reason) {
    this.audit.append({ userId, action, resourceId, decision, reason });
  }

  authenticate(userId, password, now = Date.now()) {
    const user = this.#users.get(userId);

    if (!user || !user.enabled || now < user.lockedUntil) {
      this.#record(userId, "AUTHENTICATE", "-", "DENY", "Account unavailable");
      return null;
    }

    const candidate = crypto.scryptSync(password, user.salt, 64);
    if (!crypto.timingSafeEqual(candidate, user.passwordHash)) {
      user.failedAttempts += 1;
      if (user.failedAttempts >= 5) {
        user.lockedUntil = now + 60_000;
        user.failedAttempts = 0;
      }
      this.#record(userId, "AUTHENTICATE", "-", "DENY", "Credential verification failed");
      return null;
    }

    user.failedAttempts = 0;
    const token = crypto.randomBytes(32).toString("base64url");
    const session = Object.freeze({
      token,
      userId,
      issuedAt: now,
      expiresAt: now + 15 * 60_000,
    });
    this.#sessions.set(token, session);
    this.#record(userId, "AUTHENTICATE", "-", "ALLOW", "Credentials verified");
    return token;
  }

  authorize({ token, resourceId, permission, now = Date.now() }) {
    const session = this.#sessions.get(token);
    const userId = session?.userId || "anonymous";

    const deny = (reason) => {
      this.#record(userId, permission, resourceId, "DENY", reason);
      return false;
    };

    if (!session || now >= session.expiresAt) {
      if (session) this.#sessions.delete(token);
      return deny("Session missing or expired");
    }

    const user = this.#users.get(session.userId);
    const resource = this.#resources.get(resourceId);

    if (!user?.enabled || !resource) {
      return deny("Disabled account or unknown resource");
    }

    if (!Object.values(Permission).includes(permission)) {
      return deny("Unknown permission");
    }

    if (this.#policies.get(`${userId}:${resourceId}`) === "DENY") {
      return deny("Explicit deny policy");
    }

    const granted = new Set();
    for (const role of user.roles) {
      for (const item of this.#roles.get(role)) granted.add(item);
    }

    if (userId === resource.owner) {
      granted.add("resource:read");
      granted.add("resource:write");
    }

    const requiredRolePermission = `resource:${permission.toLowerCase()}`;
    if (!granted.has(requiredRolePermission)) {
      return deny("Required role permission missing");
    }

    if (resource.requiredPermissions.length > 0 &&
        !resource.requiredPermissions.every((item) => granted.has(item))) {
      return deny("Resource-specific permission requirement not satisfied");
    }

    this.#record(userId, permission, resourceId, "ALLOW", "Authorization policy satisfied");
    return true;
  }

  revoke(token) {
    const session = this.#sessions.get(token);
    if (!session) return false;
    this.#sessions.delete(token);
    this.#record(session.userId, "REVOKE_SESSION", "-", "ALLOW", "Session revoked");
    return true;
  }
}

function runSecurityScenario() {
  const audit = new AuditTrail();
  const directory = new SecurityDirectory(audit);

  directory.addRole("reader", ["resource:read"]);
  directory.addRole("operator", ["resource:read", "resource:write"]);
  directory.addRole("security-admin", [
    "resource:read",
    "resource:write",
    "resource:execute",
  ]);

  directory.addUser({
    id: "analyst",
    password: "Analyst-Password-2026!",
    roles: ["reader"],
  });
  directory.addUser({
    id: "operator",
    password: "Operator-Password-2026!",
    roles: ["operator"],
  });
  directory.addUser({
    id: "root-operator",
    password: "Root-Operator-Password-2026!",
    roles: ["security-admin"],
  });

  directory.addResource({
    id: "incident-report",
    owner: "analyst",
    sensitivity: Sensitivity.CONFIDENTIAL,
  });
  directory.addResource({
    id: "deployment-service",
    owner: "root-operator",
    sensitivity: Sensitivity.RESTRICTED,
    requiredPermissions: ["resource:execute"],
  });

  const analystToken = directory.authenticate("analyst", "Analyst-Password-2026!");
  const operatorToken = directory.authenticate("operator", "Operator-Password-2026!");
  const adminToken = directory.authenticate("root-operator", "Root-Operator-Password-2026!");

  if (!analystToken || !operatorToken || !adminToken) {
    throw new SecurityError("Scenario account authentication failed.", "SCENARIO_AUTH_FAILED");
  }

  console.log("Analyst reads incident:", directory.authorize({
    token: analystToken,
    resourceId: "incident-report",
    permission: Permission.READ,
  }));

  console.log("Analyst writes incident:", directory.authorize({
    token: analystToken,
    resourceId: "incident-report",
    permission: Permission.WRITE,
  }));

  console.log("Operator writes incident:", directory.authorize({
    token: operatorToken,
    resourceId: "incident-report",
    permission: Permission.WRITE,
  }));

  console.log("Admin executes service:", directory.authorize({
    token: adminToken,
    resourceId: "deployment-service",
    permission: Permission.EXECUTE,
  }));

  directory.setPolicy("incident-report", "operator", "DENY");
  console.log("Operator after explicit deny:", directory.authorize({
    token: operatorToken,
    resourceId: "incident-report",
    permission: Permission.READ,
  }));

  directory.revoke(analystToken);
  console.log("Analyst after revocation:", directory.authorize({
    token: analystToken,
    resourceId: "incident-report",
    permission: Permission.READ,
  }));

  console.log("Denied event count:", audit.findDenied().length);
  console.log("Denials grouped by reason:", audit.countByReason());
}

runSecurityScenario();
