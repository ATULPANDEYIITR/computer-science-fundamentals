# Operating System Security: Authentication, Authorization, Access Control, and Permissions

## Technical scope

Operating-system security determines which identities can use a computer, which resources they can access, and which operations they may perform. A process can run under a valid account and still be denied access to a particular file, directory, service, or secret. Secure systems make these decisions at clearly defined boundaries and record enough evidence to investigate failures.

This project models four related mechanisms:

- **Authentication** establishes that an identity has supplied acceptable credentials and, where required, completed additional verification.
- **Authorization** evaluates whether an authenticated identity may perform a particular operation on a particular resource.
- **Access control** provides the policy structures used to make authorization decisions, including ownership, groups, roles, explicit denials, and security classifications.
- **Permissions** represent the specific operations granted or withheld, such as reading a file, modifying its contents, or executing a program.

These mechanisms are related but not interchangeable. A successful login does not imply unrestricted access. Administrative status should not silently bypass every security restriction. File permissions, application roles, resource classifications, account state, and session validity can impose separate conditions.

## Security decision model

The implementations use the following decision sequence:

| Mechanism | Question | Typical failure |
|---|---|---|
| Authentication | Has the identity been verified? | Invalid credentials, lockout, disabled account |
| Session validation | Is the authenticated session still valid? | Expiry, revocation, missing session |
| Discretionary access control | Do ownership, group membership, and file mode permit the operation? | Missing read, write, or execute bit |
| Role-based access control | Does an assigned role grant the requested action? | Role lacks the required permission |
| Mandatory access control | Does the identity have sufficient clearance for the resource? | Resource classification exceeds clearance |
| Explicit policy evaluation | Is there a rule that prohibits the operation? | Principal-specific or group-specific denial |
| Resource-state validation | Is the operation valid for the resource's current state? | Attempt to modify an immutable resource |
| Audit recording | Can the decision be investigated later? | Missing or incomplete security evidence |

A request should be permitted only when every applicable restriction is satisfied. An explicit denial takes precedence over an ordinary grant in the policy models provided here.

## Authentication and identity lifecycle

Authentication must be separate from authorization. Credential verification establishes a principal, while a session represents the temporary authority to make requests as that principal.

The Python implementation uses a random salt and PBKDF2-HMAC-SHA-256 to derive password verifiers. Password comparisons use `hmac.compare_digest`. It models failed-login thresholds, temporary account lockout, an MFA requirement, session expiration, and explicit revocation. The MFA code is deliberately fixed for demonstration and is not a production MFA implementation.

The JavaScript implementation uses Node.js cryptographic functions to generate salts, derive password verifiers with `scryptSync`, compare credential verifiers, issue random session tokens, and remove expired sessions. Its in-memory directory makes identity and session transitions visible without requiring a server.

The Java implementation models registration, credential verification, failed-login counters, temporary lockout, session creation, account disabling, and session revocation. Its simple SHA-256 password digest exists only to keep the example self-contained. An unsalted fast hash is unsuitable for production password storage. A deployed service should use a dedicated password-hashing algorithm, a unique random salt, suitable work parameters, secure secret handling, and a controlled migration policy.

The SQL model separates account state, authentication sessions, and authentication events. Sessions have issuance and expiry timestamps, a revocation timestamp, and an MFA verification indicator. The database records are illustrative: the sample password hashes are explicitly non-credentials, and the sample sessions are seeded data rather than evidence of actual authentication.

### Session security

A session is not valid merely because its identifier exists. The authorization path checks that the session is present, unrevoked, unexpired, and associated with an enabled principal.

Revocation should invalidate subsequent requests. When an account is disabled, associated sessions should also be revoked. A production service may need centralized session state, short-lived access tokens, refresh-token rotation, secure cookie attributes, replay defenses, and reliable propagation of account-disable events.

Random session identifiers must be unpredictable. Applications should never log passwords, authentication secrets, raw access tokens, or MFA recovery codes.

