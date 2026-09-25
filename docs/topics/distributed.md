# Distributed Systems

Key distributed-systems building blocks and trade-offs, grouped by subtopic.

## Theory and impossibility results

### CAP and PACELC

- During a **network partition**, choose Consistency (reject or block — etcd, ZooKeeper) or Availability (serve possibly stale data — Cassandra, DynamoDB default).
- CAP's "C" is linearizability, not ACID's "C" (application invariants).
- **PACELC**: if Partitioned, A vs C; Else, **Latency vs Consistency** — the everyday cost when nothing is broken.

### FLP and Two Generals

- **FLP**: no deterministic algorithm guarantees consensus in a fully asynchronous system with even one crash. Real systems use timeouts and give up liveness, never safety, in bad periods.
- **Two Generals**: over a lossy channel the last ack can always be lost, so two parties can never be sure they agree — why exactly-once *delivery* is impossible.

### Byzantine faults

- Tolerating `f` nodes that lie needs **`3f + 1`** nodes, vs `2f + 1` for crash faults; the classic algorithm is **PBFT**.
- Most internal systems assume crash faults only; blockchains must assume Byzantine ones.

## Consistency models

### Consistency hierarchy

- From strongest: strict serializable > linearizable > sequential > causal > eventual.
- **Linearizability**: single-object recency — once a write completes, every later read (in real time) sees it.
- **Serializability**: multi-object transaction isolation — equivalent to *some* serial order, not necessarily real-time order.
- **Strict serializability** adds real-time order (Spanner, FoundationDB); CockroachDB is serializable but linearizable only per key.

### Session guarantees

- **Read-your-writes**, **monotonic reads**, **monotonic writes**, writes-follow-reads — per-client guarantees layered on eventual consistency.
- Typical implementations: sticky routing to one replica, or reading from a replica that has caught up to the client's last-seen version.

## Replication

### Single-leader replication

- All writes go to one leader; **sync** followers are durable but add latency, **async** followers are fast but lose recent writes on failover.
- Semi-sync waits for at least one follower.
- **Replication lag** breaks read-your-writes: a user can't see their own update right after writing.

### Multi-leader and leaderless

- **Multi-leader**: several nodes accept writes (one per region) — needs conflict resolution.
- **Leaderless** (Dynamo-style): the client writes to and reads from several replicas, tuned with quorums.

### Quorums

- **`W + R > N`** makes read and write sets overlap, e.g. N=3, W=2, R=2.
- **Sloppy quorum + hinted handoff**: during an outage, accept writes on stand-in nodes and hand them back later — overlap is no longer guaranteed.

### Replica repair

- **Read repair** fixes stale replicas seen during a read.
- **Anti-entropy** compares **Merkle trees** in the background so only differing key ranges transfer.

## Partitioning

### Hash vs range partitioning

- **Hash** spreads load evenly but loses range scans; **range** keeps keys sorted but sequential keys (timestamps) create hot spots.
- Compound keys combine both: hash the first component to pick a partition, keep rows sorted by the rest (Cassandra partition + clustering key).

### Consistent and rendezvous hashing

- **Consistent hashing**: nodes and keys on a ring; a key belongs to the next node clockwise, so adding a node moves ~**`1/N`** of keys. **Virtual nodes** smooth the load.
- Rendezvous hashing: owner = node with the highest `hash(node, key)` — no ring, same minimal movement.

### Hot keys and secondary indexes

- A single hot key isn't fixed by more partitions — **salt** it into sub-keys and merge on read.
- **Local** secondary indexes (per partition) need scatter-gather reads; **global** ones are partitioned separately and updated asynchronously.

## Consensus and coordination

### Quorum sizing

- Consensus needs a **majority** (`⌊N/2⌋ + 1`): `2f + 1` nodes tolerate `f` crashes — hence 3 or 5 nodes.
- An even size adds no tolerance: 4 nodes still tolerate only 1 failure.

### Raft

- **Leader election**: randomized timeouts avoid split votes; one vote per node per term.
- Log replication: an entry commits once a **majority** stores it.
- **Election restriction**: only a candidate with an up-to-date log can win, so committed entries survive.

### Raft reads and membership

- A leader can't just read locally — a deposed leader may not know it yet. **ReadIndex** confirms leadership with a heartbeat round; **lease reads** skip it but rely on bounded clock drift.
- Membership changes go one server at a time (or via joint consensus); **snapshots** truncate the log.

### Paxos

- Two phases across proposers and acceptors: **prepare/promise**, then **accept/accepted**.
- Same safety as Raft but harder to implement; **Multi-Paxos** adds a stable leader to skip the first phase.

### Leases and fencing tokens

- A lease is a lock with a TTL; if the holder dies, it expires and someone else takes over.
- A holder paused past expiry (long GC) still thinks it's the leader — **split brain**. **Fencing tokens** (increasing per lease, checked by the storage) reject its stale writes.
- **Redlock** depends on timing assumptions; use a consensus store (etcd, ZooKeeper) when correctness matters.

## Time, ordering, and IDs

### Physical clocks and TrueTime

- Clocks drift and NTP can step them backward, so wall-clock timestamps can't order events across nodes — **last-write-wins** silently loses data.
- Spanner's **TrueTime** returns an uncertainty interval; a commit **waits out** the uncertainty (~ms) before becoming visible, giving external consistency.

### Logical clocks

