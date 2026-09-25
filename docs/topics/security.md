# Security

What experienced engineers forget about application security before an interview, grouped by subtopic. For AWS IAM and workload credentials, see [aws.md](aws.md); for backend-side input handling, see [backend.md](backend.md).

## Server-side attacks

### SQL injection

- Untrusted input becomes SQL syntax. Fix with **parameterized queries**, not hand escaping.
- Identifiers (sort column, table name) can't be bound — **allowlist** them; ORMs don't protect raw fragments.

### Command and template injection

- **Command injection**: input inside a shell string (`system("convert " + name)`) — pass an argument array with no shell.
- **SSTI**: user input compiled as a template (Jinja2, Twig) runs code on the server — pass it only as template data.
- **XXE**: XML parsers resolving external entities read local files or make requests — disable DTDs and external entities.

### Path traversal and unsafe deserialization

- **Path traversal**: `../../etc/passwd` in a filename escapes the base directory — resolve the canonical path and check it's still inside the base, or map IDs to files.
- **Unsafe deserialization** (Java serialization, Python `pickle`, YAML with object tags) runs attacker-chosen code — only deserialize untrusted input into plain data (JSON) with schema validation.

### SSRF

- The attacker controls where the server sends a request — reaching cloud metadata or internal services.
- Allowlist destinations, validate the **resolved IP**, and pin it for the request to avoid **DNS rebinding**.
- **IMDSv2** on AWS requires a session token, blocking naive metadata theft.

### Prototype pollution

- Merging untrusted JSON with `__proto__` or `constructor.prototype` keys adds properties to **`Object.prototype`** — every object gains them, so checks like `if (user.isAdmin)` can flip.
- Reject those keys, parse into `Map` or `Object.create(null)`, or freeze the prototype.

### HTTP request smuggling

- A proxy and the backend disagree on where a request ends (**`Content-Length` vs `Transfer-Encoding`**), so attacker bytes become the start of the next user's request.
- Reject ambiguous requests at the edge, use HTTP/2 end to end, and keep proxies patched.

## Browser-side attacks

### XSS

- **Stored** (saved, rendered later), **reflected** (echoed in the response), **DOM-based** (client code turns data into markup or script).
- Fix with context-aware output encoding and safe sinks (`textContent`, not `innerHTML`); CSP limits damage but isn't the primary fix.

### Content Security Policy

- A **strict CSP** uses per-response nonces or hashes (`script-src 'nonce-…' 'strict-dynamic'`); host allowlists are routinely bypassed through JSONP endpoints and CDN-hosted gadgets.
- **`'strict-dynamic'`** lets a trusted script load further scripts and makes supporting browsers ignore host allowlists.
- Roll out with `Content-Security-Policy-Report-Only` first.

### CSRF

