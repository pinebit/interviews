# System Design

Key system design building blocks and trade-offs, grouped by subtopic. For CAP, consistency, replication, and sharding internals, see [distributed.md](distributed.md); for API design, idempotency, and outbox, see [backend.md](backend.md); for auth and web security, see [security.md](security.md).

## Interview framework

### Structure and estimates

- Order: **requirements** (functional + scale, latency, availability, consistency) → estimates → API → data model → high-level design → **deep dive** on the hardest 1–2 parts → bottlenecks and trade-offs.
- Latencies: RAM read ~100 ns, SSD random read ~100 µs, same-DC round trip ~0.5 ms, cross-continent ~150 ms.
- Downtime per year: 99.9% ≈ **8.8 h**, 99.99% ≈ 53 min, 99.999% ≈ 5 min.

### Back-of-envelope conversions

- 1 day ≈ 86,400 s ≈ 10⁵ s, so **1M requests/day ≈ 12 QPS**; peak ≈ 2–3× average.
- 1 KB × 1M items = 1 GB; 1 KB × 1B = 1 TB.
- A well-indexed PostgreSQL box handles roughly **10k+ simple queries/s**; Redis ~100k ops/s per core.

## Traffic and edge

### Load balancing

- **L4** balances by IP/port, fast, no inspection; **L7** reads HTTP (path, headers, cookies) for content routing and retries, at higher CPU cost.
- Algorithms: round robin, weighted, **least connections** (uneven request lengths), IP/consistent hash (same key → same server, good for caches).
- Sticky sessions defeat statelessness and unbalance load — move session state to a shared store instead.

### Balancing long-lived connections

- HTTP/2 and **gRPC** multiplex all requests over one long-lived connection, so an L4 balancer pins a client to one backend and new replicas get no traffic.
- Fix with L7 (per-request) balancing, client-side balancing, or a **maximum connection age** that forces reconnects.
- WebSockets have the same problem after scale-out: rebalance by closing connections gradually.

### Proxies and gateways

- **Reverse proxy** (Nginx, Envoy): TLS termination, load balancing, caching in front of servers.
- **API gateway**: auth, rate limiting, routing, aggregation for north–south traffic; a BFF is one gateway per client type.
- **Service mesh** (Istio, Linkerd): sidecar proxies handle east–west traffic — mTLS, retries, telemetry without app changes.

### Real-time delivery to clients

| Transport | Direction | Note |
|---|---|---|
| Short polling | client pulls | simple, wasteful, latency = interval |
| Long polling | client pulls, server holds | works everywhere, one request per message |
| **SSE** | server → client | plain HTTP, auto-reconnect with `Last-Event-ID`, text only |
| **WebSocket** | both ways | stateful connections — needs sticky routing and a connection registry |

- Push to many clients means **stateful** servers: plan for reconnect storms after a deploy (jittered reconnects).

### CDN and object storage

- **Pull CDN** fetches from origin on first miss; **push CDN** is pre-uploaded (large, rarely changing files). Invalidate with versioned filenames, not purges.
- Object storage (S3, GCS) holds blobs cheaply and durably; keep only metadata in the database and use **pre-signed URLs** so transfers bypass app servers.

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
- **Cache stampede**: many concurrent misses on a hot key hit the DB at once — fix with request coalescing (single-flight), a lock, or probabilistic early refresh.
- **Jitter TTLs** so keys written together don't expire together.

### Cache and database consistency

- On write, **delete** the key rather than updating it, so concurrent writers can't leave an older value in place.
- Cache-aside still races: a slow reader can refill the cache with a value read before the write — bound it with a TTL, a delayed second delete, or **leases** (Facebook memcache).
- For many writers, invalidate from the database's change stream (**CDC**) instead of from application code.

## Data storage choices

### SQL vs NoSQL

- **SQL**: relational schema, ACID transactions, joins — the default for data needing correctness (payments, orders).
- NoSQL families by access pattern: key-value, document, **wide-column** (heavy writes, time series), graph; model tables around queries, not entities.
- Pick NoSQL only for a named reason (write volume, schema flexibility, access pattern). Internals in [database.md](database.md).

