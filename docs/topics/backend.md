# Backend Cheatsheet

The 20 most frequently asked backend interview topics, with short answers. For database internals see [database.md](database.md), for queues and consistency see [distributed.md](distributed.md), for deployment and infrastructure see [devops.md](devops.md), and for vulnerabilities see [security.md](security.md).

## 1. What makes a REST API well designed?

REST models the API as **resources** (nouns) manipulated through HTTP methods: `GET` (read, safe, cacheable), `POST` (create or non-idempotent action), `PUT` (replace, idempotent), `PATCH` (partial update), `DELETE` (remove, idempotent). URLs name resources (`/orders/42/items`), not verbs (`/getOrder`).

Use status codes to carry meaning: `200`/`201`/`204` for success, `400` for a malformed request, `401` for missing/invalid auth, `403` for authenticated but not allowed, `404` for a missing resource, `409` for a conflict, `422` for a valid request that fails business validation, `429` for rate limiting, `5xx` for server failures. Keep responses consistent (envelope shape, error format) across endpoints, and design so clients don't have to guess.

## 2. REST vs RPC vs GraphQL — when do you use which?

**REST** fits resource-oriented CRUD APIs with good HTTP caching and a simple mental model. **RPC** (gRPC, plain JSON-RPC) fits action-oriented or internal service-to-service calls — gRPC adds a strict schema (protobuf), streaming, and strong typing, which pays off inside a system you control but is harder to consume from a browser. **GraphQL** lets the client ask for exactly the fields it needs in one round trip, which is useful when many different clients need different shapes of the same data (e.g. mobile vs web), at the cost of harder caching, harder rate limiting per query, and N+1 risk on the resolvers.

Rule of thumb: public/simple CRUD → REST; high-performance internal services → gRPC; a client with varied, nested data needs → GraphQL.

## 3. What does idempotent mean, and why does it matter for an API?

An operation is **idempotent** if calling it once has the same effect as calling it many times with the same input: `GET`, `PUT`, `DELETE` are idempotent by definition; `POST` is not. This matters because **clients retry** on timeouts — the request may have succeeded on the server even though the client never saw the response, and a naive retry of a non-idempotent `POST` (e.g. "charge card") can double-execute it.

Fix: accept an **idempotency key** (a client-generated UUID) on write endpoints, store it with the result of the first request, and return the same result for any repeat with the same key instead of redoing the side effect.

## 4. How do you design pagination for a list endpoint?

**Offset pagination** (`?page=3&limit=20`, `OFFSET`/`LIMIT` under the hood) is simple but gets slower on large offsets and can skip or repeat rows if data changes between pages. **Cursor (keyset) pagination** (`?after=<opaque_cursor>`) returns a token pointing at the last seen row (typically a unique, indexed column like `id`, or `created_at` plus a tiebreaker) and queries `WHERE id > cursor LIMIT n` — an indexed seek instead of scanning and discarding skipped rows, so cost doesn't grow with page depth. It's also stable under concurrent inserts/deletes elsewhere in the list, as long as the cursor column itself is never mutated — but you can't jump to an arbitrary page. Use cursor pagination for large or frequently-changing datasets and infinite scroll; offset pagination is fine for small, mostly-static lists with page numbers in the UI. See [database.md](database.md) for why large `OFFSET` is slow.

## 5. How do you version an API?

Common strategies: **URI versioning** (`/v1/orders` — explicit and cacheable, but forces a new URL per version), **header versioning** (`Accept: application/vnd.api+json;version=2` — clean URLs, harder to discover), and **no versioning, additive-only changes** (only add optional fields, never remove/rename — works while changes stay backward compatible).

Whatever the scheme: never make a breaking change to a live version (removing a field, changing a type, changing behavior). Add new fields as optional, deprecate old ones with advance notice, and support at most a couple of versions at once — old ones cost real maintenance.

## 6. Authentication vs authorization — sessions vs tokens?

**Authentication** answers "who are you" (login); **authorization** answers "what are you allowed to do" (permissions/roles), checked on every request after authentication. Conflating them is a common bug — e.g. checking that a user is logged in but not that they own the resource they're editing (**IDOR**, see [security.md](security.md)).

**Session-based auth**: the server creates a session on login, stores it (memory, Redis, DB), and gives the client an opaque cookie ID; the server looks up the session on each request. Easy to revoke, but needs shared/sticky session storage across instances. **Token-based auth (JWT)**: the server signs a self-contained token holding the claims; any instance can verify it without a shared store (stateless, scales horizontally), but a JWT **can't be revoked before it expires** unless you add a blocklist — so keep access tokens short-lived and pair with a revocable refresh token.

