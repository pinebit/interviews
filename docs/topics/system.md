# System Design

Key system design building blocks and trade-offs, grouped by subtopic. For CAP, consistency, replication, and sharding internals, see [distributed.md](distributed.md); for API design, idempotency, and outbox, see [backend.md](backend.md); for auth and web security, see [security.md](security.md).

## Interview framework

### Structure and estimates

- Order: requirements (functional + scale, latency, availability, consistency) → estimates → API → data model → high-level design → deep dive on the hardest 1–2 parts → bottlenecks and trade-offs.
- Latencies: RAM read ~100 ns, SSD random read ~100 µs, same-DC round trip ~0.5 ms, cross-continent ~150 ms.
- [Downtime per year](https://en.wikipedia.org/wiki/High_availability#Percentage_calculation): 99.9% ≈ 8.8 h, 99.99% ≈ 53 min, 99.999% ≈ 5 min.

### Back-of-envelope conversions

- 1 day ≈ 86,400 s ≈ 10⁵ s, so 1M requests/day ≈ 12 QPS; assume peak ≈ 2–3× average unless told otherwise.
- 1 KB × 1M items = 1 GB; 1 KB × 1B = 1 TB.
- Ballpark capacity (varies with workload): a well-indexed PostgreSQL box handles 10k+ simple queries/s; Redis ~100k ops/s per core.
- [Little's law](https://en.wikipedia.org/wiki/Little%27s_law) L = λ × W: requests in flight = throughput × latency — 1,000 RPS × 200 ms = 200 concurrent requests, which sizes thread pools, connection pools, and queues.

## Traffic and edge

### Load balancing

- [L4](https://en.wikipedia.org/wiki/Transport_layer) balances by IP/port, fast, no inspection; [L7](https://en.wikipedia.org/wiki/Application_layer) reads HTTP (path, headers, cookies) for content routing and retries, at higher CPU cost.
- Algorithms: round robin, weighted, least connections (uneven request lengths), IP/[consistent hash](https://en.wikipedia.org/wiki/Consistent_hashing) (same key → same server, good for caches).
- [Sticky sessions](https://en.wikipedia.org/wiki/Load_balancing_%28computing%29#Persistence) defeat statelessness and unbalance load — move session state to a shared store instead.

### Balancing long-lived connections

- [HTTP/2](https://www.rfc-editor.org/rfc/rfc9113) and [gRPC](https://grpc.io/blog/grpc-load-balancing/) multiplex all requests over one long-lived connection, so an L4 balancer pins a client to one backend and new replicas get no traffic.
- Fix with L7 (per-request) balancing, client-side balancing, or a [maximum connection age](https://github.com/grpc/proposal/blob/master/A9-server-side-conn-mgt.md) that forces reconnects.
- [WebSockets](https://www.rfc-editor.org/rfc/rfc6455) have the same problem after scale-out: rebalance by closing connections gradually.

### Proxies and gateways

- [Reverse proxy](https://en.wikipedia.org/wiki/Reverse_proxy) ([Nginx](https://nginx.org/en/docs/), [Envoy](https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy)): TLS termination, load balancing, caching in front of servers.
- [API gateway](https://learn.microsoft.com/en-us/azure/architecture/microservices/design/gateway): auth, rate limiting, routing, aggregation for north–south traffic; a [BFF](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends) is one gateway per client type.
- [Service mesh](https://en.wikipedia.org/wiki/Service_mesh) ([Istio](https://istio.io/latest/docs/overview/what-is-istio/), [Linkerd](https://linkerd.io/what-is-a-service-mesh/)): sidecar proxies (or per-node proxies in [Istio ambient mode](https://istio.io/latest/docs/ambient/overview/)) handle east–west traffic — [mTLS](https://en.wikipedia.org/wiki/Mutual_authentication#mTLS), retries, telemetry without app changes.

### Real-time delivery to clients

| Transport | Direction | Note |
|---|---|---|
| Short polling | client pulls | simple, wasteful, latency = interval |
| [Long polling](https://en.wikipedia.org/wiki/Push_technology#Long_polling) | client pulls, server holds | works everywhere, one request per message |
| [SSE](https://html.spec.whatwg.org/multipage/server-sent-events.html) | server → client | plain HTTP, auto-reconnect with [`Last-Event-ID`](https://html.spec.whatwg.org/multipage/server-sent-events.html#the-last-event-id-header), text only |
| [WebSocket](https://www.rfc-editor.org/rfc/rfc6455) | both ways | stateful connections — needs a connection registry to find the server holding a user |

- Push to many clients means stateful servers: plan for reconnect storms after a deploy ([jittered](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) reconnects).

### CDN and object storage

- Pull [CDN](https://en.wikipedia.org/wiki/Content_delivery_network) fetches from origin on first miss; push CDN is pre-uploaded (large, rarely changing files). Invalidate with versioned filenames, not purges.
- [Object storage](https://en.wikipedia.org/wiki/Object_storage) ([S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), [GCS](https://cloud.google.com/storage/docs/introduction)) holds blobs cheaply and durably; keep only metadata in the database and use [pre-signed URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html) so transfers bypass app servers.

## Caching

### Strategies

| Pattern | Write path | Read path | Trade-off |
|---|---|---|---|
| [Cache-aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) | app writes DB, invalidates cache | miss → read DB, fill cache | most common; stale until TTL/invalidation |
| Read-through | — | cache loads from DB on miss | cache owns the loading logic |
| [Write-through](https://en.wikipedia.org/wiki/Cache_%28computing%29#Write_policies) | write cache + DB together | cache always warm | slower writes; the two writes aren't atomic, so a crash or race can still diverge them |
| [Write-behind](https://en.wikipedia.org/wiki/Cache_%28computing%29#Write_policies) | write cache, flush DB async | fast writes | risk of data loss before flush |

### Eviction and stampedes

- [Eviction](https://en.wikipedia.org/wiki/Cache_replacement_policies): [LRU](https://en.wikipedia.org/wiki/Cache_replacement_policies#LRU) (most common), [LFU](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_frequently_used_%28LFU%29), TTL.
- [Cache stampede](https://en.wikipedia.org/wiki/Cache_stampede): many concurrent misses on a hot key hit the DB at once — fix with request coalescing ([single-flight](https://pkg.go.dev/golang.org/x/sync/singleflight)), a lock, or [probabilistic early refresh](https://en.wikipedia.org/wiki/Cache_stampede#Probabilistic_early_expiration).
- Jitter TTLs so keys written together don't expire together.

### Cache and database consistency

- On write, delete the key rather than updating it, so concurrent writers can't leave an older value in place.
- Cache-aside still races: a slow reader can refill the cache with a value read before the write — bound it with a TTL, a delayed second delete, or [leases (Facebook memcache)](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala).
- For many writers, invalidate from the database's change stream ([CDC](distributed.md)) instead of from application code.

## Data storage choices

### SQL vs NoSQL

- [NoSQL](https://en.wikipedia.org/wiki/NoSQL) families by access pattern: [key-value](https://en.wikipedia.org/wiki/Key%E2%80%93value_database), [document](https://en.wikipedia.org/wiki/Document-oriented_database), [wide-column](https://en.wikipedia.org/wiki/Wide-column_store) (heavy writes, time series), [graph](https://en.wikipedia.org/wiki/Graph_database); model tables around queries, not entities.
- Pick NoSQL only for a named reason (write volume, schema flexibility, access pattern). Internals in [database.md](database.md).

### Scaling ladder

- Cheapest first: query/index tuning → caching → read replicas → vertical scaling → split databases by domain → [sharding](https://en.wikipedia.org/wiki/Shard_%28database_architecture%29).
- Sharding needs a high-cardinality, evenly spread key; cross-shard joins and transactions become the app's problem.
- [Denormalization](https://en.wikipedia.org/wiki/Denormalization) trades write complexity for read speed; [CQRS](https://martinfowler.com/bliki/CQRS.html) separates the models entirely ([distributed.md](distributed.md)).

## Asynchronous processing

### Queue semantics

- [Queues](https://en.wikipedia.org/wiki/Message_queue) decouple producers from consumers, absorb spikes, and move slow work off the request path.
- Delivery is at-least-once, so consumers must be idempotent; route repeatedly failing messages to a [dead-letter queue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html).
- Fan-out: [pub/sub](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern) ([SNS](https://docs.aws.amazon.com/sns/latest/dg/welcome.html), [Kafka topics](https://kafka.apache.org/43/getting-started/introduction/#main-concepts-and-terminology)) delivers each event to many subscribers independently.

### Queues vs logs

- [RabbitMQ](https://www.rabbitmq.com/docs/confirms)/[SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (queue): a message is removed once acknowledged — distributes tasks among workers.
- [Kafka](https://kafka.apache.org/43/getting-started/introduction/#main-concepts-and-terminology) (log): a durable append-only log; each [consumer group](https://kafka.apache.org/43/design/design/#consumer-position) tracks its own offset, so many groups can replay the same data.
- Partitioning and ordering: see [distributed.md](distributed.md).

## Rate limiting

### Rate-limiting algorithms

| Algorithm | Behavior | Note |
|---|---|---|
| [Token bucket](https://en.wikipedia.org/wiki/Token_bucket) | tokens refill at a fixed rate | allows bursts up to bucket size; most common |
| [Leaky bucket](https://en.wikipedia.org/wiki/Leaky_bucket) | requests drain at a constant rate | smooth output, no bursts |
| Fixed window counter | count per time window | simple; up to 2× limit at window boundary |
| [Sliding window log/counter](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/) | exact or blended count | accurate; counter variant is cheap |

### Distributed rate limiting

- Enforce at the gateway, keyed by user, API key, or IP; reject with [429](https://www.rfc-editor.org/rfc/rfc6585#section-4) and [`Retry-After`](https://www.rfc-editor.org/rfc/rfc9110#field.retry-after).
- Share counters in Redis so every server sees one limit; wrap [`INCR`](https://redis.io/docs/latest/commands/incr/) + [`EXPIRE`](https://redis.io/docs/latest/commands/expire/) in [`MULTI`](https://redis.io/docs/latest/develop/using-commands/transactions/) or a [Lua script](https://redis.io/docs/latest/develop/programmability/eval-intro/), or a crash between them leaves a counter with no TTL.
- A local per-instance limiter skips the round trip but is only approximate (limit ÷ instances).

## Reliability and operations

### Availability math

- Components in [series](https://en.wikipedia.org/wiki/Reliability_block_diagram) multiply: 99.9% × 99.9% ≈ 99.8%.
- Redundant components in parallel fail only together: 1 − 0.001² ≈ 99.9999%.
- Both formulas assume independent failures; a shared zone or dependency wipes out most of the parallel redundancy gain.

### Multi-region and disaster recovery

- [RPO](https://en.wikipedia.org/wiki/Recovery_point_objective) = acceptable data loss, [RTO](https://en.wikipedia.org/wiki/Recovery_time_objective) = acceptable recovery time; together they pick the tier.

| Tier | What runs in the standby region | RTO / RPO |
|---|---|---|
| [Backup and restore](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) | nothing; restore from backups | hours / hours |
| [Pilot light](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) | replicated data, compute off | tens of minutes / minutes |
| [Warm standby](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) | a scaled-down copy | minutes / seconds |
| [Active-active](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) | full capacity everywhere | ~zero / ~zero with sync replication |

- Async cross-region replication means RPO > 0; active-active also needs conflict handling or a home region per record, plus global routing ([GeoDNS](https://en.wikipedia.org/wiki/GeoDNS), [anycast](https://en.wikipedia.org/wiki/Anycast)).
- A failover that was never rehearsed rarely works: run regular [game days](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_game_days_resiliency.html).

### SLIs, SLOs, error budgets

- [SLI](https://sre.google/sre-book/service-level-objectives/) = what's measured, SLO = internal target, SLA = contractual promise (looser than the SLO).
- The gap to 100% is the [error budget](https://sre.google/workbook/error-budget-policy/) — spend it on releases, slow down when it's exhausted.
- Alert on SLO [burn rate](https://sre.google/workbook/alerting-on-slos/) and user-felt symptoms, not on every cause (CPU at 80%).

### Observability

- Metrics: numeric time series ([Prometheus](https://prometheus.io/docs/introduction/overview/)); [golden signals](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) latency, traffic, errors, saturation — [RED](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) for services, [USE](https://www.brendangregg.com/usemethod.html) for resources.
- Logs: structured, centralized, tagged with a request ID. Traces: a request's span tree across services ([OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/traces/)).
- Metrics say something is wrong, traces say where, logs say why.
- Percentiles can't be averaged across hosts or time windows: merge the [histograms](https://prometheus.io/docs/practices/histograms/) (or sketches), then take p99.
- [High-cardinality labels](https://prometheus.io/docs/practices/naming/#labels) (user ID, request ID) multiply Prometheus time series; keep them in logs and traces.

## Architecture

### Monolith vs microservices

- Default to a modular monolith: in-process calls and local transactions, with module boundaries that could later become services.
- Extract a service for a concrete reason (independent scaling, deploy cadence, team ownership); boundaries mirror teams ([Conway's law](https://en.wikipedia.org/wiki/Conway%27s_law)).

### Service discovery

- Instances register with a registry ([Consul](https://developer.hashicorp.com/consul/docs), [etcd](https://etcd.io/docs/), [Eureka](https://github.com/Netflix/eureka)) and drop out on failed health checks; clients or a load balancer resolve names to healthy instances.
- Kubernetes does this natively with [Service DNS names](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) — see [devops.md](devops.md).

## Probabilistic and spatial structures

### Bloom filter

- [Set membership](https://en.wikipedia.org/wiki/Bloom_filter) in a bit array with `k` hash functions: "definitely not" or "probably yes" — no false negatives.
- Can't delete (a [counting variant](https://en.wikipedia.org/wiki/Counting_Bloom_filter) can); used to skip disk lookups ([LSM trees](https://en.wikipedia.org/wiki/Log-structured_merge-tree)) and dedupe crawled URLs.

### Count-min sketch and HyperLogLog

- [Count-min sketch](https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch) estimates per-item frequency in fixed memory — heavy hitters, top-k in a stream.
- [HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog) estimates distinct counts in ~12 KB with ~0.8% error (Redis [`PFADD`/`PFCOUNT`](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/)).

### Geospatial indexes

- [Geohash](https://en.wikipedia.org/wiki/Geohash) encodes lat/lon as a string: a shared prefix means nearby, but close points can straddle a cell boundary and share none.
- Pick a precision whose cell is at least the search radius, then query the cell and its 8 neighbors.
- A [quadtree](https://en.wikipedia.org/wiki/Quadtree) subdivides dense areas further, adapting to uneven density; Google [S2](https://s2geometry.io/) and Uber [H3](https://h3geo.org/) use hierarchical cells the same way.

## Classic designs: user-facing

### URL shortener

- Read-heavy (~100:1); [base62](https://en.wikipedia.org/wiki/Base62) in 7 characters gives ~3.5 trillion keys.
- Keys from hash + collision check, a counter encoded in base62 (predictable unless shuffled), or a pre-generated key pool.
- [301](https://www.rfc-editor.org/rfc/rfc9110#status.301) is [cached by browsers by default](https://www.rfc-editor.org/rfc/rfc9111#heuristic.freshness) (less load, lost clicks); [302](https://www.rfc-editor.org/rfc/rfc9110#status.302) isn't cached without explicit freshness headers, so every click hits you (analytics). Collect analytics asynchronously.

### News feed

- Fan-out on write: precompute followers' feeds at post time — instant reads, but a celebrity triggers massive write amplification.
- Fan-out on read: merge followees' posts at read time — slower reads, no amplification.
- Hybrid: push for normal accounts, pull for celebrities; store post IDs, hydrate from cache, rank as a separate step.

### Chat system

- A persistent [WebSocket](https://www.rfc-editor.org/rfc/rfc6455) per client; a connection registry (user → server) routes messages via [pub/sub](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern).
- A server-assigned per-conversation sequence number orders messages; a client-generated message ID dedupes retries.
- Offline users get a push notification and fetch on reconnect; large groups hit the same fan-out problem as feeds.

### Typeahead

- A [trie](https://en.wikipedia.org/wiki/Trie) (or prefix index) with precomputed top-k suggestions per node, built offline from query logs and cached aggressively.
- [Debounce](https://developer.mozilla.org/en-US/docs/Glossary/Debounce) on the client; for semantic matches, query an [approximate nearest-neighbor](https://en.wikipedia.org/wiki/Nearest_neighbor_search#Approximation_methods) index ([HNSW](https://en.wikipedia.org/wiki/Hierarchical_navigable_small_world)).

### Video streaming

- Upload to object storage → a [transcoding](https://en.wikipedia.org/wiki/Transcoding) pipeline splits the video into chunks and encodes them in parallel at several resolutions and bitrates.
- Package as [HLS](https://www.rfc-editor.org/rfc/rfc8216) or [DASH](https://en.wikipedia.org/wiki/Dynamic_Adaptive_Streaming_over_HTTP): 2–10 s segments plus a manifest listing the renditions, served from a CDN.
- The player picks a rendition per segment from measured bandwidth and buffer ([adaptive bitrate](https://en.wikipedia.org/wiki/Adaptive_bitrate_streaming)), so quality drops instead of stalling.
- Pre-warm popular titles at the edge; the long tail streams from regional caches or the origin.

### Notification system

- One API → a queue per channel (push, SMS, email) → workers calling providers ([APNs](https://developer.apple.com/documentation/usernotifications), [FCM](https://firebase.google.com/docs/cloud-messaging), [Twilio](https://www.twilio.com/docs/messaging)) with retries.
- Dedupe by notification ID, respect user preferences and rate limits, track delivery status per message.

### Proximity service

- Index places by [geohash](https://en.wikipedia.org/wiki/Geohash) prefix or [quadtree](https://en.wikipedia.org/wiki/Quadtree) cell; search the cell plus neighbors, then filter by exact distance.
- Static places are read-heavy — cache per cell; moving objects (drivers) report every few seconds into an in-memory index ([Redis GEO](https://redis.io/docs/latest/develop/data-types/geospatial/)).

## Classic designs: data and infrastructure

### Web crawler

- A [URL frontier](https://en.wikipedia.org/wiki/Crawl_frontier) of per-host queues enforces politeness (one connection per host, [`robots.txt`](https://www.rfc-editor.org/rfc/rfc9309), crawl delay) and priority.
- Dedupe URLs with a seen-set ([Bloom filter](https://en.wikipedia.org/wiki/Bloom_filter) at scale) and content with checksums or [SimHash](https://en.wikipedia.org/wiki/SimHash).
- Cache DNS; guard against [spider traps](https://en.wikipedia.org/wiki/Spider_trap) with URL depth and length limits.

### File sync

- Split files into chunks (~4 MB) addressed by [content hash](https://en.wikipedia.org/wiki/Content-addressable_storage): upload only changed chunks and dedupe identical ones across users.
- A metadata service stores file → chunk list and versions; other devices get change notifications via [long polling](https://en.wikipedia.org/wiki/Push_technology#Long_polling) or [WebSocket](https://www.rfc-editor.org/rfc/rfc6455).
- Concurrent edits produce a conflicted copy rather than a silent overwrite.

### Metrics and click aggregation

- Events flow through [Kafka](https://kafka.apache.org/43/getting-started/introduction/#main-concepts-and-terminology) into a stream processor that aggregates per key per [tumbling window](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/#tumbling-windows), by event time with watermarks ([distributed.md](distributed.md)).
- Keep raw events so aggregates can be recomputed after a bug; dedupe by event ID.
- Pre-aggregate hot keys locally before the shuffle.

### Distributed job scheduler

- Store jobs with `next_run_at`; workers claim due rows with [`FOR UPDATE SKIP LOCKED`](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE) or a lease, so each run has one owner.
- An expired lease hands a dead worker's job to another, so jobs must be idempotent.
- At high volume, partition jobs by ID or bucket them by time (a [timing wheel](https://www.confluent.io/blog/apache-kafka-purgatory-hierarchical-timing-wheels/)).

### Payments and ledgers

- A [double-entry ledger](https://en.wikipedia.org/wiki/Double-entry_bookkeeping): every transaction is balanced debits and credits; rows are append-only, corrections are new entries.
- [Idempotency keys](backend.md) on every provider call; reconcile against provider reports daily.
- Store amounts as [integer minor units](https://docs.stripe.com/currencies#minor-units) with a currency, never floats.

### Leaderboard

- A Redis [sorted set](https://redis.io/docs/latest/develop/data-types/sorted-sets/): [`ZINCRBY`](https://redis.io/docs/latest/commands/zincrby/) updates a score and [`ZREVRANK`](https://redis.io/docs/latest/commands/zrevrank/) returns a user's rank in O(log n); [`ZRANGE ... REV`](https://redis.io/docs/latest/commands/zrange/) reads the top k in O(log n + k).
- Beyond one node, shard by score range or keep per-shard top-k and merge.

### Booking and inventory contention

- Overselling comes from check-then-write races: use conditional updates (`UPDATE ... SET left = left - 1 WHERE id = ? AND left > 0`) or [row locks](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS).
- For seat selection, place a temporary hold with a TTL that expires if payment doesn't finish; a waiting room absorbs flash-sale spikes.