### Scaling ladder

- Cheapest first: query/index tuning → caching → read replicas → vertical scaling → split databases by domain → **sharding**.
- Sharding needs a high-cardinality, evenly spread key; cross-shard joins and transactions become the app's problem.
- **Denormalization** trades write complexity for read speed; CQRS separates the models entirely ([distributed.md](distributed.md)).

## Asynchronous processing

### Queue semantics

- Queues decouple producers from consumers, absorb spikes, and move slow work off the request path.
- Delivery is at-least-once, so consumers must be **idempotent**; route repeatedly failing messages to a **dead-letter queue**.
- **Fan-out**: pub/sub (SNS, Kafka topics) delivers each event to many subscribers independently.

### Queues vs logs

- **RabbitMQ/SQS** (queue): a message is removed once acknowledged — distributes tasks among workers.
- **Kafka** (log): a durable append-only log; each consumer group tracks its own offset, so many groups can **replay** the same data.
- Partitioning and ordering: see [distributed.md](distributed.md).

## Rate limiting

### Rate-limiting algorithms

| Algorithm | Behavior | Note |
|---|---|---|
| Token bucket | tokens refill at a fixed rate | allows bursts up to bucket size; most common |
| Leaky bucket | requests drain at a constant rate | smooth output, no bursts |
| Fixed window counter | count per time window | simple; up to 2× limit at window boundary |
| Sliding window log/counter | exact or blended count | accurate; counter variant is cheap |

### Distributed rate limiting

- Enforce at the gateway, keyed by user, API key, or IP; reject with **429** and `Retry-After`.
- Share counters in **Redis** (atomic `INCR` + expiry, or a Lua script) so every server sees one limit.
- A local per-instance limiter skips the round trip but is only approximate (limit ÷ instances).

## Reliability and operations

### Availability math

- Components in **series** multiply: 99.9% × 99.9% ≈ 99.8%.
- Redundant components in **parallel** fail only together: 1 − 0.001² ≈ 99.9999%, if failures are independent.
- RPO (acceptable data loss) and RTO (acceptable recovery time) drive backup and failover design; active-passive vs active-active.

### SLIs, SLOs, error budgets

- SLI = what's measured, **SLO** = internal target, SLA = contractual promise (looser than the SLO).
- The gap to 100% is the **error budget** — spend it on releases, slow down when it's exhausted.
- Alert on SLO **burn rate** and user-felt symptoms, not on every cause (CPU at 80%).

### Observability

- Metrics: numeric time series (Prometheus); **golden signals** latency, traffic, errors, saturation — **RED** for services, **USE** for resources.
- Logs: structured, centralized, tagged with a request ID. Traces: a request's span tree across services (OpenTelemetry).
- Metrics say something is wrong, traces say where, logs say why.

## Architecture

### Monolith vs microservices

