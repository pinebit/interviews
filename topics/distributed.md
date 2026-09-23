# Distributed Systems Cheatsheet

The 20 most frequently asked distributed systems interview topics, with short answers.

## 1. What is the CAP theorem?

In the presence of a **network partition (P)**, a distributed system must choose between **Consistency (C)** — every read sees the latest write — and **Availability (A)** — every request to a non-failed node gets a response. Partitions can't be avoided in practice, so the real choice is **CP** (reject or block requests during a partition, e.g. ZooKeeper, etcd) or **AP** (keep serving, possibly stale data, reconcile later, e.g. Cassandra, DynamoDB by default).

**PACELC** extends it: if Partitioned, choose A or C; **E**lse (normal operation), choose **L**atency or **C**onsistency. It captures the everyday trade-off: stronger consistency costs coordination round-trips even when nothing is broken.

## 2. What consistency models exist?

From strongest to weakest:
- **Linearizability** (strong) — operations appear to happen instantly at a single point between call and return; everyone sees one global order that respects real time.
- **Sequential** — one global order that respects each client's program order, but not real time.
- **Causal** — operations that are causally related are seen in the same order by all; concurrent ones may differ.
- **Eventual** — if writes stop, all replicas eventually converge. No ordering guarantees in the meantime.

Useful session guarantees on top of weak models: **read-your-writes**, **monotonic reads**, and **monotonic writes**. Don't confuse CAP's "C" (linearizability) with ACID's "C" (application invariants hold).

## 3. What replication strategies exist?

- **Single-leader** — all writes go to the leader, followers replicate. Simple, no write conflicts. Replication can be **synchronous** (durable, slower) or **asynchronous** (fast, may lose recent writes on failover).
- **Multi-leader** — several nodes accept writes (e.g. one per data center). Better write availability and latency, but requires **conflict resolution** (last-write-wins, CRDTs, custom merge).
- **Leaderless** (Dynamo-style) — clients write to and read from several replicas. Consistency is tuned with **quorums**: `W + R > N` guarantees read and write sets overlap. Repairs via read repair and anti-entropy.

Replication lag causes anomalies like reading stale data after your own write — mitigate by reading from the leader or tracking versions.

## 4. How do partitioning (sharding) and consistent hashing work?

**Partitioning** splits data across nodes so each holds a subset, for scaling beyond one machine. **Range partitioning** keeps keys sorted (good for range scans, risks hot spots on sequential keys). **Hash partitioning** spreads load evenly but loses ordering. **Hot keys** (a celebrity user) need extra handling, such as splitting the key.

Naive `hash(key) % N` remaps almost every key when N changes. **Consistent hashing** places nodes and keys on a ring; a key belongs to the next node clockwise, so adding or removing a node moves only about `1/N` of the keys. **Virtual nodes** (many ring positions per physical node) smooth out the load distribution.

## 5. How does consensus work (Raft / Paxos)?

Consensus gets a group of nodes to **agree on a single value (or an ordered log)** despite crashes. It needs a **majority quorum** (`N/2 + 1`), so a cluster of `2f + 1` nodes tolerates `f` failures — hence clusters of 3 or 5. Used for leader election, configuration stores, and replicated state machines (etcd, ZooKeeper, Consul).

**Raft** splits the problem into: **leader election** (nodes time out, become candidates, win a majority vote for a **term**), **log replication** (leader appends entries, commits once a majority acknowledges), and **safety** (only nodes with up-to-date logs can win). Any two majorities overlap in at least one node, so a committed entry can never be lost by a later leader.

**Paxos** solves the same problem with proposers/acceptors and is harder to understand and implement. **FLP impossibility**: no deterministic algorithm guarantees consensus in a fully asynchronous system with even one faulty node — real systems use timeouts to get around it, giving up liveness (progress) during bad periods but never safety.

## 6. What are message delivery semantics? What is idempotency?

- **At-most-once** — send without retry; messages may be lost.
- **At-least-once** — retry until acknowledged; messages may be duplicated. The common default.
- **Exactly-once** — in general impossible over an unreliable network; in practice it's **at-least-once delivery + idempotent processing** (or deduplication).

An operation is **idempotent** if applying it multiple times has the same effect as once (`SET x = 5` yes, `x += 1` no). Make retries safe with **idempotency keys** (client-generated request ID stored with the result), deduplication tables, or conditional writes with version numbers.

## 7. How do distributed transactions work (2PC vs Saga)?

**Two-phase commit (2PC)**: a coordinator asks all participants to **prepare** (vote yes/no, locking resources), then tells everyone to **commit** or **abort**. It's atomic but **blocking**: if the coordinator crashes after prepare, participants hold locks until it recovers. Also adds latency and couples services.

