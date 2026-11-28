# Application Layer Protocols: HTTP, HTTPS, DNS, SMTP, FTP and SSH

## 1. Application Layer in Network Communication

The application layer provides communication services to software applications operating across networked systems.

It defines how application processes identify one another, exchange structured messages, interpret responses, authenticate communication partners and transfer application data.

Application layer protocols operate above the transport layer. They generally use TCP or UDP, depending on their communication requirements.

The six protocols implemented in this project serve different purposes:

| Protocol | Full name | Default port | Transport | Primary function |
|---|---|---:|---|---|
| HTTP | Hypertext Transfer Protocol | 80 | TCP | Web communication |
| HTTPS | HTTP Secure | 443 | TCP | Encrypted web communication |
| DNS | Domain Name System | 53 | UDP/TCP | Domain name resolution |
| SMTP | Simple Mail Transfer Protocol | 587 | TCP | Email submission |
| FTP | File Transfer Protocol | 21 | TCP | File transfer |
| SSH | Secure Shell | 22 | TCP | Secure remote administration |

The implementations distinguish protocol definitions, communication state, security requirements, validation and application-level processing.

## 2. Application Protocol Architecture

The general communication architecture is:

Application process
    |
Application layer protocol
    |
Transport layer: TCP or UDP
    |
Internet layer: IP
    |
Network interface
    |
Physical network

The application protocol defines message structure and application-level behavior. The transport protocol provides the underlying communication service.

For example, an HTTPS request contains HTTP semantics, while TLS protects the communication channel and TCP provides the reliable byte stream used by traditional HTTP/1.1 and HTTP/2 deployments.

The protocol registry in the implementations stores default ports, transport types, encryption properties and operational purposes.

A port number identifies a transport-layer service endpoint. It does not independently guarantee that a service is available or secure.

## 3. HTTP: Hypertext Transfer Protocol

HTTP is a stateless application-layer request-response protocol.

A client sends a request to a server. The server processes the request and returns a response.

### 3.1 HTTP request structure

An HTTP/1.1 request consists of:

- Request method.
- Request target.
- HTTP version.
- Headers.
- Optional message body.

Example request:

`GET /api/products HTTP/1.1`

Important request methods include:

| Method | Purpose |
|---|---|
| GET | Retrieve a resource |
| POST | Submit data or initiate processing |
| PUT | Replace a resource representation |
| PATCH | Partially modify a resource |
| DELETE | Request resource deletion |
| HEAD | Retrieve response headers without the response body |
| OPTIONS | Discover communication options |

### 3.2 HTTP response structure

An HTTP response contains:

- HTTP version.
- Status code.
- Reason phrase in HTTP/1.1.
- Response headers.
- Optional response body.

Important status-code categories:

| Range | Meaning |
|---|---|
| 1xx | Informational |
| 2xx | Successful |
| 3xx | Redirection |
| 4xx | Client error |
| 5xx | Server error |

Examples include:

- `200 OK`
- `201 Created`
- `301 Moved Permanently`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `500 Internal Server Error`
- `503 Service Unavailable`

### 3.3 HTTP statelessness

HTTP does not inherently require a server to retain application state between independent requests.

Applications can maintain state using cookies, sessions, authentication tokens and server-side storage.

Statelessness simplifies request processing and supports horizontal scaling, although session management introduces additional application responsibilities.

### 3.4 Implementation

The Python implementation uses `http.client.HTTPConnection` for HTTP and `http.client.HTTPSConnection` for HTTPS.

It supports:

- Request method validation.
- URL validation.
- Request headers.
- Request bodies.
- Response status codes.
- Response headers.
- Bounded response reading.
- Connection cleanup.
- Configurable timeouts.

The JavaScript implementation uses Node.js HTTP and HTTPS modules with Promise-based response processing.

It also enforces a response-size limit and rejects invalid URL schemes.

Neither implementation assumes that a successful TCP connection automatically means that the HTTP request succeeded. The HTTP response status must be examined separately.

## 4. HTTPS: HTTP Secure

HTTPS is HTTP communication protected by TLS.

It provides three principal security properties:

1. Confidentiality: protects application data against unauthorized observation.
2. Integrity: detects unauthorized modification of protected communication.
3. Authentication: verifies the server identity through certificate validation.

### 4.1 TLS communication

A simplified TLS communication sequence is:

