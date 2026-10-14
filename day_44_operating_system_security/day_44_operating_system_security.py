#!/usr/bin/env python3
"""
Operating System Security: Authentication, Authorization, Access Control, and Permissions.

A self-contained Python 3 implementation of operating-system security concepts.
The simulation models users, groups, credentials, resources, file permissions,
authentication failures, account lockout, access-control decisions, audit events,
and privilege-escalation attempts.

This is an educational policy simulator. It does not change actual operating
system accounts, passwords, file permissions, or security settings.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import asdict, dataclass, field
from enum import Enum, IntFlag
from pathlib import Path
from typing import Iterable


class Permission(IntFlag):
    NONE = 0
    EXECUTE = 1
    WRITE = 2
    READ = 4


class ResourceType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    SERVICE = "service"
    SECRET = "secret"


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Account:
    username: str
    salt: bytes
    password_hash: bytes
    groups: set[str] = field(default_factory=set)
    enabled: bool = True
    locked_until: float = 0.0
    failed_attempts: int = 0
    mfa_enabled: bool = False

    @staticmethod
    def derive_password_hash(password: str, salt: bytes) -> bytes:
        if not password:
            raise ValueError("Password must not be empty.")
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 310_000
        )

    @classmethod
    def create(
        cls,
        username: str,
        password: str,
        groups: Iterable[str] = (),
        mfa_enabled: bool = False,
    ) -> "Account":
        if not username or username.strip() != username:
            raise ValueError("Username must be nonempty and trimmed.")
        salt = secrets.token_bytes(16)
        return cls(
            username=username,
            salt=salt,
            password_hash=cls.derive_password_hash(password, salt),
            groups=set(groups),
            mfa_enabled=mfa_enabled,
        )

    def verify_password(self, password: str) -> bool:
        candidate = self.derive_password_hash(password, self.salt)
        return hmac.compare_digest(candidate, self.password_hash)


@dataclass(frozen=True)
class Session:
    session_id: str
    username: str
    issued_at: float
    expires_at: float
    mfa_verified: bool


@dataclass
class Resource:
    path: str
    owner: str
    group: str
    resource_type: ResourceType
    mode: int
    sensitivity: str = "internal"

    def __post_init__(self) -> None:
        if not self.path.startswith("/"):
            raise ValueError("Resource paths must be absolute.")
        if self.mode < 0 or self.mode > 0o777:
            raise ValueError("Mode must be an octal permission value.")
        if len(self.path) > 1 and self.path.endswith("/"):
            self.path = self.path.rstrip("/")


@dataclass(frozen=True)
class AuditEvent:
    timestamp: float
    actor: str
    action: str
    resource: str
    decision: str
    reason: str


class SecurityManager:
    """
    A simplified reference monitor.

    Authentication establishes identity. Authorization evaluates identity,
    groups, ownership, resource permissions, session validity, and explicit
    policy restrictions for each operation.
    """

    def __init__(
        self,
        max_failures: int = 3,
        lockout_seconds: int = 30,
        session_lifetime: int = 3600,
    ) -> None:
        if max_failures < 1 or lockout_seconds < 1 or session_lifetime < 1:
            raise ValueError("Security limits must be positive.")
        self.accounts: dict[str, Account] = {}
        self.resources: dict[str, Resource] = {}
        self.sessions: dict[str, Session] = {}
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self.session_lifetime = session_lifetime
        self.audit_log: list[AuditEvent] = []
        self.denied_actions: set[tuple[str, str]] = set()

    def record(
        self,
        actor: str,
        action: str,
        resource: str,
        decision: Decision,
        reason: str,
    ) -> None:
        self.audit_log.append(
            AuditEvent(
                timestamp=time.time(),
                actor=actor,
                action=action,
                resource=resource,
                decision=decision.value,
                reason=reason,
            )
        )

    def add_account(self, account: Account) -> None:
        if account.username in self.accounts:
            raise ValueError("Account already exists.")
        self.accounts[account.username] = account

    def add_resource(self, resource: Resource) -> None:
        if resource.path in self.resources:
            raise ValueError("Resource already exists.")
        if resource.owner not in self.accounts:
            raise ValueError("Resource owner must be an existing account.")
        self.resources[resource.path] = resource

    def authenticate(
        self,
        username: str,
        password: str,
        mfa_code: str | None = None,
    ) -> Session | None:
        account = self.accounts.get(username)
        now = time.time()

        if account is None:
            self.record(
                username, "authenticate", "-", Decision.DENY,
                "Unknown account",
            )
            return None

        if not account.enabled:
            self.record(
                username, "authenticate", "-", Decision.DENY,
                "Account disabled",
            )
            return None

        if now < account.locked_until:
            self.record(
                username, "authenticate", "-", Decision.DENY,
                "Account temporarily locked",
            )
            return None

        if not account.verify_password(password):
            account.failed_attempts += 1
            if account.failed_attempts >= self.max_failures:
                account.locked_until = now + self.lockout_seconds
                account.failed_attempts = 0
            self.record(
                username, "authenticate", "-", Decision.DENY,
                "Invalid credentials",
            )
            return None

        if account.mfa_enabled and mfa_code != "246810":
            self.record(
                username, "authenticate", "-", Decision.DENY,
                "MFA verification failed",
            )
            return None

        account.failed_attempts = 0
        session = Session(
            session_id=secrets.token_urlsafe(24),
            username=username,
            issued_at=now,
            expires_at=now + self.session_lifetime,
            mfa_verified=account.mfa_enabled,
        )
        self.sessions[session.session_id] = session
        self.record(
            username, "authenticate", "-", Decision.ALLOW,
            "Identity verified",
        )
        return session

    @staticmethod
    def permission_from_mode(mode: int, category: str) -> Permission:
        shifts = {"owner": 6, "group": 3, "other": 0}
        return Permission((mode >> shifts[category]) & 0b111)

    def authorize(
        self,
        session_id: str,
        path: str,
        requested: Permission,
    ) -> bool:
        session = self.sessions.get(session_id)
        actor = session.username if session else "anonymous"

        if session is None:
            self.record(
                actor, requested.name, path, Decision.DENY,
                "Missing or revoked session",
            )
            return False

        if time.time() >= session.expires_at:
            self.sessions.pop(session_id, None)
            self.record(
                actor, requested.name, path, Decision.DENY,
                "Session expired",
            )
            return False

        account = self.accounts.get(actor)
        resource = self.resources.get(path)

        if account is None or not account.enabled:
            self.record(
                actor, requested.name, path, Decision.DENY,
                "Account missing or disabled",
            )
            return False

        if resource is None:
            self.record(
                actor, requested.name, path, Decision.DENY,
                "Resource does not exist",
            )
            return False

        if requested == Permission.NONE:
            self.record(
                actor, "authorize", path, Decision.DENY,
                "Empty permission request",
            )
            return False

        if requested & (Permission.READ | Permission.WRITE | Permission.EXECUTE) != requested:
            self.record(
                actor, "authorize", path, Decision.DENY,
                "Unsupported permission bits",
            )
            return False

        if (actor, path) in self.denied_actions:
            self.record(
                actor, requested.name, path, Decision.DENY,
                "Explicit deny policy",
            )
            return False

        # Unix permission selection is owner OR group OR other, not the
        # union of every class whose identity happens to match.
        if actor == resource.owner:
            granted = self.permission_from_mode(resource.mode, "owner")
        elif resource.group in account.groups:
            granted = self.permission_from_mode(resource.mode, "group")
        else:
            granted = self.permission_from_mode(resource.mode, "other")

        allowed = (granted & requested) == requested
        reason = (
            f"Mode {resource.mode:04o} grants {granted!s}"
            if allowed
            else f"Mode {resource.mode:04o} does not grant {requested!s}"
        )
        self.record(
            actor,
            requested.name,
            path,
            Decision.ALLOW if allowed else Decision.DENY,
            reason,
        )
        return allowed

    def revoke_session(self, session_id: str) -> bool:
        session = self.sessions.pop(session_id, None)
        if session is None:
            return False
        self.record(
            session.username, "revoke_session", "-", Decision.ALLOW,
            "Session revoked",
        )
        return True

    def audit_report(self) -> dict[str, object]:
        denied = [
            asdict(event)
            for event in self.audit_log
            if event.decision == Decision.DENY.value
        ]
        return {
            "total_events": len(self.audit_log),
            "denied_events": len(denied),
            "denials": denied,
        }

    def export_audit(self, destination: Path) -> None:
        # Audit files should be protected by OS-level ownership and permissions.
        destination.write_text(
            json.dumps(
                [asdict(event) for event in self.audit_log],
                indent=2,
            ),
            encoding="utf-8",
        )


def demonstrate_security() -> None:
    print("Operating System Security Demonstration")

    security = SecurityManager(
        max_failures=3,
        lockout_seconds=30,
        session_lifetime=3600,
    )

    security.add_account(Account.create("alice", "Alice-Strong-Password!"))
    security.add_account(
        Account.create(
            "bob",
            "Bob-Strong-Password!",
            groups={"developers"},
        )
    )
    security.add_account(
        Account.create(
            "admin",
            "Admin-Strong-Password!",
            groups={"administrators", "developers"},
            mfa_enabled=True,
        )
    )

    security.add_resource(
        Resource(
            "/srv/project/source.py",
            owner="alice",
            group="developers",
            resource_type=ResourceType.FILE,
            mode=0o640,
        )
    )
    security.add_resource(
        Resource(
            "/srv/project/deploy.sh",
            owner="admin",
            group="administrators",
            resource_type=ResourceType.FILE,
            mode=0o750,
            sensitivity="restricted",
        )
    )
    security.add_resource(
        Resource(
            "/srv/project/public.txt",
            owner="alice",
            group="developers",
            resource_type=ResourceType.FILE,
            mode=0o644,
        )
    )

    alice = security.authenticate("alice", "Alice-Strong-Password!")
    bob = security.authenticate("bob", "Bob-Strong-Password!")
    admin = security.authenticate(
        "admin",
        "Admin-Strong-Password!",
        "246810",
    )

    assert alice is not None
    assert bob is not None
    assert admin is not None

    print(
        "Alice reads source:",
        security.authorize(alice.session_id, "/srv/project/source.py", Permission.READ),
    )
    print(
        "Bob reads source:",
        security.authorize(bob.session_id, "/srv/project/source.py", Permission.READ),
    )
    print(
        "Bob writes source:",
        security.authorize(bob.session_id, "/srv/project/source.py", Permission.WRITE),
    )
    print(
        "Bob executes deployment script:",
        security.authorize(bob.session_id, "/srv/project/deploy.sh", Permission.EXECUTE),
    )
    print(
        "Admin executes deployment script:",
        security.authorize(admin.session_id, "/srv/project/deploy.sh", Permission.EXECUTE),
    )

    security.denied_actions.add(("bob", "/srv/project/public.txt"))
    print(
        "Bob reads explicitly restricted public file:",
        security.authorize(bob.session_id, "/srv/project/public.txt", Permission.READ),
    )

    # Authentication failures trigger temporary lockout.
    for _ in range(3):
        security.authenticate("bob", "incorrect-password")
    print(
        "Bob after failed-login threshold:",
        security.authenticate("bob", "Bob-Strong-Password!") is not None,
    )

    security.revoke_session(alice.session_id)
    print(
        "Alice after session revocation:",
        security.authorize(alice.session_id, "/srv/project/source.py", Permission.READ),
    )

    report = security.audit_report()
    print("Audit totals:", report["total_events"])
    print("Denied events:", report["denied_events"])

    # A real deployment should use a restricted audit directory and append-only
    # centralized logging rather than trusting a local writable JSON file.


if __name__ == "__main__":
    demonstrate_security()