## Unix file permissions

Traditional Unix permissions divide access rights into three classes: owner, group, and other. Each class has read, write, and execute bits.

| Octal digit | Read | Write | Execute |
|---|---:|---:|---:|
| `0` | No | No | No |
| `4` | Yes | No | No |
| `5` | Yes | No | Yes |
| `6` | Yes | Yes | No |
| `7` | Yes | Yes | Yes |

For a regular file, read permits content access, write permits modification, and execute permits execution subject to other system restrictions. Directory permissions have distinct operational meanings: read allows listing directory entries, write allows modifying entries when combined with the relevant directory permissions, and execute allows traversal or lookup. A complete filesystem authorization decision may also depend on parent directories, ACLs, mount options, capabilities, mandatory access-control systems, and the identity of the running process.

The Python implementation models the mode as an integer and extracts the owner, group, or other permission class. The C++ implementation uses bit masks and a mutually exclusive owner/group/other selection. The JavaScript implementation uses role and resource policies rather than attempting to reproduce Unix mode semantics. The Java implementation represents each permission class using an `EnumSet<Action>`.

The SQL representation stores Unix mode values as integers constrained to the range from `0` through `511`, corresponding to octal `0000` through `0777`. For example, decimal `416` represents octal `0640`, and decimal `488` represents octal `0750`.

The class-selection rule matters. If a user owns a file, the owner bits apply even when the user also belongs to the file's group. Group permissions do not simply add to owner permissions. Supplementary groups, ACLs, and filesystem-specific rules can change the complete real-world decision, but those features are outside the simplified mode calculation.

## Discretionary access control and role-based access control

Discretionary access control (DAC) associates resource permissions with an owner and, commonly, a group. A resource owner or privileged administrator can control access within the limits of the operating system's rules.

Role-based access control (RBAC) assigns permissions to roles and assigns roles to identities. A reader may have read permission, a maintainer may have read and write permission, and a deployment role may have read and execute permission. RBAC is useful when an organization needs consistent permissions across many identities.

These mechanisms answer different questions. File ownership and mode determine whether the modeled filesystem layer grants an action. Role permissions determine whether the principal's assigned organizational role grants that action. The C++ and Java implementations require both layers to pass. This is a deliberately restrictive policy model rather than a claim that every Unix system uses RBAC in its native file-access algorithm.

The SQL model normalizes identities, groups, roles, role permissions, resource ownership, and resource policies into separate relations. This avoids embedding an uncontrolled collection of role names or permissions in a single text field. Foreign keys maintain referential integrity when assignments are created or removed.

## Mandatory access control and resource classification

Mandatory access control (MAC) applies system-defined restrictions based on labels or other centrally controlled policy attributes. The case studies classify resources as public, internal, confidential, or restricted.

Each principal has a clearance level. The sample rule denies access when the principal's clearance is lower than the resource's classification. This represents a simplified confidentiality policy, not a complete information-flow security model. Real systems may have separate rules for reading, writing, compartments, need-to-know attributes, trusted processes, and information release.

An administrator's role does not automatically satisfy classification checks. This distinction is important because operational privilege and authorization to view sensitive information are separate responsibilities.

The SQL view evaluates account state, session state, mode permissions, role grants, classification, immutability, and explicit denial policies. The view is an educational evaluation of seeded data. Its classification values are demonstration attributes, not a complete mandatory access-control implementation.

## Python implementation

The Python file models a security manager with `Account`, `Session`, `Resource`, and `AuditEvent` data structures.

`Account.create` generates a random salt and stores a PBKDF2-derived password verifier. `authenticate` checks account state, lockout, credentials, and the demonstration MFA condition before issuing a session. `authorize` verifies the session, account, resource, explicit denial rules, and Unix mode before returning a decision.

