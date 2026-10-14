import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

/*
 * Enterprise operating-system security governance model.
 *
 * Models authentication state, principal identities, role permissions,
 * access classifications, session lifecycle, authorization policy evaluation,
 * resource immutability, and security audit records.
 *
 * Java 17 or later. This program is an in-memory simulator and does not
 * enforce permissions on the underlying host.
 */

public class OperatingSystemSecurity {
    enum Action {
        READ, WRITE, EXECUTE
    }

    enum Classification {
        PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    }

    enum Effect {
        ALLOW, DENY
    }

    record AuditEvent(
            Instant timestamp,
            String principal,
            String resource,
            Action action,
            Effect effect,
            String reason) {
    }

    static final class SecurityExceptionPolicy extends RuntimeException {
        SecurityExceptionPolicy(String message) {
            super(message);
        }
    }

    static final class Principal {
        private final String username;
        private final Set<String> groups;
        private final Set<String> roles;
        private final Classification clearance;
        private boolean enabled;

        Principal(
                String username,
                Set<String> groups,
                Set<String> roles,
                Classification clearance,
                boolean enabled) {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Username is required.");
            }
            this.username = username;
            this.groups = Set.copyOf(groups);
            this.roles = Set.copyOf(roles);
            this.clearance = Objects.requireNonNull(clearance);
            this.enabled = enabled;
        }

        String username() {
            return username;
        }

        Set<String> groups() {
            return groups;
        }

        Set<String> roles() {
            return roles;
        }

        Classification clearance() {
            return clearance;
        }

        boolean enabled() {
            return enabled;
        }