- Monolith: simple to develop, deploy, and debug, with in-process calls and local transactions; struggles with many teams or very different scaling needs.
- Microservices: independent deploys and scaling, at the cost of network failures, distributed transactions, and operational overhead.
- Default to a **modular monolith**; extract services for a concrete reason. Boundaries mirror teams (**Conway's law**).

### Service discovery

- Instances register with a registry (Consul, etcd, Eureka) and drop out on failed health checks; clients or a load balancer resolve names to healthy instances.
- Kubernetes does this natively with Service DNS names — see [devops.md](devops.md).

## Probabilistic and spatial structures

### Bloom filter

- Set membership in a bit array with `k` hash functions: "definitely not" or "probably yes" — **no false negatives**.
- Can't delete (a counting variant can); used to skip disk lookups (LSM trees) and dedupe crawled URLs.

### Count-min sketch and HyperLogLog

- **Count-min sketch** estimates per-item frequency in fixed memory — heavy hitters, top-k in a stream.
- **HyperLogLog** estimates distinct counts in ~**12 KB** with ~0.8% error (Redis `PFADD`/`PFCOUNT`).

### Geospatial indexes

- **Geohash** encodes lat/lon as a string where nearby points share a prefix; query a cell and its **8 neighbors**, since close points can straddle a boundary.
- A **quadtree** subdivides dense areas further, adapting to uneven density; Google S2 and Uber H3 use hierarchical cells the same way.

## Classic designs: user-facing

### URL shortener

- Read-heavy (~100:1); **base62** in 7 characters gives ~3.5 trillion keys.
- Keys from hash + collision check, a counter encoded in base62 (predictable unless shuffled), or a pre-generated key pool.
- **301** is cached by browsers (less load); 302 hits you on every click (analytics). Collect analytics asynchronously.

### News feed

- **Fan-out on write**: precompute followers' feeds at post time — instant reads, but a celebrity triggers massive write amplification.
- **Fan-out on read**: merge followees' posts at read time — slower reads, no amplification.
- **Hybrid**: push for normal accounts, pull for celebrities; store post IDs, hydrate from cache, rank as a separate step.

### Chat system

- A persistent **WebSocket** per client; a connection registry (user → server) routes messages via pub/sub.
- A server-assigned **per-conversation sequence number** orders messages; a client-generated message ID dedupes retries.
- Offline users get a push notification and fetch on reconnect; large groups hit the same fan-out problem as feeds.

### Typeahead

- A **trie** (or prefix index) with precomputed **top-k suggestions** per node, built offline from query logs and cached aggressively.
- Debounce on the client; for semantic matches, query an approximate nearest-neighbor index (HNSW).

### Notification system

- One API → a queue per channel (push, SMS, email) → workers calling providers (APNs, FCM, Twilio) with retries.
- Dedupe by **notification ID**, respect user preferences and rate limits, track delivery status per message.

### Proximity service

- Index places by **geohash** prefix or quadtree cell; search the cell plus neighbors, then filter by exact distance.
- Static places are read-heavy — cache per cell; moving objects (drivers) report every few seconds into an in-memory index (Redis GEO).

## Classic designs: data and infrastructure

### Web crawler

- A **URL frontier** of per-host queues enforces politeness (one connection per host, `robots.txt`, crawl delay) and priority.
- Dedupe URLs with a seen-set (Bloom filter at scale) and content with checksums or **SimHash**.
- Cache DNS; guard against spider traps with URL depth and length limits.

### File sync

- Split files into **chunks** (~4 MB) addressed by content hash: upload only changed chunks and dedupe identical ones across users.
- A metadata service stores file → chunk list and versions; other devices get change notifications via long polling or WebSocket.
- Concurrent edits produce a **conflicted copy** rather than a silent overwrite.

### Metrics and click aggregation

- Events flow through Kafka into a stream processor that aggregates per key per **tumbling window**, by event time with watermarks ([distributed.md](distributed.md)).
- Keep raw events so aggregates can be **recomputed** after a bug; dedupe by event ID.
- Pre-aggregate hot keys locally before the shuffle.

### Distributed job scheduler

- Store jobs with `next_run_at`; workers claim due rows with **`FOR UPDATE SKIP LOCKED`** or a lease, so each run has one owner.
- An expired lease hands a dead worker's job to another, so jobs must be **idempotent**.
- At high volume, partition jobs by ID or bucket them by time (a **timing wheel**).

### Payments and ledgers

- A **double-entry ledger**: every transaction is balanced debits and credits; rows are append-only, corrections are new entries.
- **Idempotency keys** on every provider call; reconcile against provider reports daily.
- Store amounts as **integer minor units** with a currency, never floats.

### Leaderboard

- A Redis **sorted set**: `ZINCRBY` updates a score, `ZREVRANGE` reads the top N, `ZREVRANK` a user's rank — all O(log n).
- Beyond one node, shard by score range or keep per-shard top-k and merge.

### Booking and inventory contention

- Overselling comes from check-then-write races: use **conditional updates** (`UPDATE ... SET left = left - 1 WHERE id = ? AND left > 0`) or row locks.
- For seat selection, place a **temporary hold with a TTL** that expires if payment doesn't finish; a waiting room absorbs flash-sale spikes.