The script uses `IntFlag` to represent combinations of permission bits. A read-write request can therefore be checked by requiring all requested bits to be present. It also handles unknown resources, invalid permission requests, missing sessions, disabled accounts, expired sessions, and revoked sessions.

The audit report counts denied operations and returns the associated events. The JSON export method illustrates serialization, but the resulting file is only as trustworthy as its storage location and access controls. Production audit logs should be protected against unauthorized modification and deletion, use reliable timestamps, and be shipped to a controlled logging service when appropriate.

Run the program with Python 3.10 or later:

    python operating_system_security.py

The script uses only the Python standard library. Its account-lockout and MFA behavior is intended for controlled demonstration rather than public-facing authentication.

## JavaScript implementation

The JavaScript file focuses on event recording, role aggregation, explicit policy decisions, and session lifecycle.

`SecurityDirectory` maintains private maps for users, sessions, roles, resources, and explicit policies. Its `authenticate` method derives and compares credential verifiers, applies a failed-login threshold, and creates a random token. `authorize` gathers permissions from assigned roles, checks resource ownership, and evaluates explicit denials before allowing access.

`AuditTrail` assigns a sequence number to each event and can group denials by reason. This supports investigation of patterns such as repeated missing permissions or requests made after session expiry.

The implementation uses Node.js built-in cryptographic functions and requires no npm packages. Its role model differs from the Python mode-based model: it illustrates application-style policy composition and event-driven evaluation rather than attempting to model every Unix filesystem rule.

## C++ case study: enterprise host access-control engine

The C++ program models a server hosting engineering configuration, deployment scripts, and immutable release metadata.

The `Identity` structure holds group membership, clearance, account status, and administrative status. `FileObject` stores ownership, group, Unix mode, classification, and immutability. `Session` represents a verified identity with an expiry time. `AccessControlEngine` coordinates these structures through ordered checks.

The authorization algorithm rejects missing or expired sessions, disabled identities, unknown resources, explicit denials, insufficient mode permissions, insufficient clearance, missing role permissions, and writes to immutable objects. Each decision becomes an `AuditRecord`.

The mode calculation uses bit shifts to select the relevant permission triplet. The implementation uses ordered maps for deterministic lookup and sets for group membership, roles, and explicit denial pairs. With balanced tree maps and sets, common lookups and membership checks take logarithmic time in the number of stored entries. A production system processing high request volumes may choose hash tables or a dedicated policy engine, while accounting for concurrency and memory usage.

The program is compiled with a C++17-or-later compiler. It uses C++17-compatible standard-library features and does not require external dependencies.

The model deliberately does not make the administrative flag an automatic bypass. Real privileged processes may possess capabilities or special operating-system privileges, but those privileges must be represented explicitly when they are part of the security policy.

## Java enterprise model

The Java program separates identity, authentication, session validation, protected resources, and authorization.

`Principal` represents an identity and its assigned roles. `Session` is an immutable record with a bounded lifetime. `ProtectedResource` represents resource ownership, group permissions, other permissions, classification, and immutability. `AuthenticationService` owns account registration and session operations. `AuthorizationService` combines file-mode permissions, role permissions, classification checks, explicit denials, and resource-state restrictions.

The separation makes the policy easier to test. Authentication failures are represented by `SecurityExceptionPolicy`; authorization failures become explicit audit denials. Disabling a principal also removes that principal's active sessions in the simulation.

The implementation uses immutable copies of role and group collections to reduce accidental changes to identity state. Resource permission sets are cloned at construction. These measures prevent some unintended modifications but do not replace a complete concurrency-safe policy store or a production-grade identity provider.

Compile and run the Java file using Java 17 or later:

    javac OperatingSystemSecurity.java
    java OperatingSystemSecurity

## PostgreSQL data model

The SQL script defines the `os_security_lab` schema and the following main relationships:

