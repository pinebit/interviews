# System Design

Key system design building blocks and trade-offs, grouped by subtopic. For CAP, consistency, replication, and sharding internals, see [distributed.md](distributed.md); for API design, idempotency, and outbox, see [backend.md](backend.md); for auth and web security, see [security.md](security.md).

## Interview framework

### Structure and estimates

- Fixed order: **(1)** requirements (functional + non-functional: scale, latency, availability, consistency), **(2)** estimates (users, QPS, storage), **(3)** API, **(4)** data model, **(5)** high-level design, **(6)** deep dive on the hardest 1–2 components, **(7)** bottlenecks and trade-offs.
- Numbers to know: 1 day ≈ **86,400 s ≈ 10⁵ s**; RAM read ~100 ns, SSD random read ~100 µs, same-DC round trip ~0.5 ms, cross-continent ~150 ms.
- Availability nines: **99.9% ≈ 8.8 h/year** downtime, **99.99% ≈ 53 min/year**, **99.999% ≈ 5 min/year**.

## Traffic and edge

### Load balancing

- **L4** (transport) balances by IP/port, fast, no packet inspection. **L7** (application) reads HTTP (path, headers, cookies) for content-based routing and retries, at higher CPU cost.
- Algorithms: round robin, weighted round robin, least connections (uneven request lengths), IP/consistent hash (same client/key → same server, useful for caches).
- **Sticky sessions** work but defeat statelessness and unbalance load — prefer moving session state to a shared store.

### Proxies and gateways

- **Reverse proxy** (Nginx, Envoy) sits in front of servers: TLS termination, load balancing, caching. An **API gateway** adds edge concerns (authn, rate limiting, routing, aggregation) for north–south traffic; a **BFF** gives each client type its own gateway.
- **Service mesh** (Istio, Linkerd) handles east–west service-to-service traffic via **sidecar proxies**: mTLS, retries, circuit breaking, telemetry, without app code changes.
- **Service discovery**: instances register with a registry (Consul, etcd, Eureka) and are removed on failed health checks; Kubernetes does this natively via stable Service DNS names — see [devops.md](devops.md).

### CDN and object storage

- **Pull CDN** fetches from origin on first miss (simple, slow first request); **push CDN** is pre-uploaded (for large, rarely-changing files). Invalidate with versioned filenames (`app.3f9a.js`) rather than purges.
- **Object storage** (S3, GCS) — cheap, durable, unlimited size for blobs; keep only metadata/URLs in the database, and use **pre-signed URLs** so uploads/downloads bypass app servers.

## Caching

### Strategies

| Pattern | Write path | Read path | Trade-off |
|---|---|---|---|
| Cache-aside | app writes DB, invalidates cache | miss → read DB, fill cache | most common; stale until TTL/invalidation |
| Read-through | — | cache loads from DB on miss | cache owns the loading logic |
| Write-through | write cache + DB together | cache always warm | slower writes; the two writes aren't atomic, so a crash or race can still diverge them |
| Write-behind | write cache, flush DB async | fast writes | risk of data loss before flush |

### Eviction and stampedes

- Eviction: **LRU** (most common), LFU, TTL.
- **Invalidation**: delete the key on write rather than update it in place, to avoid races between concurrent writers.
- **Cache stampede**: many concurrent misses on a hot key hit the DB at once. Fix with request coalescing (single-flight), locks, or probabilistic early refresh with **jittered TTLs**.

## Data storage choices

### SQL vs NoSQL

- **SQL**: relational schema, ACID transactions, joins, strong consistency — default for structured data needing correctness (payments, orders).
- **NoSQL** families by access pattern: **key-value** (simple lookups), **document** (flexible JSON records), **wide-column** (heavy write/time-series), **graph** (relationship-heavy traversal). Design NoSQL tables around queries, not entities.
- Default to SQL unless there's a concrete reason (write volume, schema flexibility, a specific access pattern) — and name the reason. See [database.md](database.md) for indexes, isolation, storage engines.

### Scaling ladder

- In order of increasing complexity: query/index optimization → caching → read replicas (watch replication lag) → vertical scaling → federation by domain → **sharding** (needs a high-cardinality, evenly-distributed key; cross-shard joins/transactions get hard).
- **Denormalization** trades write complexity for read speed; **CQRS** (see [distributed.md](distributed.md)) separates write and read models entirely.

## Asynchronous processing

### Queues vs logs

