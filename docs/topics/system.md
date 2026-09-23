# System Design Cheatsheet

The 20 most frequently asked system design interview topics, with short answers. For CAP, consistency, replication, and sharding internals, see [distributed.md](distributed.md).

## 1. How do you approach a system design interview?

Follow a fixed structure and keep talking through it: **(1) requirements** — functional (what it does) and non-functional (scale, latency, availability, consistency); **(2) estimates** — users, QPS, storage, bandwidth; **(3) API** — main endpoints; **(4) data model** — entities and storage choice; **(5) high-level design** — boxes and arrows for the main request paths; **(6) deep dive** — the hardest 1–2 components; **(7) bottlenecks and trade-offs** — single points of failure, hot spots, what breaks at 10× load.

Numbers to know: 1 day ≈ **86,400 s ≈ 10⁵ s**, so 1M requests/day ≈ **12 QPS** (peak is often 2–3× the average). Latency: RAM read ~100 ns, SSD random read ~100 µs, round trip within a data center ~0.5 ms, cross-continent ~150 ms. Availability: **99.9% ≈ 8.8 h downtime/year**, **99.99% ≈ 53 min/year**.

Clarify the requirements before drawing anything, and always say which trade-off you are making. Interviewers grade the reasoning, not a "correct" diagram.

## 2. What caching strategies exist?

Caching trades freshness for speed. Layers: browser → CDN → application cache (Redis/Memcached) → database buffer pool. Patterns:

- **Cache-aside** (lazy loading) — the app reads the cache; on a miss it reads the DB and fills the cache. The most common pattern. Stale until TTL expires or the entry is invalidated.
- **Read-through** — the cache itself loads from the DB on a miss.
- **Write-through** — write to the cache and the DB together. Cache stays consistent, but writes are slower.
- **Write-back** (write-behind) — write to the cache, flush to the DB asynchronously. Fast writes, risk of data loss.

Eviction: **LRU** (most common), LFU, TTL. Hard problems: **invalidation** (delete the key on write instead of updating it, to avoid race conditions) and the **cache stampede** (many misses on a hot key hit the DB at once). Fix stampedes with request coalescing, locks, or early refresh with jittered TTLs.

## 3. Vertical vs horizontal scaling?

**Vertical scaling** (scale up) means a bigger machine: more CPU, RAM, faster disks. It's simple and needs no code changes, but it has a hard ceiling, gets expensive, and is still a single point of failure. **Horizontal scaling** (scale out) means adding more machines behind a load balancer. There's no hard ceiling and it tolerates failures, but it adds complexity: distributed state, coordination, network failures.

To scale out, make application servers **stateless**: move sessions and state to a shared store (Redis, DB) or into signed tokens (JWT). Then any server can handle any request, and you can add or remove servers freely (**autoscaling**). The hard part is always the **stateful layer** (databases), which is scaled with replication and sharding.

## 4. How does load balancing work?

A load balancer spreads traffic across servers, runs **health checks** so it only routes to healthy instances, and often handles TLS termination. **L4** (transport layer) balancers route by IP/port. They're fast and don't look inside packets. **L7** (application layer) balancers look at HTTP: path, headers, cookies. That enables content-based routing, sticky sessions, and retries, at a higher CPU cost.

Algorithms: **round robin**, **weighted round robin**, **least connections** (good for requests of uneven length), **IP/consistent hash** (the same client or key goes to the same server, useful for caches). Avoid making the load balancer a single point of failure: run it in active-passive pairs, or use DNS/anycast in front of several load balancers. **Sticky sessions** work, but they defeat statelessness and make load uneven.

## 5. SQL vs NoSQL — how do you choose?

**SQL** (PostgreSQL, MySQL): relational schema, **ACID transactions**, joins, strong consistency. The default choice for structured data with relationships and a need for correctness (payments, orders). Scales vertically plus read replicas. Sharding is possible, but the application or a proxy has to handle it.

