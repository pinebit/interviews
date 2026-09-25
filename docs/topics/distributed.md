# Distributed Systems

Key distributed-systems building blocks and trade-offs, grouped by subtopic.

## Theory and impossibility results

### CAP theorem

- During a **network partition (P)**, choose **Consistency** (reject/block, e.g. etcd, ZooKeeper) or **Availability** (keep serving, possibly stale, e.g. Cassandra, DynamoDB default).
- "C" here means **linearizability** — don't confuse it with ACID's "C" (application invariants).
- **PACELC** extends it: if Partitioned, trade Availability vs Consistency; **E**lse (normal operation), trade **L**atency vs **C**onsistency — the everyday cost even when nothing is broken.

### Impossibility results

- **FLP**: no deterministic algorithm guarantees consensus in a fully asynchronous system with even one faulty node. Real systems use timeouts, trading liveness (progress) for safety during bad periods, never the reverse.
- **Two Generals**: two parties over an unreliable channel can never be certain they agree, since the last ack can always be lost — why exactly-once delivery is impossible.
- **Byzantine fault tolerance**: nodes that lie or send conflicting messages need **`3f + 1`** nodes to tolerate `f` faulty ones (vs `2f + 1` for crash faults); classic algorithm is **PBFT**. Most internal systems assume crash faults only.

## Consistency models

### Consistency hierarchy

Roughly strongest to weakest, though they apply to different scopes: **strict serializable**/**linearizable** (single-object/transaction recency) > **sequential** > **causal** > **eventual** (multi-replica ordering).

- **Linearizability** — a recency guarantee for a single object: once a write completes, every later real-time read sees it.
- **Serializability** — an isolation guarantee for transactions (potentially many objects): the result equals *some* serial order, not necessarily matching real time.
- **Strict serializability** combines both: transactions appear in a serial order that also respects real time (Spanner, CockroachDB aim for it; FoundationDB provides it) — it's what you get when linearizability is applied at the transaction level instead of the single-object level.
- **Sequential/causal/eventual** describe how far apart replicas' views of the world can drift, not transaction isolation — session guarantees on top of them: **read-your-writes**, **monotonic reads**, **monotonic writes**, **writes-follow-reads**.

## Replication

### Replication strategies

- **Single-leader** — all writes to one leader; **sync** replication is durable but slower, **async** is fast but can lose recent writes on failover; **semi-sync** waits for at least one replica.
- **Multi-leader** — several nodes accept writes (e.g. per data center); needs conflict resolution.
- **Leaderless** (Dynamo-style) — clients write/read several replicas; tuned with quorums.

### Quorums and repair

- **`W + R > N`** guarantees read and write sets overlap.
- **Sloppy quorum + hinted handoff**: accept writes on non-owner nodes during an outage, hand them off later.
- **Read repair** fixes stale replicas during a read; **anti-entropy** compares **Merkle trees** in the background so only differing ranges transfer.
- Replication lag causes anomalies like reading stale data right after your own write.

## Partitioning

### Sharding strategies

- **Hash partitioning** spreads load evenly, loses range-scan ordering; **range partitioning** keeps keys sorted, risks hot spots on sequential keys.
- **Consistent hashing** places nodes and keys on a ring; a key belongs to the next node clockwise, so adding/removing a node moves only about `1/N` of keys. **Virtual nodes** (many ring positions per node) smooth load.
- **Rendezvous hashing** (highest random weight) picks the owner by hashing `(node, key)` pairs — no ring, simpler rebalancing math.
- **Hot keys** need salting (splitting a key into sub-keys) since no amount of replication fixes a single overloaded key.
- Secondary indexes are either **local** (each partition indexes its own data, scatter-gather reads) or **global** (indexed across partitions, needs its own partitioning and gets async, eventually-consistent updates).

## Consensus and coordination

### Consensus algorithms

- Needs a **majority quorum** (`⌊N/2⌋ + 1`): a cluster of `2f + 1` nodes tolerates `f` crash failures — hence clusters of 3 or 5.
- **Raft**: **leader election** (randomized election timeouts avoid split votes; nodes vote once per **term**), **log replication** (leader commits once a majority acks), **safety** (election restriction — a candidate must have an up-to-date log to win; any two majorities overlap, so a committed entry can't be lost).
- **Paxos** solves the same problem in two phases (prepare/promise, accept/accepted) via proposers/acceptors; harder to reason about and implement than Raft.

### Locks and leases

- A **lease** is a lock with a TTL that must be renewed; if the holder dies, it expires and another node takes over.
- **Split brain**: two nodes both believe they're leader (e.g. the old leader paused for a long GC past its lease expiry). Prevent damage with **fencing tokens** — a monotonically increasing number per lease that storage rejects if it goes backward. A lock alone, without fencing, is safety only against contention, not correctness.
- The **Redlock** algorithm (Redis-based distributed locking) is criticized for depending on wall-clock assumptions; prefer a consensus-backed store (etcd, ZooKeeper) when correctness matters.

## Time, ordering, and IDs

### Clocks

- Physical clocks drift and NTP can jump backward, so wall-clock timestamps are unreliable for cross-node ordering (breaks last-write-wins).
- **Lamport clocks**: each node increments a counter per event, and on receive sets `max(local, received) + 1`. Gives a total order consistent with causality but can't detect concurrency.
- **Vector clocks** keep one counter per node; comparing vectors detects whether two events are causally ordered or **concurrent**.
- **Hybrid logical clocks (HLC)** combine physical time with a logical counter for a causally-consistent, roughly time-ordered value.
- Spanner's **TrueTime** exposes clock uncertainty bounds and commit-waits out the uncertainty interval to get external consistency.

### Distributed IDs

- **Snowflake**: 64 bits = **41-bit timestamp** (ms) + **10-bit machine ID** + **12-bit sequence** (4096 IDs/ms/machine); roughly time-sortable, fits a `bigint`.
- **UUIDv7**: time-ordered prefix plus randomness — no coordination needed and good B-tree index locality, unlike random UUIDv4.
- **ULID**: similar time-ordered + random design, encoded as a sortable 26-char string.

## Transactions across services

### 2PC, 3PC, sagas

- **2PC**: coordinator asks all participants to **prepare** (vote, lock resources), then **commit**/**abort**. Atomic but **blocking** — if the coordinator dies after prepare, participants hold locks until it recovers.
- **3PC** adds a pre-commit phase to avoid indefinite blocking on coordinator failure, but still fails under network partitions and is rarely used in practice.
- **Sagas** break a transaction into local steps, each with a **compensating action** to undo it. Give eventual consistency, not isolation. **Orchestration** (central controller) vs **choreography** (services react to events).
- **Exactly-once = at-least-once delivery + idempotent processing** — pair with the **transactional outbox** pattern (see [backend.md](backend.md)) to publish events atomically with a local write.