Client
  |
ClientHello
  |
ServerHello and certificate
  |
Certificate validation
  |
Key establishment
  |
Secure communication
  |
Encrypted HTTP messages

Modern TLS versions negotiate cryptographic algorithms and establish session keys using authenticated key exchange.

TLS 1.3 reduces handshake complexity compared with earlier TLS versions.

### 4.2 Certificate validation

A certificate-validation process examines:

- Certificate validity period.
- Certificate chain.
- Trusted certification authority.
- Hostname matching.
- Certificate constraints.
- Cryptographic signatures.

A valid certificate does not establish that the application itself is trustworthy. It establishes an authenticated relationship between the server identity and its certificate under the applicable trust model.

### 4.3 HTTPS versus HTTP

| Characteristic | HTTP | HTTPS |
|---|---|---|
| Default port | 80 | 443 |
| TLS protection | No | Yes |
| Confidentiality | Not provided by HTTP | Provided by TLS |
| Integrity protection | Not provided by HTTP | Provided by TLS |
| Server authentication | Not provided by HTTP | Supported by certificate validation |

HTTPS does not prevent every application-layer attack. Input validation, authorization, secure session management and appropriate server configuration remain necessary.

The implementations reject unverified HTTPS certificates rather than silently accepting them.

## 5. DNS: Domain Name System

DNS translates domain names into information required by network applications.

For example:

`example.com`

may resolve to:

`192.0.2.10`

DNS is a distributed hierarchical naming system.

### 5.1 DNS hierarchy

The DNS namespace can be represented as:

Root
  |
Top-level domain
  |
Second-level domain
  |
Subdomain
  |
Host or service

A resolver may contact multiple DNS servers while obtaining the final answer.

### 5.2 DNS query process

A typical resolution sequence is:

1. An application requests the address of a hostname.
2. The operating system or resolver checks available caches.
3. A recursive resolver receives the query.
4. The resolver obtains the required information from authoritative DNS infrastructure or its cache.
5. The resolver returns the result.
6. The result may be cached according to its TTL.

### 5.3 DNS record types

| Record | Function |
|---|---|
| A | Maps a hostname to an IPv4 address |
| AAAA | Maps a hostname to an IPv6 address |
| CNAME | Defines a canonical name alias |
| MX | Identifies mail exchange servers |
| NS | Identifies authoritative name servers |
| SOA | Stores authoritative zone information |
| PTR | Supports reverse DNS lookups |
| TXT | Stores text-based DNS information |

### 5.4 DNS TTL

Time to Live specifies how long a DNS record may be cached.

A high TTL can reduce repeated DNS queries but can delay the propagation of changes through caches.

A low TTL permits faster cache expiration but can increase query traffic.

The Python implementation includes:

- DNS hostname validation.
- DNS name encoding.
- DNS name decoding.
- Compression-pointer processing.
- Transaction identifier validation.
- UDP DNS queries.
- A and AAAA response parsing.
- TTL-aware caching.

The DNS decoder detects truncated messages and invalid compression pointers.

The JavaScript implementation uses Node.js DNS resolution functions and an in-memory expiration cache.

The C++ and Java implementations provide separate DNS record-management models for application-level storage and retrieval.

These data repositories are not substitutes for an authoritative DNS server or a complete recursive resolver.

### 5.5 UDP and TCP in DNS

Traditional DNS queries commonly use UDP port 53.

TCP port 53 is also used, including for zone transfers and responses that require TCP fallback.

Modern DNS deployments also use encrypted DNS transports such as DNS over TLS and DNS over HTTPS.

DNS over HTTPS is a distinct use of HTTP-based transport for DNS messages. It does not change the underlying DNS record semantics.

## 6. SMTP: Simple Mail Transfer Protocol

SMTP is used to submit and relay electronic mail.

It is a command-response protocol with defined communication states.

### 6.1 SMTP communication sequence

A simplified authenticated submission sequence is:

Client
  |
Server greeting
  |
EHLO
  |
STARTTLS
  |
TLS handshake
  |
EHLO
  |
AUTH
  |
MAIL FROM
  |
RCPT TO
  |
DATA
  |
Message transfer
  |
QUIT

### 6.2 Important SMTP commands