A **Saga** breaks the transaction into a sequence of local transactions, each with a **compensating action** to undo it on failure (e.g. "refund payment"). It gives eventual consistency, not isolation. Coordinated by **orchestration** (a central controller) or **choreography** (services react to events). Pair with the **transactional outbox** pattern to reliably publish events together with the local DB write.

## 8. How do you handle partial failures?

In a distributed system, a remote call can succeed, fail, or **time out with an unknown outcome** — you can't tell a slow node from a dead one. Core techniques:
- **Timeouts** on every remote call.
- **Retries with exponential backoff and jitter** — only for idempotent operations, to avoid duplicating side effects and **retry storms**.
- **Circuit breaker** — after repeated failures, fail fast for a while instead of hammering a struggling dependency.
- **Bulkheads** — isolate resources (thread pools, connections) per dependency so one failure doesn't take down everything.
- **Rate limiting and load shedding** — reject excess work early to protect the system.

Failure detection uses **heartbeats** or gossip protocols; detectors are always a trade-off between speed and false positives.

## 9. How do leader election and distributed locks work? What is split brain?

A **leader** or **lock holder** is chosen via a consensus-backed store (etcd, ZooKeeper) using **leases** — a lock with a TTL that must be renewed. If the holder dies, the lease expires and someone else takes over.

**Split brain** happens when two nodes both believe they're the leader (e.g. the old leader paused for a long GC and its lease expired without it knowing). Prevent damage with a **majority quorum** for election and **fencing tokens**: every lease comes with a monotonically increasing number, and the storage layer rejects writes carrying an older token. A lock on its own, without fencing, is not safe for correctness — only for efficiency.

## 10. How do you order events without a global clock?

Physical clocks drift and NTP can jump backwards, so wall-clock timestamps are **unreliable for ordering** across nodes (a problem for last-write-wins). **Lamport clocks**: each node keeps a counter, increments on every event, and on receive sets `max(local, received) + 1`. If A happened-before B then `L(A) < L(B)`, but not the reverse — they give a total order that is consistent with causality, but they can't detect concurrency.

**Vector clocks** keep one counter per node; comparing vectors tells you whether two events are causally ordered or **concurrent** (a conflict to resolve). **Hybrid logical clocks** combine physical time with a logical counter. Google Spanner's **TrueTime** exposes clock uncertainty bounds and waits them out to achieve external consistency.

## 11. Linearizability vs serializability?

**Serializability** is an **isolation** guarantee for **transactions** (groups of operations over many objects): the result equals *some* serial order of the transactions. That order doesn't have to match real time — a transaction may appear to run "before" one that actually committed earlier.

**Linearizability** is a **recency** guarantee for **single operations on a single object**: once a write completes, every later read (in real time) sees it. It's what CAP's "C" means. **Strict serializability** combines both: transactions appear in a serial order that also respects real time (Spanner, CockroachDB aim for it; FoundationDB provides it).

## 12. How do you generate unique IDs in a distributed system?

- **Database auto-increment** — simple, but a single point of failure and bottleneck. Variants: a **ticket server** (Flickr) or handing out **ID ranges** to each node.
- **UUIDv4** — 128-bit random, no coordination at all, but large and random, so inserts scatter across the B-tree index.
- **UUIDv7** (RFC 9562, 2024) — time-ordered prefix plus randomness: no coordination *and* good index locality. A good default today.
- **Snowflake** (Twitter) — 64-bit: **41 bits timestamp** (ms, ~69 years), **10 bits machine ID**, **12 bits sequence** (4096 IDs per ms per machine). Roughly time-sortable and fits in a `bigint`.

Trade-offs to discuss: size (64 vs 128 bits), sortability, coordination needed (assigning machine IDs), and **clock skew** — Snowflake generators must refuse to issue IDs if the clock moves backwards.

## 13. How are write conflicts resolved? What are CRDTs?

Conflicts happen in multi-leader and leaderless systems when two replicas accept concurrent writes to the same data. **Last-write-wins (LWW)** keeps the write with the highest timestamp — simple, but it **silently drops data** and depends on clocks. Alternatives: keep all conflicting versions (**siblings**, detected with version vectors) and let the application or user merge them, or use custom merge logic.

**CRDTs** (Conflict-free Replicated Data Types) are data structures whose merge operation is **commutative, associative, and idempotent**, so replicas that receive the same updates in any order always converge — no coordination needed. Examples: **G-Counter** (per-node counters, sum them), **PN-Counter** (increments and decrements), **OR-Set** (add/remove set), LWW-Register, and sequence CRDTs for collaborative text editing (Automerge, Yjs). Trade-off: limited operations and metadata overhead.

## 14. What are the Two Generals and Byzantine Generals problems?

**Two Generals**: two parties communicating over an unreliable channel can **never be certain they agree**, because the last message (or acknowledgment) might always be lost. It's why exactly-once delivery is impossible and why protocols settle for probabilistic certainty, retries, and idempotency.

