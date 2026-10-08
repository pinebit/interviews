# Security

What experienced engineers forget about application security before an interview, grouped by subtopic. For AWS IAM and workload credentials, see [aws.md](aws.md); for backend-side input handling, see [backend.md](backend.md).

## Server-side attacks

### SQL injection

- Untrusted input becomes SQL syntax ([SQL injection](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)). Fix with [parameterized queries](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html), not hand escaping.
- Identifiers (sort column, table name) can't be bound — allowlist them; ORMs don't protect raw fragments.

### Command and template injection

- [Command injection](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html): input inside a shell string (`system("convert " + name)`) — pass an argument array with no shell.
- [SSTI](https://portswigger.net/web-security/server-side-template-injection): user input compiled as a template (Jinja2, Twig) runs code on the server — pass it only as template data.
- [XXE](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html): XML parsers resolving external entities read local files or make requests — disable DTDs and external entities.

### Path traversal and unsafe deserialization

- [Path traversal](https://community.owasp.org/attacks/Path_Traversal): `../../etc/passwd` in a filename escapes the base directory — resolve the canonical path and check it's still inside the base, or map IDs to files.
- [Unsafe deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html) (Java serialization, Python [`pickle`](https://docs.python.org/3/library/pickle.html), YAML with object tags) runs attacker-chosen code — only deserialize untrusted input into plain data (JSON) with schema validation.

### SSRF

- The attacker controls where the server sends a request — reaching cloud metadata or internal services ([SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)).
- Allowlist destinations, validate the resolved IP, and pin it for the request to avoid [DNS rebinding](https://en.wikipedia.org/wiki/DNS_rebinding).
- [IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) on AWS requires a session token, blocking naive metadata theft.

### Prototype pollution

- Merging untrusted JSON with `__proto__` or `constructor.prototype` keys adds properties to `Object.prototype` ([prototype pollution](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Prototype_pollution)) — every object gains them, so checks like `if (user.isAdmin)` can flip.
- Reject those keys, parse into [`Map`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map) or [`Object.create(null)`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create), or [freeze](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze) the prototype.

### HTTP request smuggling

- A proxy and the backend disagree on where a request ends ([`Content-Length` vs `Transfer-Encoding`](https://www.rfc-editor.org/rfc/rfc9112#section-6.3)), so attacker bytes become the start of the next user's request ([request smuggling](https://portswigger.net/web-security/request-smuggling)).
- Reject ambiguous requests at the edge, use HTTP/2 end to end, and keep proxies patched.

### Resource-exhaustion attacks

- [ReDoS](https://community.owasp.org/attacks/Regular_expression_Denial_of_Service_-_ReDoS): backtracking regex engines take exponential time on patterns like `(a+)+$` with crafted input; use linear-time engines ([RE2](https://github.com/google/re2/wiki/Syntax), Go [`regexp`](https://pkg.go.dev/regexp), Rust [`regex`](https://docs.rs/regex/latest/regex/)) or match timeouts.
- [Decompression bombs](https://en.wikipedia.org/wiki/Zip_bomb) and XML [billion laughs](https://en.wikipedia.org/wiki/Billion_laughs_attack) expand kilobytes into gigabytes — cap the decompressed size and disable entity expansion.
- [Hash flooding](https://en.wikipedia.org/wiki/Collision_attack#Hash_flooding) sends colliding keys that make hash tables O(n) per operation; runtimes defend with randomized hash seeds ([SipHash](https://en.wikipedia.org/wiki/SipHash)).
- Cap JSON nesting depth, [GraphQL query depth and cost](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html), and request sizes at the edge.

## Browser-side attacks

### XSS

- [XSS](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/XSS) is stored (saved, rendered later) or reflected (echoed in the response); [DOM-based](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html) means client code turns data into markup or script, and its payload can be stored or reflected too.
- Fix with [context-aware output encoding](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) and safe sinks ([`textContent`](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent), not [`innerHTML`](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML)); CSP limits damage but isn't the primary fix.

### Content Security Policy

- A [strict CSP](https://web.dev/articles/strict-csp) uses per-response nonces or hashes (`script-src 'nonce-…' 'strict-dynamic'`); host allowlists are routinely bypassed through JSONP endpoints and CDN-hosted gadgets.
- [`'strict-dynamic'`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src#strict-dynamic) lets a trusted script load further scripts and makes supporting browsers ignore host allowlists.
- [`frame-ancestors`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors) blocks framing, which stops [clickjacking](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking) (a hidden frame tricking the user into clicking the real site); [`X-Frame-Options`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options) is the legacy header.
- Roll out with [`Content-Security-Policy-Report-Only`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only) first.

### CSRF

- The browser auto-attaches cookies to a forged cross-site request ([CSRF](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/CSRF)).
- Defend with framework [CSRF tokens](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) plus [`SameSite=Lax`/`Strict`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value) cookies ([Lax is Chrome's default](https://www.chromium.org/updates/same-site/)); XSS bypasses CSRF defenses, so prevent XSS separately.

### CORS

- [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS) is a browser read policy, not authentication or a firewall — non-browser clients ignore it.
- A credentialed response can't use [`Access-Control-Allow-Origin: *`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin); reflecting any `Origin` with credentials is equivalent to no policy.
- [Simple requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#simple_requests) (GET, HEAD, or POST with a form or `text/plain` body and no custom headers) go out without a preflight: the server acts on them even though the browser hides the response, so CORS is no CSRF defense.
- Other requests are [preflighted](https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request) with `OPTIONS`; [`Access-Control-Max-Age`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age) caches the result.

### Open redirect

- `/login?next=https://evil.example` sends victims to a phishing page through a link on your domain, and can leak OAuth codes ([open redirect](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)).
- Resolve the target against your origin and require the result to stay same-origin (`//evil.example` is a relative [network-path reference](https://www.rfc-editor.org/rfc/rfc3986#section-4.2) to another host), or check it against an allowlist of hosts.

## Authentication and sessions

### Password storage

- Use a slow, memory-hard hash — [argon2id](https://www.rfc-editor.org/rfc/rfc9106), else [scrypt](https://www.rfc-editor.org/rfc/rfc7914) — never a fast hash like SHA-256; store algorithm and parameters with the hash ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)).
- [bcrypt](https://en.wikipedia.org/wiki/Bcrypt) is for legacy systems only: not memory-hard, and input is capped at 72 bytes (some libraries truncate silently, others reject — Python [`bcrypt`](https://pypi.org/project/bcrypt/) 5.0+).
- A unique [salt](https://en.wikipedia.org/wiki/Salt_%28cryptography%29) per password defeats [rainbow tables](https://en.wikipedia.org/wiki/Rainbow_table); a [pepper](https://en.wikipedia.org/wiki/Pepper_%28cryptography%29) (server-side secret stored elsewhere) helps if only the database leaks.

### Password policy (NIST SP 800-63B)

- [Rev. 4](https://pages.nist.gov/800-63-4/sp800-63b.html) (2025): minimum 15 characters for password-only login (8 with MFA), allow at least 64, no composition rules, no forced periodic rotation.
- Check new passwords against breached-password lists ([Pwned Passwords](https://haveibeenpwned.com/Passwords)); rotate only on evidence of compromise.

### Credential stuffing and enumeration

- [Credential stuffing](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html) replays leaked username/password pairs: rate-limit per account and per IP, add MFA, and check logins against breached-password lists.
- Return the same error and similar timing for "no such user" and "wrong password" to avoid [account enumeration](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#authentication-and-error-messages).

### MFA strength

- Phishing resistance: [WebAuthn](https://www.w3.org/TR/webauthn-3/)/[passkeys](https://passkeys.dev/) > [TOTP](https://www.rfc-editor.org/rfc/rfc6238) app > SMS ([SIM swap](https://en.wikipedia.org/wiki/SIM_swap_scam)).
- A passkey's private key never reaches the server (synced passkeys copy it end-to-end encrypted between the user's devices), and its signature covers the origin, so a lookalike domain gets nothing usable.

### Cookie flags

- [`HttpOnly`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#httponly) (no JS access), [`Secure`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#secure) (HTTPS only), [`SameSite`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value) (cross-site sending).
- The [`__Host-` prefix](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#cookie_prefixes) forces `Secure`, path `/`, and no `Domain`, blocking cookie injection from subdomains.

### Session fixation

- An attacker plants a known session ID before login, then shares the victim's session once they authenticate ([session fixation](https://community.owasp.org/attacks/Session_fixation)).
- Always [issue a new session ID](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#renew-the-session-id-after-any-privilege-level-change) on authentication and privilege change.

### Password reset and recovery

- Reset tokens are single-use, short-lived, high-entropy, and stored hashed like passwords ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)).
- Respond identically whether or not the account exists; revoke other sessions after a reset.
- Build the reset link from a configured origin, never the request's `Host` header — [host-header poisoning](https://portswigger.net/web-security/host-header/exploiting/password-reset-poisoning) sends the token to the attacker's domain.
- Recovery is often the weakest login path (SIM swap, support-desk social engineering): hold it to the same assurance as MFA.

### Browser token storage

- [`HttpOnly`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#httponly) cookie: safe from XSS token theft, needs `SameSite` + CSRF tokens — the default for web apps.
- In memory: no CSRF, gone on refresh (needs silent refresh), still usable by a script running on the page.
- [`localStorage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage): any XSS reads it directly — avoid for sensitive tokens.

## Tokens and federation

### JWT validation

- Pin the expected [`alg`](https://www.rfc-editor.org/rfc/rfc8725#section-3.1), reject `none`, and block [RS/HS confusion](https://portswigger.net/web-security/jwt/algorithm-confusion) (an RS256 token re-signed as HS256 with the public key as the secret).
- Pick the key by `kid` from a trusted set ([JWKS](https://www.rfc-editor.org/rfc/rfc7517)); validate [`exp`, `aud`, and `iss`](https://www.rfc-editor.org/rfc/rfc7519#section-4.1) — a valid signature is not authorization.

### JWT revocation

- Stateless [JWTs](https://www.rfc-editor.org/rfc/rfc7519) can't be revoked in place — use short expiry plus [refresh-token rotation](https://www.rfc-editor.org/rfc/rfc9700#section-4.14.2).
- A denylist of token IDs ([`jti`](https://www.rfc-editor.org/rfc/rfc7519#section-4.1.7)) works but brings back a server-side lookup on every request.

### OAuth 2.0 vs OIDC

- [OAuth 2.0](https://www.rfc-editor.org/rfc/rfc6749) is delegated authorization (an access token for a resource server); [OIDC](https://openid.net/specs/openid-connect-core-1_0.html) adds authentication via an ID token.
- Interactive login: authorization code + [PKCE](https://www.rfc-editor.org/rfc/rfc7636); service to service: [client credentials](https://www.rfc-editor.org/rfc/rfc6749#section-4.4). [OAuth 2.1](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/) drops the implicit and password grants.

### OAuth pitfalls

- Match `redirect_uri` exactly against a registered value — prefix or wildcard matching [leaks authorization codes](https://www.rfc-editor.org/rfc/rfc9700#section-4.1).
- The [`state`](https://www.rfc-editor.org/rfc/rfc6749#section-10.12) parameter (or PKCE) ties the callback to the browser session that started it, blocking login CSRF.
- Bearer tokens work for whoever holds them; [DPoP](https://www.rfc-editor.org/rfc/rfc9449) or [mTLS](https://www.rfc-editor.org/rfc/rfc8705) sender-constrains tokens to a client key.

### Refresh token rotation

- Each refresh returns a new refresh token and invalidates the old one ([RFC 9700](https://www.rfc-editor.org/rfc/rfc9700#section-4.14.2)).
- Reuse of an old token signals theft, so revoke the whole token family.

## Authorization

### RBAC, ABAC, ReBAC

| Model | Decision based on | Fits | Weak spot |
|---|---|---|---|
| [RBAC](https://en.wikipedia.org/wiki/Role-based_access_control) | roles | few, stable roles | role explosion from exceptions |
| [ABAC](https://en.wikipedia.org/wiki/Attribute-based_access_control) | subject/resource/context attributes | fine-grained conditions | needs trustworthy attributes |
| [ReBAC](https://en.wikipedia.org/wiki/Relationship-based_access_control) | relationship graph ("member of team that owns") | nested sharing (Google Docs, [Zanzibar](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)) | graph storage and evaluation cost |

- Enforce server-side and [deny by default](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#deny-by-default) — a hidden button is not access control.

### IDOR / BOLA

- The endpoint checks that the caller is logged in but not that they may access this object ID ([BOLA](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)).
- Authorize per resource on every request; unguessable IDs only hide the bug ([IDOR](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)).

## Cryptography

### Secure randomness

- Tokens, session IDs, nonces, and reset codes need a [CSPRNG](https://en.wikipedia.org/wiki/Cryptographically_secure_pseudorandom_number_generator): [`crypto.getRandomValues`](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues)/[`crypto.randomBytes`](https://nodejs.org/api/crypto.html#cryptorandombytessize-callback), Python [`secrets`](https://docs.python.org/3/library/secrets.html), Go [`crypto/rand`](https://pkg.go.dev/crypto/rand).
- [`Math.random`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/random), Python [`random`](https://docs.python.org/3/library/random.html) ([Mersenne Twister](https://en.wikipedia.org/wiki/Mersenne_Twister), reconstructable from 624 outputs), and Go [`math/rand`](https://pkg.go.dev/math/rand) aren't designed for secrets.
- Use at least 128 bits for unguessable tokens.

### AES-GCM nonces

- [AES-GCM](https://en.wikipedia.org/wiki/Galois/Counter_Mode) is [authenticated encryption](https://en.wikipedia.org/wiki/Authenticated_encryption): confidentiality plus an integrity tag.
- Reusing a nonce with the same key breaks both — nonces must never repeat per key; random 96-bit nonces are safe for about 2³² messages per key ([NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final)).

### RSA vs ECC and forward secrecy

- [ECC](https://en.wikipedia.org/wiki/Elliptic-curve_cryptography) gives equal security at far smaller keys (256-bit EC ≈ 3072-bit RSA, [NIST SP 800-57](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)), making signatures and handshakes cheaper.
- [ECDHE](https://en.wikipedia.org/wiki/Elliptic-curve_Diffie%E2%80%93Hellman) gives [forward secrecy](https://en.wikipedia.org/wiki/Forward_secrecy): a later leak of the long-term key doesn't expose past sessions.

### MAC vs signature

- A [MAC](https://en.wikipedia.org/wiki/Message_authentication_code) ([HMAC](https://www.rfc-editor.org/rfc/rfc2104)) proves integrity to anyone holding the shared key, so it can't give [non-repudiation](https://en.wikipedia.org/wiki/Non-repudiation); a [signature](https://en.wikipedia.org/wiki/Digital_signature) can, since only the private-key holder could sign.
- Naive `hash(key ‖ msg)` is open to [length extension](https://en.wikipedia.org/wiki/Length_extension_attack) on [Merkle-Damgård](https://en.wikipedia.org/wiki/Merkle%E2%80%93Damg%C3%A5rd_construction) hashes (MD5, SHA-1, SHA-256); HMAC isn't.

### Envelope encryption and key management

- Encrypt data with a random data key (DEK), encrypt the DEK with a key-encryption key (KEK) held in a KMS/[HSM](https://en.wikipedia.org/wiki/Hardware_security_module), store the wrapped DEK with the data ([envelope encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption)).
- Rotating the KEK never re-encrypts the data: KMS keeps old key versions to unwrap existing DEKs, and retiring one only means rewrapping DEKs; the master key never leaves the KMS. AWS specifics: see [aws.md](aws.md).

### Timing attacks

- Comparing secrets (HMACs, tokens) with `==` returns early at the first differing byte, leaking how much matched ([timing attack](https://en.wikipedia.org/wiki/Timing_attack)).
- Use a constant-time compare ([`hmac.compare_digest`](https://docs.python.org/3/library/hmac.html#hmac.compare_digest), [`crypto.timingSafeEqual`](https://nodejs.org/api/crypto.html#cryptotimingsafeequala-b)).

## TLS

### TLS 1.3 handshake

- [TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446) does a 1-RTT full handshake: key shares go in the first flight.
- Optional [0-RTT](https://www.rfc-editor.org/rfc/rfc8446#section-2.3) resumption data can be replayed — accept it only for requests safe to repeat (idempotent and cheap); HTTP servers can answer [`425 Too Early`](https://www.rfc-editor.org/rfc/rfc8470#section-5.2).

### Post-quantum key exchange

- [Harvest now, decrypt later](https://en.wikipedia.org/wiki/Harvest_now,_decrypt_later) makes key exchange the urgent part: browsers and CDNs negotiate hybrid [X25519MLKEM768](https://www.rfc-editor.org/rfc/rfc10024) (classical + ML-KEM, [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final)) by default since 2024–2025.
- Post-quantum signatures (ML-DSA, [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final)) are slower to roll out because certificates and chains grow much larger.

### Certificates and mTLS

- The client validates the [chain to a trusted root](https://en.wikipedia.org/wiki/Chain_of_trust) and the hostname; the server proves key ownership by signing the handshake.
- [mTLS](https://en.wikipedia.org/wiki/Mutual_authentication#mTLS): both sides present certificates — common for service-to-service auth in a mesh.

### HSTS and pinning

- [HSTS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security) forces HTTPS on later visits after one HTTPS response ([preload lists](https://hstspreload.org/) cover the first visit).
- [Certificate pinning](https://cheatsheetseries.owasp.org/cheatsheets/Pinning_Cheat_Sheet.html) resists CA compromise but makes key rotation painful — mostly limited to mobile apps now.

## Secure development

### Dependency attacks

- [Typosquatting](https://en.wikipedia.org/wiki/Typosquatting) (a lookalike package name) and [dependency confusion](https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-03-Dependency-Chain-Abuse) (a public package shadowing an internal name) trick installers.
- Pin dependencies with lock files and hashes; [install scripts](https://docs.npmjs.com/cli/v11/using-npm/scripts) run arbitrary code, so disable them where possible.

### Provenance and signing

- An [SBOM](https://www.cisa.gov/topics/information-communications-technology-supply-chain-security/sbom) ([SPDX](https://spdx.dev/), [CycloneDX](https://cyclonedx.org/)) lists what's inside an artifact, so a new CVE can be matched to affected builds.
- [SLSA](https://slsa.dev/) levels grade build provenance; [Sigstore](https://www.sigstore.dev/) ([cosign](https://docs.sigstore.dev/cosign/signing/overview/)) signs artifacts with short-lived keys tied to a CI identity.

### STRIDE

| [STRIDE](https://en.wikipedia.org/wiki/STRIDE_model) threat | Violates |
|---|---|
| Spoofing | Authentication |
| Tampering | Integrity |
| Repudiation | Non-repudiation |
| Information disclosure | Confidentiality |
| Denial of service | Availability |
| Elevation of privilege | Authorization |

- STRIDE finds threats at each trust boundary; it doesn't rank them — pair it with impact/likelihood.