| Command | Function |
|---|---|
| HELO | Introduces an SMTP client |
| EHLO | Introduces an extended SMTP client |
| MAIL FROM | Specifies the envelope sender |
| RCPT TO | Specifies a recipient |
| DATA | Starts message-content transmission |
| RSET | Resets the current mail transaction |
| NOOP | Requests a basic server response |
| QUIT | Ends the SMTP session |
| STARTTLS | Requests TLS negotiation |

SMTP envelope addresses are distinct from the visible From and To headers in an email message.

### 6.3 SMTP submission and relay

SMTP submission commonly uses port 587 with STARTTLS.

Port 25 is generally used for server-to-server mail transfer.

Port 465 is commonly used for SMTP submission over implicit TLS.

The protocol itself does not establish the complete authenticity of an email sender. SPF, DKIM and DMARC provide complementary email authentication and domain-policy mechanisms.

### 6.4 Implementation

The Python implementation uses:

- `smtplib`
- `EmailMessage`
- `SMTP.starttls()`
- Authentication
- Sender validation
- Recipient validation
- Recipient-refusal handling

The JavaScript implementation models SMTP as an event-driven state machine.

It prevents invalid state transitions, such as attempting message submission before authentication or specifying recipients before the sender.

The Java implementation uses a separate SMTP transaction object with recipient-set management.

The state-machine models demonstrate transaction sequencing. They do not implement a complete SMTP server.

## 7. FTP: File Transfer Protocol

FTP is a client-server protocol designed for file transfer.

Traditional FTP uses separate connections for control and data communication.

### 7.1 FTP control and data channels

The control channel normally uses TCP port 21.

The data channel carries directory listings and file contents.

Two major operating modes exist.

**Active FTP**

The client establishes a control connection and provides a data endpoint. The server initiates the data connection toward the client.

**Passive FTP**

The client establishes both the control and data connections.

Passive FTP is generally easier to operate through client-side firewalls and NAT environments.

### 7.2 FTP commands

| Command | Purpose |
|---|---|
| USER | Supplies username |
| PASS | Supplies password |
| LIST | Requests directory listing |
| RETR | Retrieves a file |
| STOR | Uploads a file |
| CWD | Changes working directory |
| PWD | Displays current directory |
| TYPE | Sets transfer representation |
| PASV | Requests passive mode |
| QUIT | Terminates the session |

### 7.3 FTP security limitations

Traditional FTP does not encrypt credentials or file contents.

FTPS adds TLS protection to FTP communication.

SFTP is different. It is an SSH-based file-transfer protocol and does not use FTP as its underlying protocol.

This distinction is important:

| Mechanism | Underlying protocol |
|---|---|
| FTP | FTP over TCP |
| FTPS | FTP protected by TLS |
| SFTP | SSH-based file transfer |

The Python implementation uses `ftplib.FTP_TLS` when TLS protection is selected and enables protected data connections with `prot_p()`.

The JavaScript and Java implementations model secure transfer configuration and governance rather than implementing a complete file-transfer client.

## 8. SSH: Secure Shell

SSH provides secure remote communication and administration.

It is widely used for:

- Remote command execution.
- Server administration.
- Secure file transfer through SFTP.
- Port forwarding.
- Secure tunnelling.
- Automated infrastructure management.

### 8.1 SSH architecture

SSH communication involves:

1. Transport-layer establishment.
2. Server host authentication.
3. Key exchange.
4. Encryption and integrity protection.
5. User authentication.
6. Application-channel operation.

### 8.2 SSH authentication

Common authentication mechanisms include:

- Password authentication.
- Public-key authentication.
- SSH agent authentication.
- Certificate-based authentication.

Public-key authentication avoids transmitting the private key to the server.

The private key must remain protected.

### 8.3 Host-key verification

SSH host-key verification protects against connecting to an unexpected or impersonated server.

The client compares the server's presented host key against its trusted host-key records.

Disabling host-key verification can expose a connection to man-in-the-middle attacks.

The Python implementation invokes the system OpenSSH client with:

- Batch-mode authentication.
- Strict host-key checking.
- Connection timeouts.
- Argument-list execution rather than shell interpolation.
- Bounded command length.

The C++ and Java implementations include host-key verification as an explicit policy condition.

## 9. Protocol Differences and Relationships

The six protocols solve different application-level problems.