        void disable() {
            enabled = false;
        }
    }

    record Session(
            String token,
            String username,
            Instant issuedAt,
            Instant expiresAt) {
        Session {
            Objects.requireNonNull(token);
            Objects.requireNonNull(username);
            Objects.requireNonNull(issuedAt);
            Objects.requireNonNull(expiresAt);
            if (!expiresAt.isAfter(issuedAt)) {
                throw new IllegalArgumentException("Invalid session lifetime.");
            }
        }

        boolean validAt(Instant now) {
            return now.isBefore(expiresAt);
        }
    }

    record ProtectedResource(
            String path,
            String owner,
            String group,
            EnumSet<Action> ownerPermissions,
            EnumSet<Action> groupPermissions,
            EnumSet<Action> otherPermissions,
            Classification classification,
            boolean immutable) {

        ProtectedResource {
            if (path == null || !path.startsWith("/")) {
                throw new IllegalArgumentException("Absolute resource path required.");
            }
            Objects.requireNonNull(owner);
            Objects.requireNonNull(group);
            Objects.requireNonNull(classification);

            ownerPermissions = ownerPermissions.clone();
            groupPermissions = groupPermissions.clone();
            otherPermissions = otherPermissions.clone();
        }

        boolean permitsByMode(Principal principal, Action action) {
            if (principal.username().equals(owner)) {
                return ownerPermissions.contains(action);
            }
            if (principal.groups().contains(group)) {
                return groupPermissions.contains(action);
            }
            return otherPermissions.contains(action);
        }
    }

    static final class AuthenticationService {
        private final Map<String, Principal> principals = new HashMap<>();
        private final Map<String, String> passwordDigests = new HashMap<>();
        private final Map<String, Integer> failedAttempts = new HashMap<>();
        private final Map<String, Instant> lockedUntil = new HashMap<>();
        private final Map<String, Session> sessions = new HashMap<>();
        private final Duration sessionLifetime;
        private final Duration lockoutDuration;
        private final int failureLimit;

        AuthenticationService(
                Duration sessionLifetime,
                Duration lockoutDuration,
                int failureLimit) {
            if (sessionLifetime.isNegative() || sessionLifetime.isZero()
                    || lockoutDuration.isNegative() || lockoutDuration.isZero()
                    || failureLimit < 1) {
                throw new IllegalArgumentException("Invalid authentication policy.");
            }
            this.sessionLifetime = sessionLifetime;
            this.lockoutDuration = lockoutDuration;
            this.failureLimit = failureLimit;
        }

        void register(Principal principal, String password) {
            if (principals.containsKey(principal.username())) {
                throw new SecurityExceptionPolicy("Duplicate principal.");
            }
            if (password == null || password.length() < 12) {
                throw new IllegalArgumentException("Password is too short.");
            }
            principals.put(principal.username(), principal);
            passwordDigests.put(principal.username(), digest(password));
        }

        private static String digest(String password) {
            // A digest is used only to keep this example self-contained.
            // Production password storage must use a salted password-hashing
            // scheme such as Argon2id, scrypt, or appropriately configured PBKDF2.
            try {
                var md = java.security.MessageDigest.getInstance("SHA-256");
                byte[] result = md.digest(password.getBytes(
                        java.nio.charset.StandardCharsets.UTF_8));
                return java.util.HexFormat.of().formatHex(result);
            } catch (java.security.NoSuchAlgorithmException e) {
                throw new IllegalStateException("SHA-256 unavailable.", e);
            }
        }

        Session authenticate(String username, String password, Instant now) {
            Principal principal = principals.get(username);
            if (principal == null || !principal.enabled()) {
                throw new SecurityExceptionPolicy("Unknown or disabled principal.");
            }

            Instant lockExpiry = lockedUntil.get(username);
            if (lockExpiry != null && now.isBefore(lockExpiry)) {
                throw new SecurityExceptionPolicy("Account temporarily locked.");
            }

            String candidate = digest(password);
            if (!java.security.MessageDigest.isEqual(
                    candidate.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    passwordDigests.get(username).getBytes(
                            java.nio.charset.StandardCharsets.UTF_8))) {
                int failures = failedAttempts.merge(username, 1, Integer::sum);
                if (failures >= failureLimit) {
                    lockedUntil.put(username, now.plus(lockoutDuration));
                    failedAttempts.put(username, 0);
                }
                throw new SecurityExceptionPolicy("Credential verification failed.");
            }

            failedAttempts.put(username, 0);
            lockedUntil.remove(username);

            Session session = new Session(
                    UUID.randomUUID().toString(),
                    username,
                    now,
                    now.plus(sessionLifetime));
            sessions.put(session.token(), session);
            return session;
        }

        Principal requirePrincipal(Session session, Instant now) {
            Session stored = sessions.get(session.token());
            if (stored == null || !stored.equals(session) || !session.validAt(now)) {
                sessions.remove(session.token());
                throw new SecurityExceptionPolicy("Session invalid, expired, or revoked.");
            }

            Principal principal = principals.get(session.username());
            if (principal == null || !principal.enabled()) {
                throw new SecurityExceptionPolicy("Principal disabled.");
            }
            return principal;
        }

        boolean revoke(String token) {
            return sessions.remove(token) != null;
        }

        void disablePrincipal(String username) {
            Principal principal = principals.get(username);
            if (principal == null) {
                throw new SecurityExceptionPolicy("Principal not found.");
            }
            principal.disable();
            sessions.values().removeIf(s -> s.username().equals(username));
        }
    }

    static final class AuthorizationService {
        private final AuthenticationService authentication;
        private final Map<String, ProtectedResource> resources = new HashMap<>();
        private final Map<String, Set<Action>> rolePermissions = new HashMap<>();
        private final Map<String, Effect> explicitPolicies = new HashMap<>();
        private final List<AuditEvent> audit = new ArrayList<>();

        AuthorizationService(AuthenticationService authentication) {
            this.authentication = authentication;
        }

        void registerRole(String role, Set<Action> permissions) {
            if (role == null || role.isBlank() || rolePermissions.containsKey(role)) {
                throw new SecurityExceptionPolicy("Invalid or duplicate role.");
            }
            rolePermissions.put(role, Set.copyOf(permissions));
        }

        void addResource(ProtectedResource resource) {
            if (resources.putIfAbsent(resource.path(), resource) != null) {
                throw new SecurityExceptionPolicy("Resource already exists.");
            }
        }

        void setExplicitPolicy(String username, String path, Effect effect) {
            if (!resources.containsKey(path)) {
                throw new SecurityExceptionPolicy("Unknown resource.");
            }
            explicitPolicies.put(username + ":" + path, effect);
        }

        boolean authorize(Session session, String path, Action action, Instant now) {
            String username = session.username();
            ProtectedResource resource = resources.get(path);

            try {
                Principal principal = authentication.requirePrincipal(session, now);

                if (resource == null) {
                    return deny(username, path, action, "Resource not found");
                }

                if (explicitPolicies.get(username + ":" + path) == Effect.DENY) {
                    return deny(username, path, action, "Explicit deny policy");
                }

                if (!resource.permitsByMode(principal, action)) {
                    return deny(username, path, action, "File mode denies action");
                }

                if (principal.clearance().ordinal()
                        < resource.classification().ordinal()) {
                    return deny(username, path, action, "Insufficient security clearance");
                }

                boolean roleGrantsAction = principal.roles().stream()
                        .map(rolePermissions::get)
                        .filter(Objects::nonNull)
                        .anyMatch(permissions -> permissions.contains(action));

                if (!roleGrantsAction) {
                    return deny(username, path, action, "No assigned role grants action");
                }

                if (resource.immutable() && action == Action.WRITE) {
                    return deny(username, path, action, "Resource is immutable");
                }

                audit.add(new AuditEvent(
                        now, username, path, action, Effect.ALLOW,
                        "All policy layers passed"));
                return true;
            } catch (SecurityExceptionPolicy ex) {
                return deny(username, path, action, ex.getMessage());
            }
        }

        private boolean deny(
                String username,
                String path,
                Action action,
                String reason) {
            audit.add(new AuditEvent(
                    Instant.now(), username, path, action, Effect.DENY, reason));
            return false;
        }

        List<AuditEvent> deniedEvents() {
            return audit.stream()
                    .filter(event -> event.effect() == Effect.DENY)
                    .toList();
        }

        List<AuditEvent> auditEvents() {
            return List.copyOf(audit);
        }
    }

    public static void main(String[] args) {
        Instant now = Instant.now();

        AuthenticationService authentication = new AuthenticationService(
                Duration.ofMinutes(30),
                Duration.ofMinutes(2),
                3);

        Principal engineer = new Principal(
                "engineer",
                Set.of("engineering"),
                Set.of("maintainer"),
                Classification.CONFIDENTIAL,
                true);

        Principal operator = new Principal(
                "operator",
                Set.of("operations"),
                Set.of("reader"),
                Classification.INTERNAL,
                true);

        Principal administrator = new Principal(
                "administrator",
                Set.of("security"),
                Set.of("deployer"),
                Classification.RESTRICTED,
                true);

        authentication.register(engineer, "Engineer-Password-2026!");
        authentication.register(operator, "Operator-Password-2026!");
        authentication.register(administrator, "Admin-Password-2026!");

        AuthorizationService authorization = new AuthorizationService(authentication);
        authorization.registerRole("reader", Set.of(Action.READ));
        authorization.registerRole("maintainer", Set.of(Action.READ, Action.WRITE));
        authorization.registerRole("deployer", Set.of(Action.READ, Action.EXECUTE));

        authorization.addResource(new ProtectedResource(
                "/srv/app/config.yml",
                "engineer",
                "engineering",
                EnumSet.of(Action.READ, Action.WRITE),
                EnumSet.of(Action.READ),
                EnumSet.noneOf(Action.class),
                Classification.CONFIDENTIAL,
                false));

        authorization.addResource(new ProtectedResource(
                "/srv/app/deploy.sh",
                "administrator",
                "security",
                EnumSet.of(Action.READ, Action.EXECUTE),
                EnumSet.noneOf(Action.class),
                EnumSet.noneOf(Action.class),
                Classification.RESTRICTED,
                false));

        authorization.addResource(new ProtectedResource(
                "/srv/app/release.lock",
                "administrator",
                "security",
                EnumSet.of(Action.READ, Action.WRITE),
                EnumSet.noneOf(Action.class),
                EnumSet.noneOf(Action.class),
                Classification.INTERNAL,
                true));

        Session engineerSession = authentication.authenticate(
                "engineer", "Engineer-Password-2026!", now);
        Session operatorSession = authentication.authenticate(
                "operator", "Operator-Password-2026!", now);
        Session administratorSession = authentication.authenticate(
                "administrator", "Admin-Password-2026!", now);

        System.out.println("Engineer reads configuration: "
                + authorization.authorize(
                        engineerSession, "/srv/app/config.yml", Action.READ, now));

        System.out.println("Engineer writes configuration: "
                + authorization.authorize(
                        engineerSession, "/srv/app/config.yml", Action.WRITE, now));

        System.out.println("Operator reads restricted configuration: "
                + authorization.authorize(
                        operatorSession, "/srv/app/config.yml", Action.READ, now));

        System.out.println("Administrator executes deployment: "
                + authorization.authorize(
                        administratorSession, "/srv/app/deploy.sh", Action.EXECUTE, now));

        System.out.println("Administrator writes immutable lock: "
                + authorization.authorize(
                        administratorSession, "/srv/app/release.lock", Action.WRITE, now));

        authorization.setExplicitPolicy(
                "engineer", "/srv/app/config.yml", Effect.DENY);

        System.out.println("Engineer after explicit denial: "
                + authorization.authorize(
                        engineerSession, "/srv/app/config.yml", Action.READ, now));

        authentication.revoke(engineerSession.token());

        System.out.println("Engineer after session revocation: "
                + authorization.authorize(
                        engineerSession, "/srv/app/config.yml", Action.READ, now));

        System.out.println("Audit events: " + authorization.auditEvents().size());
        System.out.println("Denied events: " + authorization.deniedEvents().size());
    }
}
