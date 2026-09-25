# Security

What experienced engineers forget about application security before an interview, grouped by subtopic. For AWS IAM and workload credentials, see [aws.md](aws.md); for backend-side input handling, see [backend.md](backend.md).

## Web vulnerabilities

### SQL injection

- Untrusted input becomes SQL syntax. Fix with **parameterized queries**, not hand escaping.
- Identifiers (sort column, table name) can't be bound — **allowlist** them; ORMs don't protect raw fragments.

### XSS

- **Stored** (saved, rendered later), **reflected** (echoed in the response), **DOM-based** (client code turns data into markup or script).
- Fix with **context-aware output encoding** and safe sinks (`textContent`, not `innerHTML`); a **CSP with nonces** limits damage but isn't the primary fix.

### CSRF

- The browser auto-attaches cookies to a forged cross-site request.
- Defend with framework **CSRF tokens** plus `SameSite=Lax`/`Strict` cookies (**Lax is Chrome's default**); XSS defeats CSRF defenses, so it's no substitute.

### SSRF

- The attacker controls where the server sends a request — reaching cloud metadata or internal services.
- Allowlist destinations, validate the **resolved IP**, and pin it for the request to avoid **DNS rebinding**; **IMDSv2** on AWS requires a session token, blocking naive metadata theft.

### Clickjacking

- A hidden frame tricks the user into clicking the real site; block framing with CSP **`frame-ancestors`** (or legacy `X-Frame-Options`).

### CORS

- CORS is a **browser read policy**, not authentication or a firewall — non-browser clients ignore it.
- A credentialed response can't use `Access-Control-Allow-Origin: *`; reflecting any `Origin` with credentials is equivalent to no policy.

### IDOR / BOLA

- The endpoint checks that the caller is logged in but not that they may access **this object ID** — authorize per resource, every time.

## Authentication and sessions

### Password storage

- Use a slow, memory-hard hash: **argon2id**, scrypt, or bcrypt — never a fast hash like SHA-256; store algorithm and parameters with the hash.
- A unique **salt** per password defeats rainbow tables; a **pepper** (server-side secret stored elsewhere) helps if only the database leaks.

### MFA strength

- Phishing resistance: **WebAuthn/passkeys** (bound to the origin) > TOTP app > SMS (SIM swap).

### Cookie flags

- **`HttpOnly`** (no JS access), **`Secure`** (HTTPS only), **`SameSite`** (cross-site sending).
- The **`__Host-`** prefix forces `Secure`, path `/`, and no `Domain`, blocking cookie injection from subdomains.

### Session fixation

- An attacker plants a known session ID before login — always **issue a new session ID** on authentication and privilege change.

### Browser token storage

- **`HttpOnly` cookie**: safe from XSS token theft, needs `SameSite` + CSRF tokens — the default for web apps.
- **In memory**: no CSRF, gone on refresh (needs silent refresh), still usable by a script running on the page.
- **`localStorage`**: any XSS reads it directly — avoid for sensitive tokens.

## Tokens and federation

### JWT validation

- Pin the expected **`alg`**, reject **`none`**, and block **RS/HS confusion** (an RS256 token re-signed as HS256 with the public key as the secret).
- Pick the key by **`kid`** from a trusted set; validate `exp`, `aud`, and `iss` — a valid signature is not authorization.

### JWT revocation

- Stateless tokens can't be revoked in place — use **short expiry** plus refresh-token rotation; a denylist brings back server state.

### OAuth 2.0 vs OIDC

- **OAuth 2.0** is delegated *authorization* (an access token for a resource server); **OIDC** adds *authentication* via an **ID token**.
- Interactive login: **authorization code + PKCE**; service to service: **client credentials**. **OAuth 2.1** drops the implicit and password grants.

### Refresh token rotation

- Each refresh returns a new refresh token and invalidates the old one; reuse of an old token signals theft, so revoke the whole family.

## Access control models

### RBAC, ABAC, ReBAC

| Model | Decision based on | Fits | Weak spot |
|---|---|---|---|
| RBAC | roles | few, stable roles | role explosion from exceptions |
| ABAC | subject/resource/context attributes | fine-grained conditions | needs trustworthy attributes |
| ReBAC | relationship graph ("member of team that owns") | nested sharing (Google Docs, Zanzibar) | graph storage and evaluation cost |

- Enforce **server-side** and **deny by default** — a hidden button is not access control.

## Cryptography

### Encoding vs encryption vs hashing

| | Reversible? | Needs a key? | Purpose |
|---|---|---|---|
| Encoding (Base64) | yes | no | representation |
| Encryption | yes, with the key | yes | confidentiality |
| Hashing | no | no | integrity, fingerprint |

### AES-GCM nonces

- **AES-GCM** is authenticated encryption; **reusing a nonce with the same key** breaks both confidentiality and integrity — nonces must never repeat per key.

### RSA vs ECC and forward secrecy

- ECC gives equal security at far smaller keys (**256-bit EC ≈ 3072-bit RSA**), making signatures and handshakes cheaper.
- **ECDHE** gives **forward secrecy**: a later leak of the long-term key doesn't expose past sessions.

### MAC vs signature

- A **MAC** (HMAC) proves integrity to anyone holding the shared key, so it can't give **non-repudiation**; a **signature** can, since only the private-key holder could sign.
- Naive `hash(key ‖ msg)` is open to **length extension** on Merkle-Damgård hashes (MD5, SHA-1, SHA-256); HMAC isn't.

## TLS

### TLS 1.3 handshake

- **1-RTT** full handshake: key shares go in the first flight.
- Optional **0-RTT** resumption data can be **replayed** — only safe for idempotent requests.

### Certificates and mTLS

- The client validates the **chain to a trusted root** and the hostname; the server proves key ownership by signing the handshake.
- **mTLS**: both sides present certificates — common for service-to-service auth in a mesh.

### HSTS and pinning

- **HSTS** forces HTTPS on later visits after one HTTPS response (preload lists cover the first visit).
- **Certificate pinning** resists CA compromise but makes key rotation painful — mostly limited to mobile apps now.

## Threat modeling

### STRIDE

| STRIDE threat | Violates |
|---|---|
| Spoofing | Authentication |
| Tampering | Integrity |
| Repudiation | Non-repudiation |
| Information disclosure | Confidentiality |
| Denial of service | Availability |
| Elevation of privilege | Authorization |

- STRIDE finds threats at each trust boundary; it doesn't rank them — pair it with impact/likelihood.

### OWASP Top 10:2025

- Broken Access Control, Security Misconfiguration, **Software Supply Chain Failures** (new), Cryptographic Failures, Injection, Insecure Design, Authentication Failures, Software/Data Integrity Failures, Security Logging and Alerting Failures, **Mishandling of Exceptional Conditions** (new).
- An awareness list, not a test checklist — name the edition when citing it.