| Relation | Purpose |
|---|---|
| `security_principal` | Identity, account state, MFA requirement, and lockout state |
| `security_group` | Named collections of identities |
| `principal_group` | Many-to-many group membership |
| `security_role` | Organizational permission roles |
| `role_permission` | Actions granted by each role |
| `principal_role` | Role assignments to identities |
| `protected_resource` | Resource owner, group, mode, type, classification, and immutability |
| `resource_policy` | Principal-specific or group-specific allow/deny policy records |
| `authentication_session` | Session lifetime, revocation, and MFA state |
| `authentication_event` | Successful and failed authentication attempts |
| `access_audit` | Recorded access decisions and their reasons |

Foreign keys prevent assignments from referencing nonexistent principals, groups, roles, or resources. Unique constraints prevent duplicate usernames, role names, resource paths, and membership pairs. Check constraints restrict permission modes, enforce absolute paths, validate session lifetimes, and require a policy to target exactly one principal or group.

Partial indexes accelerate queries for unrevoked sessions and failed authentication events. Additional indexes support denial investigations and policy lookups. These indexes should be selected according to measured query patterns and write volume in a deployed system.

`effective_access_decisions` combines the relevant relations and computes a decision for every seeded session, resource, and action. Its common table expressions separate request construction, Unix permission selection, role checks, and final policy evaluation. The later queries display decisions, persist an audit snapshot, and aggregate failed logins and denied operations.

The transaction demonstrates that account disabling and session revocation can be performed atomically. The sample database is reset when the script runs, so it should be executed only in a dedicated learning database.

### Database enforcement limitations

The view is not a replacement for PostgreSQL row-level security, operating-system permissions, or a trusted authentication service. A view evaluates the query's modeled state; it does not intercept filesystem operations. A production database would need appropriate ownership, schema privileges, transaction boundaries, restricted mutation rights, and potentially row-level security policies to prevent users from bypassing the intended controls.

The demonstration also uses fixed session UUIDs and non-secret credential markers. Production sessions must be generated securely, and authentication records must be issued only after real credential verification.

## Common failure modes and security considerations

### Authentication is not authorization

A successful login proves only that the authentication mechanism accepted the credentials and other required factors. A session still needs to be checked against resource-specific policy. Applications should avoid using a successful login as a universal permission grant.

### File mode is not the complete filesystem policy

Unix mode bits do not capture every relevant restriction. Directory traversal, ACLs, mount flags, process credentials, capabilities, SELinux or AppArmor rules, and namespace boundaries can affect access. The code uses a simplified permission model and should not be treated as a replacement for the host operating system's own access checks.

### Role assignment can create excessive privilege

A broad administrative role can unintentionally give users write or execute rights across unrelated resources. Assign only the permissions required for a person's responsibilities. Separate deployment, administration, and ordinary read access where practical, and periodically review assignments.

### Account lockout requires careful design

Lockout can reduce repeated password guessing, but an attacker may also use it to deny legitimate users access. Production systems should consider progressive delays, rate limits, monitoring, recovery workflows, and identity-provider protections. Failed-login events should not disclose whether a username exists.

### Session revocation must affect future requests

Deleting a local token does not invalidate a copied token if another service continues accepting it. Distributed systems need a consistent revocation strategy, short expiration windows, or server-side checks appropriate to the threat model.

### Audit evidence must be protected

Security logs can contain sensitive identities, resource paths, and operational details. Access to logs should be restricted, timestamps should be trustworthy, and retention should follow the organization's requirements. High-assurance environments may require remote collection, tamper detection, alerting, and separation between administrators who change policy and those who review audit records.

## Production boundary

These implementations teach security policy evaluation and the relationship between identity, permissions, and resource state. They do not modify real host permissions, configure operating-system authentication, enforce kernel-level access checks, implement a complete mandatory access-control system, or provide a production identity service.

Actual enforcement belongs at the appropriate trusted boundary: the operating-system kernel and filesystem for host resources, the database for database records, and the application or identity provider for application-specific actions. A secure deployment must ensure that users cannot bypass the component responsible for enforcing the policy.
