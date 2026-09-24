# Backend

What experienced backend engineers forget before an interview, grouped by subtopic. For database internals see [database.md](database.md); for queues, sagas, and retries see [distributed.md](distributed.md); for caching and rate limiting see [system.md](system.md); for deployment see [devops.md](devops.md); for auth and vulnerabilities see [security.md](security.md).

## API design

### Resource modeling and status codes

- Model the API as resources (nouns) with HTTP verbs, not verbs in the URL (`/orders/42/items`, not `/getOrder`).
- Status codes people confuse: **401** (missing/invalid auth) vs **403** (authenticated but not allowed); **409** (conflict with current state) vs **422** (well-formed request, fails business validation); **429** (rate limited); **202** (accepted, processing async — no result yet).
- `PUT` **replaces** a resource and is idempotent; `PATCH` partially updates and is **not necessarily** idempotent depending on the patch semantics used.

### Protocol choice and pagination

- **REST** — resource CRUD, good HTTP caching, simple mental model. **gRPC** — Protobuf over HTTP/2, strict schema, streaming; needs HTTP/2, so poor direct browser support. **GraphQL** — client asks for exact fields in one round trip; harder to cache, needs N+1 protection on resolvers.
- **Cursor (keyset) pagination** (`WHERE id > cursor LIMIT n`) stays fast and stable at any depth; **offset pagination** degrades and can skip/repeat rows as data changes underneath it — see [database.md](database.md).
- **Versioning**: URI (`/v1/`, explicit, cacheable) vs header (`Accept: ...;version=2`, clean URLs, harder to discover) vs additive-only with no versioning. Never make a breaking change to a live version regardless of scheme.
- Error responses: a consistent shape across endpoints (RFC 9457 **problem details** is the standardized JSON format) — never leak stack traces or SQL in the response; log detail server-side and return a correlation/request ID.

## Idempotency and consistency

### Idempotency keys

- An operation is idempotent if repeating it has the same effect as doing it once — `GET`/`PUT`/`DELETE` by definition, `POST` not.
- **Idempotency key** implementation: client generates a UUID per logical operation, server stores the key with the first request's result, and returns that stored result for any retry with the same key instead of re-executing the side effect. Handle the **in-flight** case too — a retry arriving while the first request is still processing should wait or be rejected, not race a second execution. Expire keys after a TTL.
- **Outbox pattern**: writing a business row and an "event to publish" row in the **same DB transaction**, then a separate poller/CDC process publishes from the outbox and marks rows sent — avoids the split between "DB commit succeeded" and "message actually published" that a direct publish-after-commit can't guarantee atomically.
- **Inbox / deduplication on consumers**: since delivery is at-least-once, a consumer records processed message IDs (with a TTL) and skips already-seen ones — the receiving-side complement to the outbox pattern.

## Resilience in service calls

### Defense per call

- **Timeout on every outbound call** — never wait forever on a dependency.
- Retry **only idempotent operations**, with exponential backoff **and jitter** — see [distributed.md](distributed.md) for why blind retries amplify outages.
- **Deadline propagation**: pass the remaining time budget down the call chain so a downstream service doesn't keep working after the original caller has already given up — without it, a slow leaf call can burn resources for a result nobody will use.

## Async work

### Queue vs direct call

- Direct call when the result is needed immediately and the dependency is fast/available; a queue when work is slow, the downstream is unreliable/rate-limited (**load leveling**), or multiple independent consumers need the same event.
- **Background jobs**: at-least-once delivery means jobs must be **idempotent**; route persistently-failing jobs to a **dead-letter queue** with alerting, not silent drops.
- **Scheduled jobs**: guard against **overlapping runs** (a run longer than its interval) with a lock, and ensure only one instance runs the job when horizontally scaled — a leader-election or DB-lock pattern, not "hope cron only fires once."

## Data access

### N+1 and transactions

- **N+1**: fetching a list then issuing one extra query per item for related data. Fix with eager loading (a `JOIN` or batched `WHERE id IN (...)`) or a **DataLoader**-style batching layer that collects lookups within a tick and issues one query — common in GraphQL resolvers. Spot it via query-count logging or APM. See [database.md](database.md).
- **Pool sizing**: too few connections queues requests behind the pool itself; too many can overwhelm the database's own connection limit before its CPU limit — size around the DB's actual capacity, not the app's thread count.
- **Transaction boundaries**: never make a network call (another service, a slow API) inside an open DB transaction — it holds locks and a connection for the full round trip, starving the pool under load.

## Lifecycle and config

### Graceful shutdown

- On `SIGTERM`: **fail the readiness probe first** (so the load balancer stops routing new traffic) → stop accepting new requests → let in-flight requests finish within a deadline → close DB connections / flush buffered writes and metrics → exit. A hard kill mid-request drops responses clients are waiting on and can leave partial writes.
- Background workers: stop pulling new jobs, let (or checkpoint) the current job finish, then exit — otherwise work is lost or duplicated depending on the queue's ack semantics.

### Twelve-factor config

- Config that varies by environment (DB URLs, flags, credentials) comes from the **environment**, not the build artifact — the same built artifact promotes from staging to production unchanged.
- Secrets go in a secret manager, injected at deploy/runtime, never committed; validate required config at **startup**, failing fast instead of discovering a gap on the first request that hits the unconfigured path.

## Backend security specifics

### Common backend-side gaps

- **Mass assignment**: binding a request body directly onto a model can let a client set fields it shouldn't (`isAdmin: true`) — allowlist bindable fields explicitly.
- **Input validation at the boundary**: parse and validate type/required/format/range before any business logic runs, fail fast with 400; business-rule failures (e.g. "email already registered") are a distinct, deeper check, usually 409/422.
- **SSRF in webhooks/URL fetchers**: any endpoint that fetches a user-supplied URL is a potential SSRF vector against internal services or cloud metadata — see [security.md](security.md) for mitigations.
- **Secrets in logs**: request/response logging middleware can accidentally capture auth headers, tokens, or PII — redact known-sensitive fields at the logging layer, not per call site.

## Testing

### Test pyramid

- **Unit** — business logic isolated, dependencies mocked, fast, run every commit. **Integration** — real (often containerized via **Testcontainers**) dependencies, catches SQL that's syntactically fine but semantically wrong. **Contract tests** — verify a service's API matches consumer expectations (e.g. Pact) without spinning up the consumer, catching breaking changes before production. **End-to-end** — full system through real interfaces, valuable but slow/flaky, so keep the count small.
- Favor the pyramid shape (many unit, fewer integration, few e2e) — an inverted pyramid (mostly e2e) makes the suite slow and hard to debug when something fails.