## Conflict resolution

### Strategies and CRDTs

- **Last-write-wins (LWW)** — simplest, but silently drops data and depends on clock accuracy.
- **Version vectors** detect concurrent writes (**siblings**) and surface them for app/user merge instead of silently discarding one.
- **CRDTs** (Conflict-free Replicated Data Types) merge **commutatively, associatively, and idempotently**, so replicas converge with no coordination: **G-Counter** (sum per-node counters), **PN-Counter** (inc/dec), **OR-Set** (add/remove set), **LWW-Register**.
- **OT** (Operational Transformation) vs **CRDT** for collaborative editing: OT transforms concurrent ops against a central server/order; CRDTs merge peer-to-peer without one, at the cost of larger metadata (Automerge, Yjs use CRDTs).

## Failure handling

### Resilience techniques

- **Timeouts** on every remote call; **retries with exponential backoff + jitter**, only for idempotent operations, to avoid retry storms.
- **Retry budgets** cap the fraction of traffic that may be retries, preventing a retry storm from amplifying an outage.
- **Circuit breaker** states: closed (normal) → open (fail fast after threshold) → half-open (probe, then close or re-open).
- **Bulkheads** isolate resources (thread pools, connections) per dependency; **backpressure** and **load shedding** reject excess work before it queues unboundedly.
- **Hedged requests**: send a second copy to another replica if the first hasn't answered by roughly the p95 time, use whichever returns first.

### Tail latency and failure detection

- **Fan-out amplification**: if a request calls `n` servers each slow `p`% of the time, roughly `1 − (1 − p)ⁿ` of requests hit at least one slow server — at scale the tail becomes typical.
- Failure detectors: **heartbeats with fixed timeouts** (simple, but a bad trade between speed and false positives); **phi-accrual** (Cassandra, Akka) outputs a continuous suspicion level from heartbeat history instead of a hard cutoff; **SWIM** (Consul/Serf) pings a random node and, on timeout, asks k peers to ping it indirectly before marking it suspect.

## Stream processing

### Event time and windows

- **Event time** (when it happened) vs **processing time** (when the system saw it) — late or out-of-order events break naive processing-time windows.
- **Watermarks** declare "no more events before time T are expected," deciding when a window can close despite lateness.
- Window types: **tumbling** (fixed, non-overlapping), **sliding** (fixed, overlapping), **session** (gap-based, variable length).

### Kafka and event architectures

- Ordering is guaranteed **only within a partition**; **consumer groups** split partitions across consumer instances for parallelism.
- **Idempotent producer** (`enable.idempotence`) dedupes retried sends per partition; **transactions** extend that to atomic multi-partition writes.
- **Event sourcing** stores every change as an immutable event and rebuilds state by replay (with snapshots for speed); **CQRS** separates the write model from one or more read models updated asynchronously — the read side is eventually consistent, and event schemas must evolve without breaking old events.
