# System Design Cheatsheet

The 10 most frequently asked system design interview topics, with short answers. For CAP, consistency, replication, and sharding internals, see [distributed.md](distributed.md).

## 1. How do you approach a system design interview?

Follow a fixed structure and keep talking through it: **(1) requirements** — functional (what it does) and non-functional (scale, latency, availability, consistency); **(2) estimates** — users, QPS, storage, bandwidth; **(3) API** — main endpoints; **(4) data model** — entities and storage choice; **(5) high-level design** — boxes and arrows for the main request paths; **(6) deep dive** — the hardest 1–2 components; **(7) bottlenecks and trade-offs** — single points of failure, hot spots, what breaks at 10× load.

Numbers to know: 1 day ≈ **86,400 s ≈ 10⁵ s**, so 1M requests/day ≈ **12 QPS** (peak is often 2–3× the average). Latency: RAM read ~100 ns, SSD random read ~100 µs, round trip within a data center ~0.5 ms, cross-continent ~150 ms. Availability: **99.9% ≈ 8.8 h downtime/year**, **99.99% ≈ 53 min/year**. Clarify the requirements before drawing anything, and always say which trade-off you are making.

## 2. Vertical vs horizontal scaling?

**Vertical scaling** (scale up) means a bigger machine: more CPU, RAM, faster disks. It's simple and needs no code changes, but it has a hard ceiling, gets expensive, and is still a single point of failure. **Horizontal scaling** (scale out) means adding more machines behind a load balancer. There's no hard ceiling and it tolerates failures, but it adds complexity: distributed state, coordination, network failures.

To scale out, make application servers **stateless**: move sessions and state to a shared store (Redis, DB) or into signed tokens (JWT). Then any server can handle any request, and you can add or remove servers freely (**autoscaling**). The hard part is always the **stateful layer** (databases), which is scaled with replication and sharding.

## 3. How does load balancing work?

A load balancer spreads traffic across servers, runs **health checks** so it only routes to healthy instances, and often handles TLS termination. **L4** (transport layer) balancers route by IP/port. They're fast and don't look inside packets. **L7** (application layer) balancers look at HTTP: path, headers, cookies. That enables content-based routing, sticky sessions, and retries, at a higher CPU cost.

Algorithms: **round robin**, **weighted round robin**, **least connections** (good for requests of uneven length), **IP/consistent hash** (the same client or key goes to the same server, useful for caches). Avoid making the load balancer a single point of failure: run it in active-passive pairs, or use DNS/anycast in front of several load balancers. **Sticky sessions** work, but they defeat statelessness and make load uneven.

## 4. What caching strategies exist?

Caching trades freshness for speed. Layers: browser → CDN → application cache (Redis/Memcached) → database buffer pool. Patterns:
- **Cache-aside** (lazy loading) — the app reads the cache; on a miss it reads the DB and fills the cache. The most common pattern. Stale until TTL expires or the entry is invalidated.
- **Read-through** — the cache itself loads from the DB on a miss.
- **Write-through** — write to the cache and the DB together. Cache stays consistent, but writes are slower.
- **Write-back** (write-behind) — write to the cache, flush to the DB asynchronously. Fast writes, risk of data loss.

Eviction: **LRU** (most common), LFU, TTL. Hard problems: **invalidation** (delete the key on write instead of updating it, to avoid race conditions) and the **cache stampede** (many misses on a hot key hit the DB at once). Fix stampedes with request coalescing, locks, or early refresh with jittered TTLs.

## 5. SQL vs NoSQL — how do you choose?

**SQL** (PostgreSQL, MySQL): relational schema, **ACID transactions**, joins, strong consistency. The default choice for structured data with relationships and a need for correctness (payments, orders). Scales vertically plus read replicas. Sharding is possible, but the application or a proxy has to handle it.

**NoSQL** trades flexibility in queries for scale or a better fit to the data model: **key-value** (Redis, DynamoDB) for simple lookups; **document** (MongoDB) for flexible JSON-like records; **wide-column** (Cassandra, HBase) for heavy write loads and time series; **graph** (Neo4j) for data full of relationships. Most scale horizontally out of the box, often with eventual consistency. Choose based on **access patterns**: design NoSQL tables around your queries, not your entities. **Indexes** (usually B-trees; LSM trees in write-optimized stores) speed up reads but slow down writes and take storage.