- The browser auto-attaches cookies to a forged cross-site request.
- Defend with framework **CSRF tokens** plus `SameSite=Lax`/`Strict` cookies (**Lax is Chrome's default**); XSS defeats CSRF defenses, so it's no substitute.

### Clickjacking

- A hidden frame tricks the user into clicking the real site.
- Block framing with CSP **`frame-ancestors`** (or legacy `X-Frame-Options`).

### CORS

- CORS is a **browser read policy**, not authentication or a firewall — non-browser clients ignore it.
- A credentialed response can't use `Access-Control-Allow-Origin: *`; reflecting any `Origin` with credentials is equivalent to no policy.

### Open redirect

- `/login?next=https://evil.example` sends victims to a phishing page through a link on your domain, and can leak OAuth codes.
- Allow only **relative paths** or an allowlist of hosts.

## Authentication and sessions

### Password storage

- Use a slow, memory-hard hash: **argon2id**, scrypt, or bcrypt — never a fast hash like SHA-256; store algorithm and parameters with the hash.
- A unique **salt** per password defeats rainbow tables; a **pepper** (server-side secret stored elsewhere) helps if only the database leaks.

### Password policy (NIST SP 800-63B)

- Rev. 4 (2025): minimum **15 characters** for password-only login (8 with MFA), allow at least 64, **no composition rules**, no forced periodic rotation.
- Check new passwords against breached-password lists; rotate only on evidence of compromise.

### Credential stuffing and enumeration

- **Credential stuffing** replays leaked username/password pairs: rate-limit per account and per IP, add MFA, and check logins against breached-password lists.
- Return the same error and similar timing for "no such user" and "wrong password" to avoid **account enumeration**.

### MFA strength

- Phishing resistance: **WebAuthn/passkeys** > TOTP app > SMS (SIM swap).
- A passkey's private key never leaves the device and its signature covers the **origin**, so a lookalike domain gets nothing usable.

### Cookie flags

- **`HttpOnly`** (no JS access), **`Secure`** (HTTPS only), `SameSite` (cross-site sending).
- The **`__Host-`** prefix forces `Secure`, path `/`, and no `Domain`, blocking cookie injection from subdomains.

### Session fixation

- An attacker plants a known session ID before login, then shares the victim's session once they authenticate.
- Always **issue a new session ID** on authentication and privilege change.

### Browser token storage

- **`HttpOnly` cookie**: safe from XSS token theft, needs `SameSite` + CSRF tokens — the default for web apps.
- In memory: no CSRF, gone on refresh (needs silent refresh), still usable by a script running on the page.
- **`localStorage`**: any XSS reads it directly — avoid for sensitive tokens.

## Tokens and federation

### JWT validation

- Pin the expected **`alg`**, reject `none`, and block **RS/HS confusion** (an RS256 token re-signed as HS256 with the public key as the secret).
- Pick the key by `kid` from a trusted set; validate `exp`, `aud`, and `iss` — a valid signature is not authorization.

### JWT revocation

- Stateless tokens can't be revoked in place — use **short expiry** plus refresh-token rotation.
- A denylist of token IDs works but brings back a server-side lookup on every request.

### OAuth 2.0 vs OIDC

- **OAuth 2.0** is delegated authorization (an access token for a resource server); **OIDC** adds authentication via an ID token.
- Interactive login: **authorization code + PKCE**; service to service: client credentials. OAuth 2.1 drops the implicit and password grants.

### OAuth pitfalls

- Match **`redirect_uri` exactly** against a registered value — prefix or wildcard matching leaks authorization codes.
- The **`state`** parameter (or PKCE) ties the callback to the browser session that started it, blocking login CSRF.
- Bearer tokens work for whoever holds them; **DPoP** or mTLS sender-constrains tokens to a client key.

### Refresh token rotation

- Each refresh returns a **new refresh token** and invalidates the old one.
- Reuse of an old token signals theft, so revoke the whole token family.

## Authorization

### RBAC, ABAC, ReBAC

| Model | Decision based on | Fits | Weak spot |
|---|---|---|---|
| RBAC | roles | few, stable roles | role explosion from exceptions |
| ABAC | subject/resource/context attributes | fine-grained conditions | needs trustworthy attributes |
| ReBAC | relationship graph ("member of team that owns") | nested sharing (Google Docs, Zanzibar) | graph storage and evaluation cost |

- Enforce **server-side** and **deny by default** — a hidden button is not access control.

### IDOR / BOLA

- The endpoint checks that the caller is logged in but not that they may access **this object ID**.
- Authorize per resource on every request; unguessable IDs only hide the bug.

## Cryptography

### Encoding vs encryption vs hashing

| | Reversible? | Needs a key? | Purpose |
|---|---|---|---|
| Encoding (Base64) | yes | no | representation |
| Encryption | yes, with the key | yes | confidentiality |
| Hashing | no | no | integrity, fingerprint |

### AES-GCM nonces

- **AES-GCM** is authenticated encryption: confidentiality plus an integrity tag.
- **Reusing a nonce with the same key** breaks both — nonces must never repeat per key; random 96-bit nonces are safe for about 2³² messages per key.

### RSA vs ECC and forward secrecy

- ECC gives equal security at far smaller keys (**256-bit EC ≈ 3072-bit RSA**), making signatures and handshakes cheaper.
- **ECDHE** gives **forward secrecy**: a later leak of the long-term key doesn't expose past sessions.

### MAC vs signature

- A **MAC** (HMAC) proves integrity to anyone holding the shared key, so it can't give non-repudiation; a **signature** can, since only the private-key holder could sign.
- Naive `hash(key ‖ msg)` is open to **length extension** on Merkle-Damgård hashes (MD5, SHA-1, SHA-256); HMAC isn't.

### Envelope encryption and key management

- Encrypt data with a random **data key (DEK)**, encrypt the DEK with a **key-encryption key (KEK)** held in a KMS/HSM, store the wrapped DEK with the data.
- Rotating the KEK only rewraps DEKs, not the data; the master key never leaves the KMS. AWS specifics: see [aws.md](aws.md).

### Timing attacks

- Comparing secrets (HMACs, tokens) with `==` returns early at the first differing byte, leaking how much matched.
- Use a **constant-time compare** (`hmac.compare_digest`, `crypto.timingSafeEqual`).

## TLS

### TLS 1.3 handshake

- **1-RTT** full handshake: key shares go in the first flight.
- Optional **0-RTT** resumption data can be **replayed** — only safe for idempotent requests.

### Post-quantum key exchange

- **Harvest now, decrypt later** makes key exchange the urgent part: browsers and CDNs negotiate hybrid **X25519MLKEM768** (classical + ML-KEM, FIPS 203) by default since 2024–2025.
- Post-quantum signatures (ML-DSA, FIPS 204) are slower to roll out because certificates and chains grow much larger.

### Certificates and mTLS

- The client validates the **chain to a trusted root** and the hostname; the server proves key ownership by signing the handshake.
- **mTLS**: both sides present certificates — common for service-to-service auth in a mesh.

### HSTS and pinning

- **HSTS** forces HTTPS on later visits after one HTTPS response (preload lists cover the first visit).
- **Certificate pinning** resists CA compromise but makes key rotation painful — mostly limited to mobile apps now.

## Supply chain

### Dependency attacks

- **Typosquatting** (a lookalike package name) and **dependency confusion** (a public package shadowing an internal name) trick installers.
- Pin dependencies with lock files and hashes; install scripts run arbitrary code, so disable them where possible.

### Provenance and signing

- An **SBOM** (SPDX, CycloneDX) lists what's inside an artifact, so a new CVE can be matched to affected builds.
- **SLSA** levels grade build provenance; **Sigstore** (cosign) signs artifacts with short-lived keys tied to a CI identity.

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

- Broken Access Control, Security Misconfiguration, **Software Supply Chain Failures** (new), Cryptographic Failures, Injection, Insecure Design.
- Authentication Failures, Software/Data Integrity Failures, Security Logging and Alerting Failures, **Mishandling of Exceptional Conditions** (new).
- An awareness list, not a test checklist — name the edition when citing it.