| Dimension | HTTP | HTTPS | DNS | SMTP | FTP | SSH |
|---|---|---|---|---|---|---|
| Main purpose | Web access | Secure web access | Name resolution | Email transfer | File transfer | Remote administration |
| Default port | 80 | 443 | 53 | 587 | 21 | 22 |
| Typical transport | TCP | TCP | UDP/TCP | TCP | TCP | TCP |
| Encryption | No | TLS | Not inherent | STARTTLS or implicit TLS | Not inherent | Built-in |
| Typical interaction | Request-response | Request-response | Query-response | Command-response | Command-response | Secure channels |

A protocol's default port does not determine its entire security configuration.

For example, DNS may operate through encrypted transports, and FTP can use TLS through FTPS.

## 10. Python Implementation Architecture

The Python file provides executable protocol clients and supporting protocol models.

| Component | Responsibility |
|---|---|
| `ProtocolResult` | Standardized operation results |
| `DNSCache` | TTL-aware DNS caching |
| `DNSClient` | DNS packet construction and parsing |
| `HTTPClient` | HTTP and HTTPS communication |
| `SMTPWorkflow` | Authenticated email submission |
| `FTPWorkflow` | FTP and FTPS directory access |
| `SSHWorkflow` | OpenSSH remote command execution |
| `PROTOCOLS` | Protocol metadata registry |

### Important implementation decisions

DNS uses binary packet construction through `struct`.

The response parser validates transaction identifiers, response flags, question sections and answer boundaries.

The DNS cache uses monotonic time for expiration calculations, avoiding errors caused by changes to the system clock.

HTTP and HTTPS use explicit connection cleanup and certificate verification.

SMTP uses STARTTLS before authentication.

FTP uses protected data connections when FTPS is selected.

SSH delegates cryptographic transport and host-key handling to OpenSSH rather than implementing cryptography independently.

The validation tests execute without requiring external network access.

Actual network operations require reachable services and appropriate authentication.

## 11. JavaScript Implementation Architecture

The JavaScript file emphasizes asynchronous communication and event-driven protocol management.

| Component | Responsibility |
|---|---|
| `ProtocolRegistry` | Protocol definitions |
| `ProtocolMonitor` | Event collection and metrics |
| `NetworkPolicy` | Network access decisions |
| `DNSResolver` | DNS resolution and caching |
| `WebClient` | HTTP and HTTPS requests |
| `SMTPTransaction` | SMTP state transitions |
| `FTPConfiguration` | FTP/FTPS configuration |
| `SSHConfiguration` | SSH security configuration |
| `ProtocolApplication` | Application orchestration |

### Event-driven processing

The monitoring system emits:

- `protocol-event`
- `protocol-failure`

A consumer can subscribe to these events to implement logging, alerting and operational reporting.

Promises provide asynchronous control flow for DNS queries and HTTP requests.

The HTTP client also enforces response-size limits and connection timeouts.

### Policy evaluation

The policy engine separates network-access decisions from protocol execution.

This design allows the same policy to be applied to multiple application components without duplicating security rules.

The implementation also records failed policy decisions.

## 12. C++17 Governance Engine

The C++17 implementation emphasizes domain modeling, deterministic policy evaluation and state management.

### Main components

| Component | Responsibility |
|---|---|
| `ProtocolRegistry` | Protocol metadata |
| `NetworkEndpoint` | Validated endpoint |
| `ProtocolRequest` | Application operation |
| `ProtocolPolicy` | Governance configuration |
| `PolicyEngine` | Eligibility evaluation |
| `ProtocolConnection` | Connection state |
| `DNSDatabase` | DNS record storage |
| `ProtocolAudit` | Operational audit |
| `ProtocolGovernanceService` | Application orchestration |

### Policy evaluation

A request is checked against:

- Allowed protocols.
- Permitted destination ports.
- Encryption requirements.
- Authentication requirements.
- Payload limits.
- HTTPS certificate verification.
- SSH host-key verification.

A policy decision contains an acceptance result and a list of violations.

This is preferable to returning only a Boolean because multiple security failures may be relevant to a single rejected request.

### State management

The connection state machine uses explicit states:

`DISCONNECTED → CONNECTING → CONNECTED → AUTHENTICATED → CLOSED`

Invalid transitions produce exceptions.

This prevents application logic from assuming that authentication or communication has succeeded when the required preceding state has not been reached.

## 13. Java 17 Enterprise Architecture

