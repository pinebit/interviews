# Security

What experienced security engineers forget before an interview, grouped by subtopic. For AWS IAM and least privilege in practice, see [devops.md](devops.md); for session/identity protocol placement in an architecture, see [system.md](system.md).

## Web vulnerabilities

### Injection and XSS

- **SQL injection**: untrusted input becomes SQL syntax. Fix with **parameterized queries**, not escaping by hand; allowlist identifiers (e.g. sort columns) that can't be bound as parameters — ORMs don't save you from raw fragments.
- **XSS**: stored (saved, shown later), reflected (echoed in a response), DOM-based (unsafe client code turns data into executable content). Fix with **context-aware output encoding** and safe DOM APIs (`textContent`); a **CSP with nonces** limits blast radius but isn't the primary fix.

### CSRF, SSRF, clickjacking, CORS

- **CSRF**: a browser auto-attaches a session cookie to a forged cross-site request. Fix with framework CSRF tokens and `SameSite=Lax`/`Strict` cookies (**Lax is Chrome's default**) — XSS can bypass many CSRF defenses, so it's not a substitute.
- **SSRF**: attacker controls a server-made request's destination, potentially reaching the cloud metadata endpoint or internal services. Use a strict destination allowlist, validate resolved IPs (**IMDSv2** on AWS specifically requires a session token, blocking naive SSRF-via-metadata), and watch for **DNS rebinding** between validation and the actual request.
- **Clickjacking**: framed page tricks a click into hitting the real site. Fix with CSP's **`frame-ancestors`**.
- **CORS** is a **browser read policy**, not server auth or a firewall — non-browser clients ignore it entirely; a credentialed response can't use `Access-Control-Allow-Origin: *`.
- **IDOR/BOLA**: authorization checked at the endpoint but not per-object — always check permission against the specific resource ID from the request, not just that the caller is logged in.

## Authentication and sessions

### Password storage

- Purpose-built, costly hash: **argon2id / bcrypt / scrypt** — never a fast general hash like SHA-256 alone. Tune the work factor; store algorithm + parameters alongside the hash.
- A unique random **salt** per password defeats precomputed (rainbow table) attacks; a **pepper** (server-side secret, not stored with the hash) adds defense if the hash database leaks alone.

### MFA and sessions

- MFA phishing resistance ranks: **WebAuthn/passkeys** (phishing-resistant, bound to origin) > TOTP app > SMS (vulnerable to SIM swap).
- Cookie flags: **`HttpOnly`** (no JS access), **`Secure`** (HTTPS only), **`SameSite`**, and the **`__Host-`** prefix (forces `Secure`, no `Domain` attribute, path `/`) to prevent subdomain cookie injection.
- **Session fixation**: attacker sets a known session ID before login — always issue a fresh session ID on authentication.

## Tokens and federation

### JWT validation checklist

- Pin the expected **`alg`**; reject **`none`**; guard against **RS/HS confusion** (an attacker resubmits an RS256 token as HS256, using the public key as the HMAC secret).
- Use **`kid`** to select the right verification key from a set, and validate `exp`/`aud`/`iss` — a valid signature alone is not authorization.
- JWTs are **stateless**, so **revocation is the hard problem** — short expiry plus a refresh-token rotation scheme is the usual mitigation, not a blocklist that defeats the point of statelessness.

### OAuth and OIDC

- **OAuth 2.0** is delegated *authorization* (an access token scoped to a resource server); **OIDC** adds *authentication* on top via an ID token.
- Interactive sign-in: **authorization code flow + PKCE**; service-to-service: **client credentials**. The **implicit** and **password** grants are deprecated in **OAuth 2.1**.
- **Refresh token rotation**: each use issues a new refresh token and invalidates the old one, so a stolen-and-reused old token signals compromise.

## Access control models

### RBAC vs ABAC vs ReBAC

- **RBAC** — permissions via roles; simple to audit with few roles, but many exceptions cause role proliferation.
- **ABAC** — policy evaluated against subject/resource/action/context attributes; expresses fine-grained conditions but needs consistent, trustworthy attributes.
- **ReBAC** — permissions derived from relationships in a graph (e.g. "owner of," "member of team that owns") — fits deeply nested sharing models (Google Docs-style) that RBAC/ABAC express awkwardly.
- All three must be enforced **server-side**, denying by default — a client-hidden button is not access control.

## Cryptography

### Primitives

| | Reversible? | Needs a key? | Purpose |
|---|---|---|---|
| Encoding (Base64) | yes, no secret | no | representation change |
| Encryption | yes, with the key | yes | confidentiality |
| Hashing | no (one-way) | no | integrity/fingerprint |

- **AES-GCM**: nonce reuse with the same key is catastrophic — it can fully break confidentiality and authenticity, so nonces must never repeat per key.
- **RSA vs ECC**: ECC gives equivalent security at much smaller key sizes (256-bit EC ≈ 3072-bit RSA), cheaper for signatures and handshakes.
- **ECDHE** provides **forward secrecy** — session keys aren't derivable even if the long-term private key later leaks.
- **MAC vs signature**: a MAC (HMAC) proves integrity + authenticity to anyone holding the shared secret, so it can't give non-repudiation; a signature (asymmetric) can, since only the private key holder could have produced it.
- **HMAC vs naive `hash(key ‖ msg)`**: the naive construction is vulnerable to **length-extension attacks** on Merkle-Damgård hashes (MD5, SHA-1, SHA-256); HMAC's nested construction avoids this.

## TLS

### Handshake and trust

- TLS 1.3 handshake is **1-RTT** (client and server exchange ephemeral key shares in the first round trip); optional **0-RTT** resumption data carries a **replay risk** since it isn't tied to a fresh handshake.
- The server proves identity via a certificate + signature; the client validates the full **chain to a trusted root** and the hostname.
- **mTLS** — both sides present certificates, common for service-to-service auth inside a mesh.
- **HSTS** forces HTTPS on future visits after the first HTTPS response; **certificate pinning** hard-codes a trusted key/cert, trading resilience to CA compromise against ops pain during rotation.

## Threat modeling

### STRIDE and OWASP

| STRIDE threat | Violates |
|---|---|
| Spoofing | Authentication |
| Tampering | Integrity |
| Repudiation | Non-repudiation |
| Information disclosure | Confidentiality |
| Denial of service | Availability |
| Elevation of privilege | Authorization |

- STRIDE is a prompt list for finding threats at each trust boundary — it doesn't rank or fix them; pair it with impact/likelihood scoring.
- **OWASP Top 10:2025** current categories (broad awareness list, not a full test checklist — name the edition when citing it): Broken Access Control, Security Misconfiguration, Software Supply Chain Failures, Cryptographic Failures, Injection, Insecure Design, Authentication Failures, Software/Data Integrity Failures, Security Logging and Alerting Failures, Mishandling of Exceptional Conditions.