**Byzantine Generals**: some nodes may be **malicious or arbitrarily faulty** (lying, sending conflicting messages), not just crashed. Byzantine fault tolerance needs **`3f + 1` nodes to tolerate `f` faulty ones** (vs `2f + 1` for crash faults). Classic algorithm: **PBFT**. Most internal systems assume crash faults only; BFT matters in blockchains and systems spanning untrusted parties.

## 15. How do gossip protocols and failure detection work?

In a **gossip** (epidemic) protocol, each node periodically exchanges state with a few **random peers**. Information spreads to all N nodes in **O(log N)** rounds, with no central coordinator and high tolerance to failures. Used for cluster membership, failure detection, and spreading metadata (Cassandra, Consul, DynamoDB).

Failure detectors: **heartbeats with timeouts** (simple, but a fixed timeout is either slow or trigger-happy); **phi accrual** (Cassandra, Akka) outputs a suspicion level based on the history of heartbeat arrival times; **SWIM** (used by Consul/Serf) pings a random node, and if it doesn't answer, asks k other nodes to ping it indirectly before marking it suspect. **Anti-entropy** repairs replicas in the background, comparing **Merkle trees** of their data so only differing ranges are transferred.

## 16. What are event sourcing and CQRS?

**Event sourcing** stores **every change as an immutable event** (`OrderPlaced`, `ItemAdded`) instead of the current state. The event log is the source of truth, and current state is rebuilt by **replaying events** (with periodic **snapshots** for speed). You get a full audit trail, the ability to rebuild state at any point in time, and easy creation of new views from history.

**CQRS** (Command Query Responsibility Segregation) separates the **write model** (validates commands, emits events) from one or more **read models** optimized for queries (denormalized tables, search indexes, caches), updated asynchronously from events. The two fit together naturally. Costs: read models are **eventually consistent**, **event schemas must evolve** without breaking old events, and the overall system is more complex — use it where the audit trail or read scaling justifies it.

## 17. Batch vs stream processing?

**Batch** processing runs over a large, bounded dataset (hours or days of data) — high throughput, high latency. **MapReduce**: **map** each record to key-value pairs, **shuffle** so all values for a key reach the same node, **reduce** them. **Spark** is its faster successor, keeping intermediate data in memory. Failures are handled by re-running tasks, since inputs are immutable.

**Stream** processing handles unbounded data continuously, with low latency (**Flink**, Kafka Streams, Spark Structured Streaming). Key concepts: **windows** (tumbling, sliding, session), **event time vs processing time**, and **watermarks** that decide when a window is complete despite late events. Exactly-once state is achieved with periodic **checkpoints** (distributed snapshots) plus replayable sources like Kafka. **Lambda architecture** runs batch and streaming side by side; **Kappa** uses only streaming, replaying the log to reprocess.

## 18. What is backpressure?

When a producer is faster than a consumer, work piles up. Without control, queues grow until memory runs out or latency explodes. **Backpressure** is the consumer signaling the producer to **slow down**: bounded queues that block the producer, TCP flow control, gRPC/HTTP/2 flow-control windows, or Reactive Streams' `request(n)`.

When you can't slow the producer, the options are to **buffer** (only with a bound), **drop** (load shedding, sampling), or **scale** consumers. **Little's Law** (`L = λ × W`: items in the system = arrival rate × time in system) explains why a queue grows without limit once arrival rate exceeds processing rate. Never use unbounded queues in production.

## 19. What is tail latency and why does it matter?

**Tail latency** is the latency of the slowest requests — **p99, p99.9** — as opposed to the average, which hides them. It matters because of **fan-out**: if a request calls 100 servers and each is slow 1% of the time, about **63% of requests** hit at least one slow server. At scale, the tail becomes the typical experience.

Mitigations (Google's "The Tail at Scale"): **hedged requests** (send a second copy to another replica if the first hasn't answered by roughly the p95 time, use whichever returns first), **tied requests** (send to two, cancel the loser), reducing variance (GC tuning, avoiding head-of-line blocking, isolating background work), and timeouts with partial results. Always **measure percentiles**, and beware coordinated omission in load tests.

## 20. How does service discovery work?

In dynamic environments (autoscaling, containers), service addresses change constantly, so clients need a way to find healthy instances. A **service registry** (Consul, etcd, ZooKeeper, Eureka) tracks instances, which register themselves and are removed when **health checks** or TTL heartbeats fail.

**Client-side discovery**: the client queries the registry and load-balances itself (more control, but logic in every client). **Server-side discovery**: the client calls a load balancer or DNS name that routes to healthy instances. **Kubernetes** does server-side discovery built in — a Service gets a stable DNS name and virtual IP. A **service mesh** (Istio, Linkerd) moves discovery, retries, mTLS, and telemetry into sidecar proxies, so application code stays unaware of it.
