# Distributed Systems Cheatsheet

The 10 most frequently asked distributed systems interview topics, with short answers.

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

## 3. How does consensus work (Raft / Paxos)?

Consensus gets a group of nodes to **agree on a single value (or an ordered log)** despite crashes. It needs a **majority quorum** (`N/2 + 1`), so a cluster of `2f + 1` nodes tolerates `f` failures — hence clusters of 3 or 5. Used for leader election, configuration stores, and replicated state machines (etcd, ZooKeeper, Consul).

**Raft** splits the problem into: **leader election** (nodes time out, become candidates, win a majority vote for a **term**), **log replication** (leader appends entries, commits once a majority acknowledges), and **safety** (only nodes with up-to-date logs can win). **Paxos** solves the same problem with proposers/acceptors and is harder to understand and implement. **FLP impossibility**: no deterministic algorithm guarantees consensus in a fully asynchronous system with even one faulty node — real systems use timeouts to get around it.

## 4. What replication strategies exist?

- **Single-leader** — all writes go to the leader, followers replicate. Simple, no write conflicts. Replication can be **synchronous** (durable, slower) or **asynchronous** (fast, may lose recent writes on failover).
- **Multi-leader** — several nodes accept writes (e.g. one per data center). Better write availability and latency, but requires **conflict resolution** (last-write-wins, CRDTs, custom merge).
- **Leaderless** (Dynamo-style) — clients write to and read from several replicas. Consistency is tuned with **quorums**: `W + R > N` guarantees read and write sets overlap. Repairs via read repair and anti-entropy.

Replication lag causes anomalies like reading stale data after your own write — mitigate by reading from the leader or tracking versions.

## 5. How do partitioning (sharding) and consistent hashing work?

**Partitioning** splits data across nodes so each holds a subset, for scaling beyond one machine. **Range partitioning** keeps keys sorted (good for range scans, risks hot spots on sequential keys). **Hash partitioning** spreads load evenly but loses ordering. **Hot keys** (a celebrity user) need extra handling, such as splitting the key.

Naive `hash(key) % N` remaps almost every key when N changes. **Consistent hashing** places nodes and keys on a ring; a key belongs to the next node clockwise, so adding or removing a node moves only about `1/N` of the keys. **Virtual nodes** (many ring positions per physical node) smooth out the load distribution.

## 6. How do distributed transactions work (2PC vs Saga)?

**Two-phase commit (2PC)**: a coordinator asks all participants to **prepare** (vote yes/no, locking resources), then tells everyone to **commit** or **abort**. It's atomic but **blocking**: if the coordinator crashes after prepare, participants hold locks until it recovers. Also adds latency and couples services.

A **Saga** breaks the transaction into a sequence of local transactions, each with a **compensating action** to undo it on failure (e.g. "refund payment"). It gives eventual consistency, not isolation. Coordinated by **orchestration** (a central controller) or **choreography** (services react to events). Pair with the **transactional outbox** pattern to reliably publish events together with the local DB write.

## 7. What are message delivery semantics? What is idempotency?

- **At-most-once** — send without retry; messages may be lost.
- **At-least-once** — retry until acknowledged; messages may be duplicated. The common default.
- **Exactly-once** — in general impossible over an unreliable network; in practice it's **at-least-once delivery + idempotent processing** (or deduplication).

An operation is **idempotent** if applying it multiple times has the same effect as once (`SET x = 5` yes, `x += 1` no). Make retries safe with **idempotency keys** (client-generated request ID stored with the result), deduplication tables, or conditional writes with version numbers.

## 8. How do you order events without a global clock?

Physical clocks drift and NTP can jump backwards, so wall-clock timestamps are **unreliable for ordering** across nodes (a problem for last-write-wins). **Lamport clocks**: each node keeps a counter, increments on every event, and on receive sets `max(local, received) + 1`. If A happened-before B then `L(A) < L(B)`, but not the reverse — they give a total order that is consistent with causality, but they can't detect concurrency.

**Vector clocks** keep one counter per node; comparing vectors tells you whether two events are causally ordered or **concurrent** (a conflict to resolve). **Hybrid logical clocks** combine physical time with a logical counter. Google Spanner's **TrueTime** exposes clock uncertainty bounds and waits them out to achieve external consistency.

## 9. How do you handle partial failures?

In a distributed system, a remote call can succeed, fail, or **time out with an unknown outcome** — you can't tell a slow node from a dead one. Core techniques:
- **Timeouts** on every remote call.
- **Retries with exponential backoff and jitter** — only for idempotent operations, to avoid duplicating side effects and **retry storms**.
- **Circuit breaker** — after repeated failures, fail fast for a while instead of hammering a struggling dependency.
- **Bulkheads** — isolate resources (thread pools, connections) per dependency so one failure doesn't take down everything.
- **Rate limiting and load shedding** — reject excess work early to protect the system.

Failure detection uses **heartbeats** or gossip protocols; detectors are always a trade-off between speed and false positives.

## 10. How do leader election and distributed locks work? What is split brain?

A **leader** or **lock holder** is chosen via a consensus-backed store (etcd, ZooKeeper) using **leases** — a lock with a TTL that must be renewed. If the holder dies, the lease expires and someone else takes over.

**Split brain** happens when two nodes both believe they're the leader (e.g. the old leader paused for a long GC and its lease expired without it knowing). Prevent damage with a **majority quorum** for election and **fencing tokens**: every lease comes with a monotonically increasing number, and the storage layer rejects writes carrying an older token. A lock on its own, without fencing, is not safe for correctness — only for efficiency.