## 7. How does OAuth 2.0 / OIDC work at a high level?

**OAuth 2.0** is a **delegation** protocol: it lets a user grant a third-party app limited access to their data on another service (e.g. "sign in with Google") without sharing their password. The most common flow, **authorization code + PKCE**: the app redirects the user to the provider's login/consent page, gets back a one-time **authorization code**, and exchanges it for an **access token** (and optionally a **refresh token**). **PKCE** (a one-time secret generated by the client and verified at token exchange) is required for public clients that can't hold a secret (SPAs, mobile apps) and is now recommended for confidential (server-side) clients too, as defense against code interception.

**OIDC (OpenID Connect)** is a thin identity layer on top of OAuth 2.0: it adds a standardized **ID token** (a JWT with the user's identity claims), turning "delegated access" into "login." OAuth answers "can this app access this data," OIDC answers "who is this user."

## 8. How do you rate limit an API?

Common algorithms: **token bucket** (a bucket refills at a fixed rate, each request consumes a token — allows bursts up to the bucket size), **leaky bucket** (smooths bursts into a constant output rate), **fixed window** (simple counter per time window, but allows 2x the limit at window boundaries), **sliding window** (weights the previous window's count — fixes the boundary problem).

Key an in-memory or Redis counter by user ID or API key (not just IP — shared IPs like NAT or corporate proxies punish innocent users together). Return `429 Too Many Requests` with a `Retry-After` header. Rate limit at the edge (gateway/load balancer) when possible so rejected requests never reach application servers.

## 9. What layers does a typical backend service have?

A common layering: **handler/controller** (parses the HTTP request, calls the service, formats the response — no business logic), **service/use case** (business logic, orchestrates repositories and external calls, framework-agnostic), **repository/data access** (talks to the database, hides SQL/ORM details behind an interface). This keeps business logic testable without spinning up HTTP or a real database, and lets you swap the storage layer without touching business rules.

Don't over-engineer this for a small service — three layers for a CRUD endpoint with no real logic is often unnecessary ceremony. Add structure when the logic actually needs isolating.

## 10. How do you handle validation and error responses?

Validate at the **boundary**: parse and validate the request body/query/path params before any business logic runs (type, required fields, format, ranges) — fail fast with `400`. Business-rule failures (e.g. "email already registered") are a different case, usually `409` or `422`, and are detected deeper in the service layer, not at the parsing boundary.

Return a **consistent error shape** (e.g. `{ "error": { "code", "message", "details" } }`) across all endpoints so clients can handle errors generically. Never leak internals (stack traces, SQL, secrets) in error responses; log the detail server-side and return a generic message plus a correlation/request ID the client can report.

## 11. When do you use a message queue instead of a direct call?

A **direct (synchronous) call** is simplest when the caller needs the result immediately and the dependency is fast and usually available. A **queue** (SQS, RabbitMQ, Kafka) decouples producer and consumer in time: the producer publishes and moves on, a worker processes later. Use a queue when the work is slow (sending emails, generating reports), when the downstream system is unreliable or has limited throughput (smooths spikes — **load leveling**), or when multiple independent consumers need the same event.

Trade-off: queues add **eventual consistency** (the caller doesn't know the result yet), operational complexity (another system to run and monitor), and require handling duplicate delivery (most queues are at-least-once) and ordering. See [distributed.md](distributed.md) for exactly-once semantics and stream processing.

## 12. What is the outbox pattern?

The problem: a request needs to both write to the database **and** publish an event (e.g. "order created" → notify shipping), but a DB commit and a message publish are two different systems — without coordination, a crash between them either loses the event or publishes one for a transaction that later rolled back. Distributed (two-phase) transactions across a DB and a broker are possible in principle but rarely supported end-to-end and add latency and coupling, so most systems avoid relying on them.

The **transactional outbox**: write the business row and an "event to publish" row into the **same database transaction** (so they commit atomically), then a separate poller/CDC process reads the outbox table and publishes to the queue, marking rows as sent. This guarantees **at-least-once** delivery consistent with the DB state; the consumer must be idempotent to handle the rare duplicate.

## 13. How do you make cross-service calls safe under retries and failures?

Combine: **timeouts** on every outbound call (never wait forever), **retries with exponential backoff and jitter** for transient failures (never retry blindly in a tight loop — that amplifies an outage), and **idempotency keys** so a retried write isn't double-applied (see Q3). A **circuit breaker** stops calling a dependency that's clearly failing, giving it time to recover and failing fast locally instead of piling up threads/connections waiting on doomed calls.

For multi-step operations across services (no distributed transaction), use a **saga**: each step has a compensating action, and if a later step fails, earlier steps are undone by running their compensations in reverse.

## 14. How do you cache in a backend service?

**Cache-aside (lazy loading)**: on read, check the cache; on a miss, read from the DB and populate the cache. Simplest and most common — only requested data gets cached. **Write-through**: writes go to the cache and the DB together, keeping the cache always warm at the cost of extra write latency. **Write-behind**: writes go to the cache first and are flushed to the DB asynchronously — fast writes, but risks data loss on a crash.

**Invalidation** is the hard part: set a **TTL** as a safety net even when you actively invalidate on writes, since missed invalidations otherwise serve stale data forever. Watch for **cache stampede** (many requests miss simultaneously and hammer the DB when a hot key expires) — mitigate with jittered TTLs or a lock/single-flight around the recompute.

## 15. What is the N+1 query problem?

Fetching a list, then making one extra query per item to fetch related data (e.g. 1 query for 50 orders, then 50 queries for each order's customer) — 51 queries where 2 would do. It's the most common ORM performance bug, usually introduced by lazy-loaded associations accessed inside a loop.

Fix by **eager loading** the association up front (a `JOIN` or a single `WHERE id IN (...)` batch query), or by using a **DataLoader**-style batching layer (common in GraphQL resolvers) that collects individual lookups within a tick and issues one batched query. Spot it with query logging or an APM tool showing a suspiciously high query count for one request. See [database.md](database.md) for the DB-side view.

## 16. How do you shut a backend service down gracefully?

On `SIGTERM` (what orchestrators send before killing a process): stop accepting **new** requests (remove from load balancer / fail readiness probe), let **in-flight** requests finish within a deadline, close DB connections and flush any buffered writes/metrics, then exit. A hard kill mid-request drops responses the client is waiting on and can leave partial writes.

For background workers: stop pulling new jobs from the queue, let the current job finish (or checkpoint it), and only then exit — otherwise you lose or duplicate work depending on the queue's ack semantics.

## 17. How do you structure background jobs and scheduled tasks?

**Background jobs** run outside the request/response cycle, usually pulled from a queue by a worker pool (Sidekiq, Celery, BullMQ) — used for anything slow or that shouldn't block the user's request. **Cron/scheduled jobs** run on a fixed schedule (nightly cleanup, daily report). Both need: **idempotency** (a retried or duplicate-delivered job shouldn't double-charge or double-send), a **retry policy with backoff** and a **dead-letter queue** for jobs that keep failing, and **observability** (job duration, failure rate, queue depth) since nothing user-facing surfaces a stuck worker.

For scheduled jobs specifically, guard against **overlapping runs** (a job that takes longer than its interval) with a lock, and make sure only one instance runs the job when the service is horizontally scaled.

## 18. What backend-specific security practices matter most?

**Validate and sanitize all input** at the boundary — never trust the client. Use **parameterized queries**, never string-concatenated SQL (SQL injection). Store passwords with a slow, salted hash (**bcrypt**/**argon2**), never plain or fast-hashed. Enforce **authorization on every request** server-side — never trust a client-supplied role or ID. Keep secrets (DB passwords, API keys) out of source control and code, injected via environment variables or a secret manager. Apply **least privilege** to service credentials (a service account should only reach what it needs). See [security.md](security.md) for the full vulnerability list (XSS, CSRF, IDOR, SSRF) and [devops.md](devops.md) for secret management infrastructure.

## 19. How do you manage configuration across environments?

Follow **twelve-factor**: config that varies between environments (DB URLs, feature flags, credentials) comes from the **environment**, not hardcoded or baked into the build artifact — the same build gets promoted from staging to production unchanged. Non-secret config can live in version control (YAML/env files per environment); secrets go in a secret manager (Vault, AWS Secrets Manager, Kubernetes Secrets) and are injected at deploy/runtime, never committed.

Validate config at **startup** (fail fast if a required variable is missing or malformed) rather than discovering the gap when the first request hits the unconfigured code path.

## 20. How do you test a backend service?

**Unit tests**: business logic in isolation, dependencies (DB, external APIs) mocked or faked — fast, run on every commit. **Integration tests**: the service against a real (often containerized, e.g. Testcontainers) database or queue, verifying the parts actually wire together — SQL that's syntactically fine but semantically wrong only shows up here. **Contract tests**: verify a service's API matches what its consumers expect (e.g. Pact) without spinning up the consumer — catches breaking changes before they reach production. **End-to-end tests**: the full system through real interfaces — valuable but slow and flaky, so keep the count small and cover critical paths only.

Favor the **test pyramid**: many unit tests, fewer integration tests, few e2e tests — inverting it (mostly e2e) makes the suite slow and hard to debug when something fails.
</content>