- **Lamport clock**: increment per event; on receive, `max(local, received) + 1`. A total order consistent with causality, but can't detect concurrency.
- **Vector clock**: one counter per node; comparing two vectors tells **happened-before** from concurrent.
- Hybrid logical clock (HLC): physical time + logical counter — causal and close to wall time (CockroachDB).

### Distributed IDs

| Scheme | Layout | Note |
|---|---|---|
| **Snowflake** | 41-bit ms timestamp + 10-bit machine + 12-bit sequence | 4,096 IDs/ms/machine, fits `bigint` |
| **UUIDv7** | 48-bit ms timestamp + random | time-ordered, good B-tree locality |
| **ULID** | timestamp + random, 26-char string | sortable text form |
| UUIDv4 | 122 random bits | scatters index inserts |

## Transactions across services

### Two-phase commit

- Coordinator asks participants to prepare (vote and hold locks), then commit or abort.
- Atomic but **blocking**: if the coordinator dies after prepare, participants hold locks until it returns. **3PC** avoids that only without partitions, so it's rarely used.

### Sagas

- A chain of local transactions, each with a **compensating action**; eventual consistency, **no isolation** (others see intermediate states).
- **Orchestration** (a central coordinator) vs choreography (services react to each other's events).

### Effectively-once processing

- **Exactly-once = at-least-once delivery + idempotent processing**.
- Publish events atomically with the local write via the **transactional outbox**; dedupe on the consumer via an inbox — both in [backend.md](backend.md).

## Conflict resolution

### Last-write-wins and siblings

- **LWW** is simplest but silently drops concurrent writes and depends on clocks.
- **Version vectors** detect concurrent writes and keep **siblings** for the app or user to merge.

### CRDTs

- Merges are **commutative, associative, idempotent**, so replicas converge without coordination.
- **G-Counter** (per-node counts, summed), PN-Counter (two G-Counters), **OR-Set** (add wins over concurrent remove), LWW-Register.

### OT vs CRDT for collaborative editing

- **OT** transforms concurrent operations against each other, usually via a central server (Google Docs).
- **CRDTs** merge peer-to-peer with larger metadata (Automerge, Yjs).

## Failure handling

### Timeouts and retries

- Put a timeout on every remote call.
- Retry only **idempotent** operations, with **exponential backoff + jitter** so retries don't synchronize.
- A **retry budget** (e.g. retries ≤ 10% of requests) stops retries from multiplying load during an outage.

### Circuit breakers

- **Closed** (normal) → **open** after an error threshold (fail fast) → **half-open** (let a probe through, then close or reopen).
- Keep one breaker per dependency and pair it with a fallback (cached or default response).

### Bulkheads, backpressure, load shedding

- **Bulkheads** give each dependency its own pool (threads, connections), so one slow dependency can't exhaust everything.
- **Backpressure** slows producers; **load shedding** rejects excess work early rather than queueing it without bound.

### Tail latency and hedging

- With fan-out to `n` servers each slow with probability `p`, a request is slow with probability **`1 − (1 − p)ⁿ`** — at 100 servers, a 1% tail hits 63% of requests.
- **Hedged requests**: send a second copy after ~p95 latency and take the first reply.

### Failure detection

- **Fixed-timeout heartbeats** trade detection speed against false positives.
- **Phi-accrual** (Cassandra, Akka) outputs a suspicion level from heartbeat history.
- **SWIM** (Consul, Serf) pings a random member, then asks `k` peers to probe it indirectly before suspecting it.

## Stream processing

### Event time and watermarks

- **Event time** (when it happened) vs **processing time** (when it arrived) — late events break processing-time windows.
- A **watermark** says "no events older than T are expected", letting a window close; later stragglers go to a side output or update results.

### Window types

- **Tumbling** (fixed, non-overlapping), **sliding/hopping** (fixed, overlapping), **session** (closed by an inactivity gap).

### Kafka ordering and consumer groups

- Order is guaranteed **only within a partition**; key by entity ID to keep one entity's events in order.
- A **consumer group** splits partitions among its members — parallelism is capped at the **partition count**.

### Kafka producer semantics

- **Idempotent producer** (default since Kafka 3.0) dedupes retried sends per partition.
- **Transactions** make writes across partitions and the consumer offset commit atomic — exactly-once for read-process-write within Kafka.

### Kafka durability

- Each partition has a leader and followers; the **ISR** (in-sync replicas) are followers caught up within `replica.lag.time.max.ms`.
- **`acks=all`** + **`min.insync.replicas=2`** (with replication factor 3) acknowledges a write only once 2 replicas have it — survives one broker loss without losing acknowledged data.
- `unclean.leader.election.enable=false` (default) refuses to elect an out-of-sync replica, choosing unavailability over data loss.

### Kafka rebalancing, compaction, KRaft

- A rebalance reassigns partitions when consumers join or leave; the **KIP-848** consumer protocol (GA in Kafka 4.0) makes it incremental and broker-driven instead of stop-the-world.
- **Log compaction** keeps only the latest record per key (a delete = `null` tombstone) — for changelogs and state restoration.
- **Kafka 4.0 (March 2025) removed ZooKeeper**: metadata lives in a Raft quorum of controllers (KRaft).

### Event sourcing and CQRS

- **Event sourcing** stores every change as an immutable event and rebuilds state by replay, with snapshots for speed.
- **CQRS** splits the write model from read models updated asynchronously — reads are eventually consistent.
- Event schemas must stay readable forever: only add fields, or upcast old events.
