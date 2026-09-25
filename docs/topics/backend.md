# Backend

What experienced backend engineers forget before an interview, grouped by subtopic. For database internals see [database.md](database.md); for queues, sagas, and retries see [distributed.md](distributed.md); for caching and rate limiting see [system.md](system.md); for HTTP versions see [networking.md](networking.md); for auth and vulnerabilities see [security.md](security.md).

## API design

### Resource modeling

- Resources are nouns and HTTP methods are verbs: `POST /orders/42/items`, not `/addItemToOrder`.
- Non-CRUD actions become sub-resources or state changes: `POST /orders/42/cancellation`.

### Status codes people confuse

- **401** not authenticated vs **403** authenticated but not allowed (or **404** to hide that the resource exists).
- **409** conflicts with current state vs **422** well-formed but fails validation.
- **202** accepted for async processing; **204** success with no body; **412** precondition (`If-Match`) failed; **429** rate limited.

### Method semantics

| Method | Safe | Idempotent |
|---|---|---|
| GET, HEAD | yes | yes |
| PUT, DELETE | no | **yes** |
| POST | no | no |
| PATCH | no | not guaranteed — depends on the patch format |

### REST vs gRPC vs GraphQL

| | REST | gRPC | GraphQL |
|---|---|---|---|
| Contract | OpenAPI (optional) | **Protobuf**, strict | schema, strict |
| Transport | HTTP/1.1 or 2 | **HTTP/2** only | usually HTTP POST |
| Strength | HTTP caching, simplicity | streaming, speed, codegen | client picks fields, one round trip |
| Weakness | over/under-fetching | browsers need gRPC-Web | hard to cache, N+1, query-cost limits |

### Pagination

- **Cursor (keyset)**: `WHERE (created_at, id) > (:c, :id) ORDER BY ... LIMIT n` — fast and stable at any depth; return an opaque cursor.
- **Offset**: simple and jumps to page N, but slows with depth and skips or repeats rows as data changes.

### Versioning

- URI (`/v1/`) is explicit and cacheable; a header (`Accept: ...;version=2`) keeps URLs clean but is harder to discover.
- Whatever the scheme: **additive changes only** within a version; removing or renaming a field is a breaking change.

### Error responses

- One error shape everywhere — **RFC 9457 problem details** (`type`, `title`, `status`, `detail`).
- Never return stack traces or SQL; log details server-side and return a request ID.

## Idempotency and concurrency

### Idempotency keys

- The client sends a unique key per logical operation; the server stores the key with the **first result** and returns it on every retry.
- Handle the **in-flight** case: a retry arriving while the first attempt is running must wait or get 409, not execute twice.
- Scope keys per client and expire them after a TTL (e.g. 24 h).

### Optimistic concurrency with ETags

- `GET` returns an **`ETag`**; the client sends `PUT` with **`If-Match: <etag>`**, and the server answers **412** if the resource changed — no lost updates between clients.

### Transactional outbox

- Write the business row and an outbox row in the **same DB transaction**; a relay (poller or CDC) publishes outbox rows and marks them sent.
- Fixes the dual-write problem: committing and publishing can't both be atomic otherwise. Delivery is at-least-once.

### Inbox deduplication

- Consumers record processed message IDs (in the same transaction as their effect) and skip repeats — the receiving side of the outbox.

## Service calls

### Timeouts and deadline propagation

- Every outbound call gets a **timeout**, shorter than the caller's own.
- **Propagate the deadline** (gRPC does it natively) so downstream services stop work once the original caller has given up.
- Retries, backoff, and circuit breakers: see [distributed.md](distributed.md).

### Webhooks

- **Sign** each payload (HMAC over timestamp + body) and have receivers verify it with a **constant-time** compare; reject stale timestamps to stop replays.
- Deliver **at least once** with backoff, so receivers dedupe by event ID; receivers should ack fast (2xx) and process asynchronously.
- Fetching a user-supplied webhook URL is an **SSRF** risk — see [security.md](security.md).

## Async work

### Queue vs direct call

- Direct call when the caller needs the result now and the dependency is fast and available.
- Queue when work is slow, the downstream is flaky or rate-limited (**load leveling**), or several consumers need the event.

### Long-running operations

- Return **202 Accepted** with a `Location` to a status resource (`/operations/123`); the client polls it or gets a webhook when done.
- The status resource carries state (`pending`, `running`, `succeeded`, `failed`) and the result or error.

### Background jobs

- At-least-once delivery means jobs must be **idempotent**; persistently failing jobs go to a **dead-letter queue** with alerting.

### Scheduled jobs

- Guard against **overlapping runs** (a run longer than its interval) and against every replica firing the same cron — use a lock (DB row, advisory lock, lease) or a single scheduler.

## Data access

### N+1 queries

- Loading a list, then one query per item. Fix with a `JOIN`, a batched `WHERE id IN (...)`, or a **DataLoader** that batches lookups per tick (GraphQL resolvers).
- Spot it with per-request query counts in logs or APM.

### Connection pool sizing

- Size the pool from the **database's** capacity, not the app's thread count — many app instances × a large pool overwhelm the database.
- A good starting point is a small pool per instance (~2× DB cores total across instances), then measure wait time.

### Transaction boundaries

- Never make a network call inside an open DB transaction — it holds locks and a connection for the whole round trip.

### File uploads

- Large files go straight to object storage with a **presigned URL**, bypassing app servers; the app stores only metadata.
- **Multipart/resumable uploads** retry individual parts instead of the whole file.

## Lifecycle and config

### Graceful shutdown

- On **`SIGTERM`**: fail readiness → stop accepting new connections → finish in-flight requests within a deadline → close pools and flush telemetry → exit.
- Workers stop pulling jobs and finish or checkpoint the current one. Kubernetes timing: see [devops.md](devops.md).

### Configuration and secrets

- Config that varies by environment comes from the **environment**, so one immutable artifact promotes from staging to production.
- Secrets come from a secret manager at runtime, never from the repo; **validate config at startup** and fail fast.

## Backend security

### Mass assignment

- Binding the request body straight onto a model lets clients set `isAdmin: true` — **allowlist** bindable fields or use separate DTOs.

### Input validation

- Validate type, format, and range at the boundary before business logic (**400**); business-rule failures come later (**409/422**).

### Secrets in logs

- Request logging middleware can capture tokens, auth headers, and PII — **redact centrally** in the logging layer, not per call site.

## Testing

### Integration and contract tests

- **Testcontainers** runs real dependencies (Postgres, Kafka) in tests, catching SQL and serialization bugs that mocks hide.
- **Consumer-driven contract tests** (Pact) check that a provider still satisfies what each consumer relies on, without deploying both.
