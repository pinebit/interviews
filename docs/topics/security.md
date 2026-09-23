# Security Cheatsheet

The 20 most frequently asked security interview topics, with short answers.

## 1. What is the difference between authentication and authorization?

**Authentication** establishes who a user or service is; **authorization** decides what that identity may do. A valid login does not grant access to every resource: check permission on each request and for each target object, including when its ID comes from the client.

For session and identity protocol choices, see [system.md](system.md).

## 2. What is SQL injection, and how do you prevent it?

**SQL injection** occurs when untrusted input becomes part of SQL syntax, letting an attacker change a query's meaning. Use **parameterized queries** so values are bound separately from SQL code; allowlist any identifiers, such as sort columns, that cannot be parameters.

Input validation and least-privilege database accounts add protection, but neither replaces parameterization. Stored procedures are safe only when they avoid unsafe dynamic SQL; escaping input by hand is fragile.

## 3. What is cross-site scripting (XSS)?

**XSS** lets attacker-controlled content run as script in another user's browser. It can be **stored** (saved and shown later), **reflected** (returned in a response), or **DOM-based** (unsafe client-side code turns data into executable content).

Prevent it with framework escaping, **context-aware output encoding**, and safe DOM APIs such as `textContent`. Sanitize content only when users must supply HTML. A restrictive Content Security Policy (CSP) limits impact but is an additional layer, not the primary fix.

## 4. What is cross-site request forgery (CSRF)?

**CSRF** makes a browser send an unwanted state-changing request to a site where the victim is logged in. It matters especially when the browser automatically attaches a session cookie; CORS does not by itself prevent the request.

Use framework **CSRF tokens** or another server-verified request-origin defense for state-changing actions. Set session cookies to `SameSite=Lax` or `Strict` where feasible, and never change state through a GET request. XSS can bypass many CSRF defenses.

## 5. What is the principle of least privilege?

**Least privilege** gives each user, service, and process only the permissions needed for its job, for only as long as needed. For example, an application database account should access its required tables, not administer the database.

Apply it to API scopes, cloud roles, file permissions, and production access. Review permissions as roles change; otherwise old grants accumulate. For AWS IAM specifics, see [devops.md](devops.md).

## 6. How should passwords be stored, and why use a salt?

Store a password with a purpose-built, costly **password hashing** function such as Argon2id, scrypt, or bcrypt, never a fast hash such as SHA-256 alone. Tune its work factor to make offline guessing expensive and store the algorithm and parameters with the result.

A unique, random **salt** per password prevents precomputed attacks and makes equal passwords produce different hashes. It does not make a weak password unguessable; reputable password-hashing libraries normally generate and store the salt for you.

## 7. What is a JSON Web Token (JWT), and how do you validate one?

A **JWT** is a compact token carrying claims, often protected by a signature. A signed payload is readable, not encrypted, so do not put secrets in it. A signature proves the token was issued by a holder of the signing key; it does not by itself grant permission.

Verify the signature with a trusted key and a configured **algorithm allowlist**; reject `none` and algorithm confusion. Check `iss`, `aud`, `exp`, and other required claims, then enforce resource authorization separately. Plan for token expiry and revocation.

## 8. What is server-side request forgery (SSRF)?

**SSRF** occurs when an attacker controls where a server makes a request, potentially reaching internal services, cloud metadata endpoints, or other destinations the attacker cannot reach directly.

Prefer a strict **destination allowlist** and construct URLs from approved components. Disable automatic redirects or validate every hop; restrict egress and validate resolved IPv4 and IPv6 addresses so DNS changes and alternate IP forms cannot bypass private-network blocks.

## 9. What is the difference between OAuth 2.0 and OpenID Connect (OIDC)?

**OAuth 2.0** lets a client obtain limited access to a protected resource using an access token. **OIDC** adds an identity layer: its ID token lets the client verify the user's authentication and obtain identity claims.

An access token is for the resource server, not proof of login to the client. Common interactive sign-in uses the authorization code flow with **PKCE**; validate the ID token's issuer, audience, signature, and expiry. See [system.md](system.md) for the wider authentication design.

## 10. How does an HTTPS/TLS handshake work at a high level?

**HTTPS** is HTTP over **TLS**. In TLS 1.3, client and server negotiate parameters and exchange ephemeral key shares. The server proves its identity with a certificate and a signature; the client validates the certificate chain and hostname.