The Java implementation uses records, enums, immutable policy objects, repository classes and service-layer separation.

### Domain model

The application separates:

- Protocol definitions.
- Network endpoints.
- DNS records.
- Protocol requests.
- Enterprise policies.
- Policy decisions.
- Connection sessions.
- Audit records.

### Immutable policy configuration

`ProtocolPolicy` uses immutable sets.

This prevents accidental modification of permitted protocols and ports after the policy has been constructed.

### Service separation

`ProtocolPolicyService` evaluates security requirements.

`ProtocolApplicationService` coordinates requests and audit persistence.

`DNSRepository` manages DNS records.

`AuditRepository` provides filtering and aggregation.

`ProtocolSession` controls connection state transitions.

The separation of these responsibilities makes the enterprise model easier to test and extend.

The Java implementation uses in-memory repositories. It does not claim to provide persistent database storage or real network transport.

## 14. PostgreSQL Database Architecture

The SQL implementation models protocol governance through a relational database.

### Entity relationships

Organizations
    |
    +---- Users
    |
    +---- Endpoints
    |
    +---- DNS Records
    |
    +---- Protocol Policies
              |
              +---- Policy Protocols
              |
              +---- Policy Ports

Protocol Requests
    |
    +---- Protocol Connections
    |
    +---- Protocol Audit

Protocols
    |
    +---- Protocol Requests
    |
    +---- Policy Protocols

### Table responsibilities

| Table | Purpose |
|---|---|
| `protocols` | Application protocol registry |
| `organizations` | Organizational ownership |
| `users` | User and role information |
| `endpoints` | Network service endpoints |
| `dns_records` | DNS record management |
| `protocol_policies` | Security policy definitions |
| `policy_protocols` | Protocol permissions |
| `policy_ports` | Permitted destination ports |
| `protocol_requests` | Requested application operations |
| `protocol_connections` | Connection lifecycle |
| `protocol_audit` | Historical request events |

### Referential integrity

Primary keys uniquely identify database entities.

Foreign keys enforce relationships between organizations, users, endpoints, policies and protocol requests.

Check constraints enforce port ranges, positive payload limits and DNS record conditions.

Unique constraints prevent duplicate organization usernames, email addresses and endpoint definitions.

### Database indexes

Indexes support:

- Endpoint hostname searches.
- IP address searches.
- DNS record retrieval.
- Request-status reporting.
- Organization-based filtering.
- Protocol-specific analysis.
- Audit-event retrieval.

GIN indexing supports searches over structured JSONB audit information.

### Stored functions

`evaluate_protocol_request()` determines whether a request satisfies its assigned policy.

It checks organizational ownership, policy activation, protocol permissions, port permissions, encryption, authentication, payload size and applicable certificate or SSH host-key verification.

`process_protocol_request()` locks the request row, evaluates eligibility and updates the request status.

A successful request creates a connection record.

The procedure rejects requests that are not pending.

### Triggers

`audit_request_changes()` records request creation and status changes.

The audit table retains operational information independently of the current request status.

### Transaction management

The request-processing procedure executes within the caller's transaction.

`SELECT ... FOR UPDATE` prevents concurrent transactions from processing the same pending request without coordination.

The final demonstration uses a savepoint and rollback to show how reversible database changes can be isolated.

## 15. Security Considerations

Application protocol security requires controls at several levels.

| Security area | Relevant control |
|---|---|
| Transport confidentiality | TLS or SSH encryption |
| Server identity | TLS certificate validation |
| SSH server identity | Host-key verification |
| User identity | Authentication |
| Application access | Authorization |
| DNS integrity | DNSSEC where applicable |
| Email authenticity | SPF, DKIM and DMARC |
| File transfer | FTPS or SFTP |
| Network exposure | Firewall and port restrictions |
| Operational visibility | Logging and audit records |

Important limitations include:

- Encryption does not replace authorization.
- Authentication does not guarantee that a requested operation is safe.
- A trusted certificate does not guarantee application integrity.
- DNS caching can preserve outdated records until expiration.
- FTP and HTTP should not be used for sensitive information without suitable protection.
- SSH private keys require secure storage.
- Credentials must not be embedded in source code.
- Audit logs should not contain passwords, private keys, access tokens or sensitive message contents.

The SQL implementation uses illustrative organizational records and does not store actual credentials.