## 6. How do you scale a database?

In order of increasing complexity:
1. **Query optimization and indexes** — check `EXPLAIN`, add missing indexes, fix N+1 queries.
2. **Caching** — take reads off the database.
3. **Read replicas** — send reads to followers. Watch out for **replication lag** (read-your-writes issues).
4. **Vertical scaling** — a bigger instance.
5. **Federation / functional partitioning** — split databases by domain (users DB, orders DB).
6. **Sharding** — split one table across nodes by a shard key. Choose a key with high cardinality and even distribution. Cross-shard joins and transactions become hard.

**Denormalization** (storing redundant copies of data so reads don't need joins) makes reads faster at the cost of write complexity. **CQRS** separates the write model from read models that are optimized for queries. Also use **connection pooling** (PgBouncer): databases often hit their connection limit before their CPU limit.

## 7. When and how do you use message queues?

Queues **decouple** producers from consumers, **absorb traffic spikes**, and move slow work off the request path (emails, video encoding, notifications). If a consumer is down, messages wait instead of being lost. You scale by adding consumers. Deliveries are at-least-once, so consumers must be **idempotent**. Put messages that keep failing into a **dead-letter queue**.

**RabbitMQ / SQS**: traditional queues — a message is removed once acknowledged, good for spreading tasks across workers. **Kafka**: a durable, append-only **log** split into partitions. Consumers track their own offsets, so many consumer groups can read the same data and **replay** it. Order is guaranteed only **within a partition**, so partition by entity ID when order matters. Pub/sub (SNS, Kafka topics) sends each event to many subscribers.

## 8. How do you design APIs? REST vs gRPC vs GraphQL?

- **REST** — resources + HTTP verbs, JSON, cacheable, available everywhere. The default for public APIs.
- **gRPC** — Protobuf over HTTP/2, strongly typed contracts, streaming, much faster. The default for internal service-to-service calls. Poor browser support.
- **GraphQL** — clients ask for exactly the fields they need in one round trip. Good for varied frontends. Harder to cache, and needs protection against expensive queries.

Common details: **cursor-based pagination** (stable and fast; offset pagination gets slow on deep pages and skips items when data changes), **versioning** (`/v1/`), **idempotency keys** for safe retries of POST, correct status codes. For real-time updates: **short polling** (simple, wasteful), **long polling**, **Server-Sent Events** (one-way server→client), **WebSockets** (two-way, stateful connections that are harder to scale).

## 9. How does rate limiting work?

Rate limiting protects services from abuse and overload. It is usually enforced at the **API gateway**, keyed by user, API key, or IP, and returns **HTTP 429** with a `Retry-After` header. Algorithms:
- **Token bucket** — tokens refill at a fixed rate, and each request uses one. Allows **bursts** up to the bucket size. The most common choice.
- **Leaky bucket** — requests drain from a queue at a constant rate. Output is smooth, with no bursts.
- **Fixed window counter** — count per time window. Simple, but allows up to 2× the limit at window boundaries.
- **Sliding window log / counter** — accurate and smooth. The counter variant blends the current and previous window's counts and is cheap.

In a distributed setup, keep counters in **Redis** (atomic `INCR` + expiry, or Lua scripts) so all servers share the same limits. A local limiter per instance is less exact but avoids a round trip to Redis on every request.

## 10. What are CDNs and object storage for?

A **CDN** (CloudFront, Cloudflare, Akamai) caches content on **edge servers close to users**, cutting latency and load on your own servers. Best for static assets (images, JS, video). It can also cache API responses and absorb DDoS attacks. **Pull CDN**: the edge fetches from your server on the first miss (simple, the first request is slow). **Push CDN**: you upload content ahead of time (good for large, rarely changing files). Invalidate with **versioned file names** (`app.3f9a.js`) rather than purges.

**Object/blob storage** (S3, GCS) stores large unstructured files (uploads, videos, backups) cheaply, durably (11 nines), and with no practical size limit. Keep the files there and only **metadata and URLs in the database**. Let clients upload and download directly with **pre-signed URLs**, so large files don't pass through your app servers. For video, add **transcoding** to several bitrates plus **adaptive streaming** (HLS/DASH).
