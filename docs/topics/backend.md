# Backend

What experienced backend engineers forget before an interview, grouped by subtopic. For PostgreSQL internals see [postgresql.md](postgresql.md); for Redis see [redis.md](redis.md); for queues, sagas, and retries see [distributed.md](distributed.md); for caching and rate limiting see [system.md](system.md); for HTTP versions see [networking.md](networking.md); for auth and vulnerabilities see [security.md](security.md).

## API design

### Status codes people confuse

| Codes | Meaning |
|---|---|
| [401](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.2) vs [403](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.4) | missing or invalid credentials (re-auth may help) vs refused — credentials, if sent, are insufficient; others might succeed (or 404 to hide that the resource exists) |
| [409](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.10) vs [422](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.21) | conflicts with current state vs well-formed but fails validation |
| [202](https://www.rfc-editor.org/rfc/rfc9110#section-15.3.3) / [204](https://www.rfc-editor.org/rfc/rfc9110#section-15.3.5) | accepted for async processing / success with no body |
| [412](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.13) / [429](https://www.rfc-editor.org/rfc/rfc6585#section-4) | precondition (`If-Match`) failed / rate limited |

### Method semantics

| Method | [Safe](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.1) | [Idempotent](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2) |
|---|---|---|
| GET, HEAD | yes | yes |
| PUT, DELETE | no | yes |
| POST | no | no |
| [PATCH](https://www.rfc-editor.org/rfc/rfc5789) | no | not guaranteed — depends on the patch format |

### PATCH formats

- [JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396) (RFC 7396): send a partial object; `null` deletes a field — so it can't set a value to null or edit one array element.
- [JSON Patch](https://www.rfc-editor.org/rfc/rfc6902) (RFC 6902): a list of operations (`add`, `remove`, `replace`, `test`) on [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901) paths; `test` makes the patch conditional.

### REST vs gRPC vs GraphQL

| | [REST](https://en.wikipedia.org/wiki/REST) | [gRPC](https://grpc.io/docs/what-is-grpc/introduction/) | [GraphQL](https://graphql.org/learn/) |
|---|---|---|---|
| Contract | [OpenAPI](https://spec.openapis.org/oas/latest.html) (optional) | [Protobuf](https://protobuf.dev/overview/), strict | schema, strict |
| Transport | any HTTP version | [HTTP/2](https://www.rfc-editor.org/rfc/rfc9113) only | usually HTTP POST |
| Strength | HTTP caching, simplicity | streaming, speed, codegen | client picks fields, one round trip |
| Weakness | over/under-fetching | browsers need [gRPC-Web](https://grpc.io/docs/platforms/web/) | hard to cache, N+1, query-cost limits |

### Pagination

- [Keyset](https://use-the-index-luke.com/no-offset): `WHERE (created_at, id) > (:c, :id) ORDER BY ... LIMIT n` — fast at any depth and unaffected by inserts; needs a unique, immutable sort key, or updated rows skip or repeat.
- Expose the position as an opaque cursor; a cursor is just a token and can also encode an offset.
- [Offset](https://www.postgresql.org/docs/current/queries-limit.html): simple and jumps to page N, but slows with depth and skips or repeats rows as data changes.

### Versioning

- URI (`/v1/`) is explicit and cacheable; a header ([`Accept: ...;version=2`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept)) keeps URLs clean but is harder to discover.
- Whatever the scheme: additive changes only within a version; removing or renaming a field is a breaking change.

### Error responses

- One error shape everywhere — [RFC 9457 problem details](https://www.rfc-editor.org/rfc/rfc9457) (`type`, `title`, `status`, `detail`).
- Never return stack traces or SQL; log details server-side and return a request ID.

## Idempotency and concurrency

### Idempotency keys

- The client sends a unique [`Idempotency-Key`](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/) per logical operation; the server stores the key with the first result and returns it on every retry.
- Handle the in-flight case: a retry arriving while the first attempt is running must wait or get 409, not execute twice.
- Scope keys per client and expire them after a TTL (e.g. 24 h).

### Optimistic concurrency with ETags

- `GET` returns an [`ETag`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag); the client sends `PUT` with [`If-Match: <etag>`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match), and the server answers 412 if the resource changed — no lost updates between clients.
- `If-Match` needs a [strong ETag](https://www.rfc-editor.org/rfc/rfc9110#section-8.8.1) (not `W/`); [`If-None-Match: *`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-None-Match) makes a `PUT` create-only.

### Transactional outbox

- Write the business row and an outbox row in the same DB transaction; a relay (poller or [CDC](https://en.wikipedia.org/wiki/Change_data_capture)) publishes outbox rows and marks them sent — the [transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html).
- Fixes the dual-write problem without [2PC](https://en.wikipedia.org/wiki/Two-phase_commit_protocol), which most brokers don't support. Delivery is at-least-once (see [distributed.md](distributed.md)).

### Inbox deduplication

- Consumers record processed message IDs in the same transaction as their effect and skip repeats — the receiving side of the outbox ([idempotent consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html)).
- Expire entries only after the broker's maximum redelivery window.

## Service calls

### Timeouts and deadline propagation

- Every outbound call gets a timeout, shorter than the caller's own.
- Propagate the deadline so downstream services stop work once the original caller has given up — [gRPC](https://grpc.io/docs/guides/deadlines/) sends it on the wire, but each server must pass it on to its outbound calls and honor cancellation.
- Retries, backoff, and circuit breakers: see [distributed.md](distributed.md).

### Schema evolution

- [Backward compatible](https://en.wikipedia.org/wiki/Backward_compatibility): new readers read old data; [forward compatible](https://en.wikipedia.org/wiki/Forward_compatibility): old readers read new data — rolling deploys and replayed events need both.
- [Protobuf](https://protobuf.dev/programming-guides/proto3/#updating): never reuse or renumber a field tag (mark removed ones [`reserved`](https://protobuf.dev/programming-guides/proto3/#reserved)); adding fields is safe; proto3 has no `required`; unknown fields survive a binary round trip, but not conversion to JSON.
- [Avro](https://avro.apache.org/docs/) with a [schema registry](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) checks BACKWARD, FORWARD, or FULL compatibility on every schema change.
- JSON consumers must ignore unknown fields ([tolerant reader](https://martinfowler.com/bliki/TolerantReader.html)); rename a field by adding the new one, writing both, moving readers over, then removing the old.

### Webhooks

- Sign each payload ([HMAC](https://en.wikipedia.org/wiki/HMAC) over timestamp + body) and have receivers verify it with a [constant-time](https://en.wikipedia.org/wiki/Timing_attack) compare; reject stale timestamps to stop replays.
- Deliver at least once with backoff, so receivers dedupe by event ID; receivers should ack fast (2xx) and process asynchronously.
- Fetching a user-supplied webhook URL is an [SSRF](https://community.owasp.org/attacks/Server_Side_Request_Forgery) risk — see [security.md](security.md).

## Async work

### Long-running operations

- Return [202 Accepted](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/202) with a [`Location`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Location) to a status resource (`/operations/123`); the client polls it or gets a webhook when done.
- The status resource carries state (`pending`, `running`, `succeeded`, `failed`) and the result or error ([asynchronous request-reply](https://learn.microsoft.com/en-us/azure/architecture/patterns/asynchronous-request-reply)).

### Background jobs

- At-least-once delivery means jobs must be [idempotent](https://en.wikipedia.org/wiki/Idempotence); persistently failing jobs go to a [dead-letter queue](https://en.wikipedia.org/wiki/Dead_letter_queue) with alerting.
- Give every job a timeout; long jobs checkpoint progress so a retry resumes instead of restarting.

### Scheduled jobs

- Guard against overlapping runs, where one run lasts longer than the interval.
- With several replicas, each fires the same [cron](https://en.wikipedia.org/wiki/Cron) — use a lock (DB row, [advisory lock](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS), [lease](https://en.wikipedia.org/wiki/Lease_%28computer_science%29)) or a single scheduler.

## Data access

### N+1 queries

- Loading a list, then one query per item. Fix with a `JOIN`, a batched `WHERE id IN (...)`, or a [DataLoader](https://github.com/graphql/dataloader) that batches lookups per tick (GraphQL resolvers).
- Spot it with per-request query counts in logs or [APM](https://en.wikipedia.org/wiki/Application_performance_management).

### Connection pool sizing

- Size the [connection pool](https://en.wikipedia.org/wiki/Connection_pool) from the database's capacity, not the app's thread count — many app instances × a large pool overwhelm the database.
- A good starting point is a small pool per instance (~2× DB cores total across instances, [HikariCP's formula](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)), then measure wait time; server-side pooling in [postgresql.md](postgresql.md).

### Transaction boundaries

- Never make a network call inside an open DB transaction — it holds locks and a connection for the whole round trip.
- For "commit, then notify another service", use the [outbox](https://microservices.io/patterns/data/transactional-outbox.html) instead of calling inside the transaction.

### Multi-tenancy models

- Shared tables with a `tenant_id`: cheapest, but every query must filter — enforce it with PostgreSQL [row-level security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) (the table owner bypasses it unless [`FORCE ROW LEVEL SECURITY`](https://www.postgresql.org/docs/current/sql-altertable.html)).
- Schema per tenant: more isolation, but migrations and connection pools multiply with the tenant count.
- Database per tenant: strongest isolation, per-tenant restore and data residency, the most operational work.
- Move [noisy neighbors](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/noisy-neighbor/noisy-neighbor) (the largest tenants) to their own shard or database, and rate-limit per tenant.

### Time handling

- Store and send instants in UTC ([RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) with an offset, `2026-03-08T09:30:00Z`); in PostgreSQL use [`timestamptz`](https://www.postgresql.org/docs/current/datatype-datetime.html).
- For future local-time events (meetings, schedules), store the local time plus an [IANA zone](https://www.iana.org/time-zones) (`Europe/Berlin`), not an offset — DST rules and offsets change.
- A [DST](https://en.wikipedia.org/wiki/Daylight_saving_time) switch skips or repeats a local hour, so a job scheduled at 02:30 local time runs never or twice; schedule jobs in UTC.

### File uploads

- Clients upload straight to object storage with a [presigned URL](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html), bypassing app servers ([system.md](system.md)).
- [Multipart](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html) or [resumable](https://tus.io/protocols/resumable-upload) uploads retry individual parts instead of the whole file.

## Service lifecycle

### Graceful shutdown

- On [`SIGTERM`](https://man7.org/linux/man-pages/man7/signal.7.html): fail readiness → stop accepting new connections → finish in-flight requests within a deadline → close pools and flush telemetry → exit.
- Workers stop pulling jobs and finish or checkpoint the current one. Kubernetes timing: see [devops.md](devops.md).

### Health endpoints

- Separate endpoints: [liveness](https://kubernetes.io/docs/concepts/workloads/pods/probes/) checks only that the process can make progress; readiness checks what serving needs (warm-up done, required dependencies) and fails while draining.
- Keep them cheap and on an internal port; probe configuration and pitfalls: see [devops.md](devops.md).

## Backend security

### Mass assignment

- Binding the request body straight onto a model lets clients set `isAdmin: true` ([mass assignment](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html)) — allowlist bindable fields or use separate [DTOs](https://martinfowler.com/eaaCatalog/dataTransferObject.html).
- Serialize responses through explicit DTOs too, so a new sensitive column doesn't leak.

### Input validation

- [Validate](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) type, format, and range at the boundary before business logic (400); business-rule failures come later (409/422).
- Cap sizes — body, array lengths, string lengths, nesting depth — to prevent [resource exhaustion](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption/).

### Secrets in logs

- Request logging middleware can capture tokens, auth headers, and [PII](https://en.wikipedia.org/wiki/Personal_data) — redact centrally in the logging layer, not per call site ([OWASP logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)).
- Tokens in URL query strings end up in proxy and CDN logs — send them in headers.

## Testing

### Integration tests with real dependencies

- [Testcontainers](https://testcontainers.com/) runs real dependencies (Postgres, Kafka) in tests, catching SQL and serialization bugs that mocks hide.
- A [mock](https://martinfowler.com/articles/mocksArentStubs.html) only checks your assumptions about a dependency; test the real one at least at the adapter boundary.

### Consumer-driven contract tests

- [Consumer-driven contract tests](https://martinfowler.com/articles/consumerDrivenContracts.html) ([Pact](https://docs.pact.io/)): each consumer records the requests and fields it relies on, and the provider's CI verifies them.
- Catches breaking API changes without deploying both services together.