- Queues **decouple** producers from consumers, absorb spikes, move slow work off the request path. Deliveries are at-least-once, so consumers must be **idempotent**; route repeated failures to a **dead-letter queue**.
- **RabbitMQ/SQS**: message removed once acknowledged, good for distributing discrete tasks. **Kafka**: durable append-only log, consumers track their own offsets so many consumer groups can replay the same data; order is guaranteed only **within a partition** — partition by entity ID when order matters.
- **Fan-out**: pub/sub (SNS, Kafka topics) delivers each event to many subscribers independently.

## Rate limiting

### Algorithms

| Algorithm | Behavior | Note |
|---|---|---|
| Token bucket | tokens refill at a fixed rate | allows bursts up to bucket size; most common |
| Leaky bucket | requests drain at a constant rate | smooth output, no bursts |
| Fixed window counter | count per time window | simple; up to 2× limit at window boundary |
| Sliding window log/counter | exact or blended count | accurate; counter variant is cheap |

- Enforced at the API gateway, keyed by user/API key/IP, returns **429** with `Retry-After`.
- Distributed setups keep counters in Redis (atomic `INCR` + expiry, or Lua scripts) so all servers share the same limit; a local per-instance limiter is less exact but skips the round trip.

## Reliability and operations

### Availability targets

- **SLI** = what's measured, **SLO** = internal target, **SLA** = contractual promise (looser than the SLO). The gap to 100% is the **error budget** — spend it on releases, slow down when exhausted.
- Series components multiply availability (99.9% × 99.9% ≈ 99.8%); redundant parallel components only fail together (1 − 0.001² ≈ 99.9999%).
- **RPO** (acceptable data loss) and **RTO** (acceptable recovery time) drive backup/failover design; **active-passive** (standby takes over) vs **active-active** (all serve traffic).

### Observability

- **Metrics** — numeric time series (Prometheus/Grafana); golden signals: latency, traffic, errors, saturation (**RED** for services, **USE** for resources).
- **Logs** — structured (JSON), centralized, tagged with a correlation/request ID.
- **Traces** — a request's span tree across services with a propagated trace ID (OpenTelemetry, Jaeger).
- Metrics say **something** is wrong, traces say **where**, logs say **why**. Alert on user-felt symptoms (error rate, latency, SLO burn rate), not every cause (CPU at 80%).

## Architecture

### Monolith vs microservices

- **Monolith**: simple to develop/deploy/debug, in-process calls, local transactions. Struggles with many teams in one codebase or parts needing very different scaling.
- **Microservices**: independent deploys/scaling, team autonomy, fault isolation — at the cost of network failures, distributed transactions (sagas, see [distributed.md](distributed.md)), and much more operational overhead.
- Default to a **modular monolith** with clear internal boundaries; extract services only for a concrete reason. Service boundaries tend to mirror team boundaries (**Conway's law**).

## Probabilistic and spatial structures

### Sketches

- **Bloom filter** — "definitely not" or "probably yes" set membership in a bit array + k hash functions; false positives possible, **false negatives impossible**; can't delete (counting variant can).
- **Count-min sketch** — estimates item frequency in a stream in fixed memory (heavy hitters, top-k).
- **HyperLogLog** — estimates distinct count (cardinality) in ~**12 KB** with ~**0.8%** error (Redis `PFADD`/`PFCOUNT`).
- **Geohash** encodes lat/lon as a sortable string prefix (nearby points share prefixes); a **quadtree** recursively subdivides space for variable-density range/nearest-neighbor queries.

## Classic designs

### URL shortener

- Read-heavy (~100:1); **base62** in 7 characters gives ~3.5 trillion keys.
- Key generation: hash + collision check, a counter/ID generator encoded in base62 (predictable unless shuffled), or a pre-generated key pool service.
- **301** (cached by browser, less load) vs **302** (every click hits you, lets you count clicks); cache hot keys, collect analytics asynchronously via a queue.

### News feed

- **Fan-out on write (push)**: precompute each follower's feed at post time — instant reads, but a celebrity triggers massive write amplification.
- **Fan-out on read (pull)**: merge followees' posts at read time — no write amplification, slower reads for heavy followers.
- **Hybrid**: push for normal accounts, pull for celebrities, merged at read time. Store post IDs, hydrate from cache; rank as a separate scoring step.

### Chat system

- Persistent **WebSocket** per client; a connection registry (user → server) routes delivery via pub/sub.
- Assign a **per-conversation sequence number** server-side for ordering (never trust client clocks); dedupe retries via a client-generated message ID.
- Offline delivery via push notification + fetch-on-reconnect; large groups face the same fan-out problem as celebrity feeds.

### Typeahead

- A **trie** (or prefix index) storing precomputed **top-k suggestions** per prefix node, built offline from query logs, cached aggressively, debounced client-side.
- For semantic variants, store embeddings and query an approximate nearest-neighbor index (HNSW).