Both sides derive symmetric **traffic keys** from the shared secret and handshake transcript, then use authenticated encryption for application data. TLS 1.3 does not encrypt a session secret with the server's public key as older RSA key-exchange descriptions suggest; its ephemeral exchange provides forward secrecy.

## 11. What is the difference between hashing, encryption, and encoding?

**Encoding** changes a representation (for example, Base64) and is reversible without a secret. **Encryption** uses a key to keep data confidential and is reversible with the right key. **Cryptographic hashing** produces a fixed-size digest used to detect changes, with practical resistance to reversing or finding collisions.

A hash alone does not prove who produced data; use a MAC or digital signature for authenticity. Passwords need a slow password-hashing scheme, not a general-purpose hash.

## 12. What is the difference between symmetric and asymmetric cryptography?

**Symmetric cryptography** uses a shared secret key, usually for fast bulk encryption; both parties must protect that key. **Asymmetric cryptography** uses a public/private key pair for operations such as key agreement and digital signatures.

In practice, protocols combine them: TLS 1.3 uses asymmetric key exchange and authentication to establish symmetric traffic keys. Do not assume every public-key system supports both encryption and signing.

## 13. What are digital signatures, and what do they prove?

A **digital signature** is created with a private key and verified with the matching public key. It establishes message **integrity** and that the signer controlled the private key, provided the verifier trusts the key's binding to that identity.

Signatures do not provide confidentiality. They can support non-repudiation, but a compromised or shared private key weakens any claim about which person signed.

## 14. What is the difference between role-based and attribute-based access control?

**RBAC** grants permissions through roles such as editor or administrator. **ABAC** evaluates policy against attributes of the subject, resource, action, and context, such as department and document classification.

RBAC is simpler to audit when roles are few; many special cases can cause role proliferation. ABAC expresses finer conditions but needs consistent attributes and carefully tested policies. Both must enforce access on the server for the specific resource.

## 15. What is defense in depth?

**Defense in depth** uses independent controls so one failure does not expose the whole system. For a database-backed application, controls might include input-safe queries, narrow database permissions, network isolation, encryption, and monitoring.

Layers should address distinct failure modes; adding more of the same weak check does not create strong protection. Start with a direct fix for each risk, then add controls that limit impact if it fails.

## 16. What is threat modeling, and what does STRIDE mean?

**Threat modeling** identifies assets, trust boundaries, likely attackers, and abuse paths before choosing mitigations. Review data flows and ask what could go wrong at each boundary, then prioritize by impact and likelihood.

**STRIDE** is a prompt list: spoofing, tampering, repudiation, information disclosure, denial of service, and elevation of privilege. It helps find threats; it does not rank or fix them by itself.

## 17. What is CORS, and why does it exist?

**Cross-Origin Resource Sharing (CORS)** lets a server tell browsers which other origins may read its responses, relaxing the browser's same-origin policy. A server can allow a specific origin with `Access-Control-Allow-Origin`; credentialed responses cannot use `*`.

CORS is a **browser read control**, not API authentication or a general request firewall. Non-browser clients ignore it, and some cross-origin requests can still be sent. Use server-side authorization and CSRF defenses where applicable.

## 18. What is clickjacking, and how is it prevented?

**Clickjacking** tricks a user into clicking controls on a site framed inside an attacker's page, often under misleading visual content. The user's browser sends the click to the real site with their credentials.

Restrict framing with CSP's **`frame-ancestors`** directive. `X-Frame-Options: DENY` or `SAMEORIGIN` is a fallback for older clients; confirm any legitimate embedding still works.

## 19. What is the OWASP Top 10?

The **OWASP Top 10** is an awareness list of major web application security risk categories, not a complete testing checklist. The current released edition is **2025**; categories include broken access control, security misconfiguration, software supply chain failures, cryptographic failures, and injection.

Use it to guide discussion and prioritization, then test the application's actual threats and controls. The categories can change between editions, so name the edition when citing them.

## 20. What is a zero-day vulnerability?

A **zero-day vulnerability** is a flaw for which defenders have no available fix when it becomes known or exploited. A **zero-day exploit** is a method that uses that flaw; the two terms describe different things.

Until a fix is available, reduce exposure with mitigations such as disabling the affected feature, restricting access, or filtering known attack paths. Patch and verify once a vendor fix is released.