## 16. Failure Conditions and Edge Cases

| Protocol | Failure condition | Appropriate handling |
|---|---|---|
| HTTP | Invalid request or server error | Inspect status and response |
| HTTPS | Invalid certificate | Reject connection |
| DNS | NXDOMAIN or timeout | Report resolution failure |
| DNS | Expired cache entry | Perform fresh lookup |
| SMTP | Recipient rejected | Record recipient failure |
| SMTP | Authentication failure | Terminate submission |
| FTP | Data connection failure | Close and report transfer failure |
| FTP | TLS negotiation failure | Reject protected transfer |
| SSH | Unknown host key | Reject connection |
| SSH | Authentication failure | Terminate session |
| All | Network timeout | Apply bounded retry policy where safe |

Retries require care.

Read-only DNS and HTTP requests may be suitable for retrying under appropriate conditions.

Email submission and other state-changing operations require duplicate-submission safeguards because a timeout does not necessarily establish that the remote operation failed.

## 17. Performance and Scalability

Performance depends on network latency, DNS caching, connection establishment, encryption, payload size and server processing.

### DNS

Caching reduces repeated resolution operations.

A cache must respect record expiration and account for negative responses if negative caching is implemented.

### HTTP and HTTPS

Connection reuse can reduce repeated TCP and TLS handshake overhead.

Response-size limits protect applications from excessive memory consumption.

Concurrent request processing improves throughput when the workload is network-bound.

### SMTP

Connection reuse can reduce repeated authentication and TLS handshake costs.

Mail submission systems should use queues, delivery tracking and retry policies.

### FTP

Large file transfers benefit from streaming instead of loading complete files into memory.

Passive-mode port ranges must be configured appropriately in firewalls.

### SSH

Connection multiplexing can reduce repeated connection-establishment costs.

Administrative sessions should use bounded execution times and controlled authentication.

### Database

Indexes accelerate frequent lookups but increase write and storage costs.

For large audit tables, partitioning by time can improve maintenance and reporting performance.

## 18. Testing and Execution

### Python

Requirements: Python 3.10 or later.

Run:

`python application_protocols.py`

The validation tests exercise:

- DNS hostname validation.
- DNS encoding and decoding.
- Cache retrieval.
- HTTP request validation.
- Protocol metadata.
- IP address classification.

The demonstration does not require external network access.

Actual HTTP, HTTPS, DNS, SMTP, FTP and SSH operations require appropriate network services.

### JavaScript

Requirements: Node.js 18 or later.

Run:

`node application_protocols.js`

The demonstration exercises:

- Protocol metadata.
- Network policy evaluation.
- DNS resolution.
- SMTP state transitions.
- SSH configuration validation.
- FTPS configuration.
- Event-driven monitoring.

DNS resolution requires network connectivity.

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic application_protocols.cpp -o protocol_lab`

Run:

`./protocol_lab`

On Windows, run:

`protocol_lab.exe`

The program uses only the C++ standard library.

### Java 17

Compile:

`javac --release 17 ApplicationProtocolEnterprise.java`

Run:

`java ApplicationProtocolEnterprise`

The application uses Java standard-library features without third-party dependencies.

### PostgreSQL

Execute the SQL script using a PostgreSQL 15 or later database.

The script creates the `protocol_lab` schema, domain types, tables, constraints, indexes, stored functions, stored procedures, triggers and sample records.

It also executes the workflow and produces validation and reporting queries.

The SQL script uses a transaction and commits the completed database setup.

## 19. Technical Limitations

The six implementations have deliberately different scopes.

| Implementation | Primary scope | Important limitation |
|---|---|---|
| Python | Protocol clients and DNS packet processing | SSH depends on installed OpenSSH |
| JavaScript | Asynchronous communication and monitoring | FTP and SSH are configuration models |
| C++17 | Policy evaluation and connection state | No real network transport |
| Java 17 | Enterprise domain and service architecture | In-memory repositories |
| PostgreSQL | Relational governance and auditing | Does not implement network protocols |

The implementations demonstrate application-layer protocol concepts and operational governance. They are not complete replacements for production DNS servers, mail transfer agents, web servers, FTP servers or SSH servers.

The protocol registry, state machines, security checks, database constraints and audit mechanisms provide distinct perspectives on how application protocols are defined, implemented, controlled and monitored.