**NoSQL** trades flexibility in queries for scale or a better fit to the data model: **key-value** (Redis, DynamoDB) for simple lookups; **document** (MongoDB) for flexible JSON-like records; **wide-column** (Cassandra, HBase) for heavy write loads and time series; **graph** (Neo4j) for data full of relationships. Most scale horizontally out of the box, often with eventual consistency. Choose based on **access patterns**: design NoSQL tables around your queries, not your entities.

In interviews, default to SQL unless there's a concrete reason (write volume, schema flexibility, specific access pattern) — and say what that reason is. See [database.md](database.md) for indexes, isolation, and storage engines.

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

## 8. How would you design a URL shortener?

**Requirements**: create a short link for a long URL, redirect quickly; very **read-heavy** (e.g. 100:1). Estimate: 100M new links/day ≈ 1,200 writes/s, ~120k redirects/s; 7 characters of **base62** give 62⁷ ≈ **3.5 trillion** keys. Storage: a key-value mapping `short_key → long_url` (plus owner, created, expiry) fits a KV store or a simple SQL table.

**Key generation** is the core of the discussion: **(a)** hash the URL (MD5/SHA-256), take 7 characters, and check for collisions — the same URL can return the same key; **(b)** a unique **counter/ID generator** encoded in base62 — no collisions, but keys are predictable (shuffle the bits if that matters); **(c)** a **key generation service** that pre-creates random keys and hands them out in batches.

**Reads**: cache hot keys in Redis (link popularity follows a power law), put a CDN in front. Choose **301** (permanent, browsers cache it, less load) or **302** (temporary, every click reaches you, so you can count clicks). Collect analytics **asynchronously** through a queue so redirects stay fast. Extras: custom aliases, expiration, and abuse/malware checks.

## 9. How do you design APIs? REST vs gRPC vs GraphQL?

- **REST** — resources + HTTP verbs, JSON, cacheable, available everywhere. The default for public APIs.
- **gRPC** — Protobuf over HTTP/2, strongly typed contracts, streaming, much faster. The default for internal service-to-service calls. Poor browser support.
- **GraphQL** — clients ask for exactly the fields they need in one round trip. Good for varied frontends. Harder to cache, and needs protection against expensive queries.

Common details: **cursor-based pagination** (stable and fast; offset pagination gets slow on deep pages and skips items when data changes), **versioning** (`/v1/`), **idempotency keys** for safe retries of POST, correct status codes. For real-time updates: **short polling** (simple, wasteful), **long polling**, **Server-Sent Events** (one-way server→client), **WebSockets** (two-way, stateful connections that are harder to scale).

## 10. How does rate limiting work?

Rate limiting protects services from abuse and overload. It is usually enforced at the **API gateway**, keyed by user, API key, or IP, and returns **HTTP 429** with a `Retry-After` header. Algorithms:

- **Token bucket** — tokens refill at a fixed rate, and each request uses one. Allows **bursts** up to the bucket size. The most common choice.
- **Leaky bucket** — requests drain from a queue at a constant rate. Output is smooth, with no bursts.
- **Fixed window counter** — count per time window. Simple, but allows up to 2× the limit at window boundaries.
- **Sliding window log / counter** — accurate and smooth. The counter variant blends the current and previous window's counts and is cheap.

In a distributed setup, keep counters in **Redis** (atomic `INCR` + expiry, or Lua scripts) so all servers share the same limits. A local limiter per instance is less exact but avoids a round trip to Redis on every request.

## 11. How would you design a news feed?

A user's feed shows recent posts from people they follow. The central choice is **when to build the feed**:

- **Fan-out on write (push)** — when someone posts, add the post ID to every follower's precomputed feed (a list in Redis). Reads are instant, but a celebrity with 50M followers triggers 50M writes.
- **Fan-out on read (pull)** — at read time, fetch recent posts from everyone the user follows and merge them. No write amplification, but reads are slow for users following many accounts.
- **Hybrid** (what large platforms do) — push for normal accounts, pull for celebrities, merged at read time.

Store feeds as lists of **post IDs**, not full posts, and fetch the posts themselves from a cache ("hydration"). Paginate with a **cursor**. Ranking (relevance instead of time order) is a separate scoring step. Media goes to object storage + CDN, and fan-out runs asynchronously through a queue.

## 12. What are CDNs and object storage for?

A **CDN** (CloudFront, Cloudflare, Akamai) caches content on **edge servers close to users**, cutting latency and load on your own servers. Best for static assets (images, JS, video). It can also cache API responses and absorb DDoS attacks. **Pull CDN**: the edge fetches from your server on the first miss (simple, the first request is slow). **Push CDN**: you upload content ahead of time (good for large, rarely changing files). Invalidate with **versioned file names** (`app.3f9a.js`) rather than purges.

**Object/blob storage** (S3, GCS) stores large unstructured files (uploads, videos, backups) cheaply, durably (11 nines), and with no practical size limit. Keep the files there and only **metadata and URLs in the database**. Let clients upload and download directly with **pre-signed URLs**, so large files don't pass through your app servers. For video, add **transcoding** to several bitrates plus **adaptive streaming** (HLS/DASH).

## 13. Monolith vs microservices?

A **monolith** is one deployable application. It's simple to develop, test, deploy, and debug; calls are in-process and transactions are local. It struggles when many teams work on one codebase, when one part needs to scale very differently, or when a bug in one module can take down everything.

**Microservices** split the system into independently deployable services, each owning its **own database**. Benefits: independent deploys and scaling, team autonomy, fault isolation, freedom to choose technology. Costs: network calls that can fail, **distributed transactions** (sagas), eventual consistency, harder debugging (needs tracing), and much more operational overhead.

The usual advice: **start with a modular monolith** with clear internal boundaries, and extract services when there's a concrete reason — team scaling, very different load profiles, or isolation needs. Service boundaries tend to mirror team boundaries (**Conway's law**).

## 14. How would you design a chat system?

Clients keep a persistent **WebSocket** connection to a chat server. Since connections are stateful, keep a **connection registry** (user → server, in Redis). Message flow: sender → its chat server → **persist** the message → look up the recipient's server → deliver through **pub/sub** or a queue → push over the recipient's WebSocket. If the recipient is offline, send a **push notification**; the client fetches missed messages on reconnect.

**Ordering**: don't rely on client clocks — assign a **per-conversation sequence number** on the server. **Delivery**: clients send a client-generated message ID so retries can be **deduplicated**, and acknowledgments drive the sent/delivered/read receipts. **Storage** is write-heavy and read by conversation, so a wide-column store (Cassandra, HBase) partitioned by `conversation_id` and sorted by message ID fits well.

Extras to mention: **presence** via heartbeats (online/last seen), **group chats** (fan-out to members; large groups behave like the celebrity problem in feeds), media via object storage + CDN, and **end-to-end encryption** (Signal protocol), where the server only relays ciphertext.

## 15. How do you design for high availability?

Define targets first: an **SLI** is what you measure (e.g. % of successful requests under 300 ms), an **SLO** is the internal target (99.9%), an **SLA** is the contractual promise with penalties (looser than the SLO). The gap between 100% and the SLO is the **error budget** — spend it on releases; when it's exhausted, slow down.

Techniques: **remove single points of failure** with redundancy (N+1 instances), **failover** (active-passive: a standby takes over; active-active: all serve traffic), deploy across **availability zones** and, for stricter targets, **regions**. Math: components in series multiply (99.9% × 99.9% ≈ 99.8%); redundant components in parallel fail only together (1 − 0.001² = 99.9999%).

Also define **RPO** (how much data you can lose) and **RTO** (how long recovery may take), use **graceful degradation** (serve cached or partial results when a dependency fails), deploy gradually with canaries and fast rollbacks (see [devops.md](devops.md)), and test failures deliberately (**chaos engineering**).

## 16. Reverse proxy vs API gateway vs service mesh?

A **forward proxy** sits in front of *clients* (corporate proxy, VPN-like egress). A **reverse proxy** (Nginx, HAProxy, Envoy) sits in front of *servers*: TLS termination, load balancing, caching, compression, and hiding the internal topology.

An **API gateway** is a reverse proxy with API-specific features at the edge ("north-south" traffic): **authentication**, **rate limiting**, routing to services, request aggregation, and versioning. The **Backend-for-Frontend (BFF)** pattern gives each client type (web, mobile) its own gateway. A **service mesh** (Istio, Linkerd) handles service-to-service ("east-west") traffic through **sidecar proxies** next to each service: **mTLS**, retries, timeouts, circuit breaking, and telemetry — without changing application code, at the cost of operational complexity.

## 17. How do authentication and authorization work?

**Authentication** (authN) is proving who you are; **authorization** (authZ) is deciding what you may do (**RBAC** — roles, or **ABAC** — attribute-based rules). **Sessions**: the server stores session data and gives the client a session ID in a cookie — easy to revoke, but needs a shared session store. **JWTs**: signed, self-contained tokens verified without a lookup — stateless and scalable, but **hard to revoke**, so use short expiry plus **refresh tokens**.

**OAuth 2.0** is **delegated authorization**: an app gets an access token to call an API on a user's behalf, without seeing their password. Use the **authorization code flow with PKCE** for web and mobile apps, and **client credentials** for service-to-service. **OpenID Connect (OIDC)** adds authentication on top (an ID token saying who the user is) — the basis for "Sign in with Google" and SSO.

Basics interviewers check: hash passwords with **bcrypt, scrypt, or Argon2** (never plain hashes); cookies with `HttpOnly`, `Secure`, `SameSite`; protect against CSRF and XSS; use **mTLS** or signed tokens between internal services.

## 18. How does search work? How would you design typeahead?

Full-text search uses an **inverted index**: a map from each **term** to a **posting list** of document IDs (and positions). Documents are **tokenized**, lowercased, stemmed ("running" → "run"), and stop words dropped. Results are ranked by relevance — **TF-IDF** or **BM25** (term frequency, adjusted for how rare the term is). **Elasticsearch/OpenSearch** (built on Lucene) shards and replicates the index and is near-real-time.

Keep the primary database as the **source of truth** and feed the search index asynchronously (CDC or events) — it will be slightly behind. For **typeahead**, use a **trie** (or prefix index) that stores the **top-k suggestions** at each prefix node, precomputed offline from query logs, cached aggressively, and debounced on the client. For semantic search, store **embeddings** and use approximate nearest-neighbor indexes (HNSW).

## 19. What is observability? Logs vs metrics vs traces?

- **Metrics** — numeric time series, cheap to store and aggregate (Prometheus, Grafana). Monitor the **four golden signals**: latency, traffic, errors, saturation. RED method for services (Rate, Errors, Duration), USE for resources (Utilization, Saturation, Errors).
- **Logs** — detailed event records. Make them **structured** (JSON) and centralized (ELK, Loki), and include a **correlation/request ID**.
- **Traces** — follow one request across services as a tree of **spans** with a propagated trace ID (OpenTelemetry, Jaeger). Essential for finding which service made a request slow.

Metrics tell you **something is wrong**, traces tell you **where**, logs tell you **why**. **Alert on symptoms** that users feel (error rate, latency, SLO burn rate), not on every cause (CPU at 80%), to avoid alert fatigue. OpenTelemetry is the standard for instrumenting all three.

## 20. What are Bloom filters and other probabilistic data structures?

A **Bloom filter** answers "is X in the set?" using a bit array and k hash functions, in a tiny fraction of the memory of the set itself. It can return **false positives but never false negatives** — "definitely not" or "probably yes". Used to skip expensive lookups: LSM-tree databases skip files, caches skip known misses, browsers check for malicious URLs. Standard Bloom filters can't delete items (counting Bloom filters can).

**HyperLogLog** estimates the **number of distinct items** (unique visitors) with ~1% error in a few KB of memory — Redis `PFADD`/`PFCOUNT`. **Count-Min Sketch** estimates **item frequencies** in a stream in fixed memory (heavy hitters, trending topics, top-k). All three trade exactness for huge memory savings — mention them when the interviewer asks about counting at massive scale.
