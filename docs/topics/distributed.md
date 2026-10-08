# Distributed Systems

Key distributed-systems building blocks and trade-offs, grouped by subtopic.

## Theory and impossibility results

### CAP and PACELC

- During a [network partition](https://en.wikipedia.org/wiki/Network_partition), choose Consistency (reject or block — [etcd](https://etcd.io/docs/), [ZooKeeper](https://zookeeper.apache.org/)) or Availability (serve possibly stale data — [Cassandra](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html#tunable-consistency), [DynamoDB default](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)).
- [CAP](https://en.wikipedia.org/wiki/CAP_theorem)'s "C" is [linearizability](https://jepsen.io/consistency/models/linearizable), not [ACID's "C"](https://en.wikipedia.org/wiki/ACID#Consistency) (application invariants).
- [PACELC](https://en.wikipedia.org/wiki/PACELC_design_principle): if Partitioned, A vs C; Else, Latency vs Consistency — the everyday cost when nothing is broken.

### FLP and Two Generals

- [FLP](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf): no deterministic algorithm guarantees consensus in a fully asynchronous system with even one crash. Real systems use timeouts and give up [liveness, never safety](https://en.wikipedia.org/wiki/Safety_and_liveness_properties), in bad periods.
- [Two Generals](https://en.wikipedia.org/wiki/Two_Generals%27_Problem): over a lossy channel the last ack can always be lost, so two parties can never be sure they agree — why exactly-once *delivery* is impossible.

### Byzantine faults

- Under [partial synchrony](https://groups.csail.mit.edu/tds/papers/Lynch/jacm88.pdf), tolerating `f` [nodes that lie](https://en.wikipedia.org/wiki/Byzantine_fault) needs `3f + 1` nodes, vs `2f + 1` for crash faults; the classic algorithm is [PBFT](https://www.usenix.org/conference/osdi-99/practical-byzantine-fault-tolerance).
- The bound depends on the model: with [signed messages](https://lamport.azurewebsites.net/pubs/byz.pdf) and a synchronous network, fewer nodes suffice.
- Most internal systems assume crash faults only; blockchains must assume Byzantine ones.

## Consistency models

### Consistency hierarchy

- [Single-object models](https://jepsen.io/consistency), strongest first: [linearizable](https://jepsen.io/consistency/models/linearizable) > [sequential](https://jepsen.io/consistency/models/sequential) > [causal](https://jepsen.io/consistency/models/causal); [eventual](https://en.wikipedia.org/wiki/Eventual_consistency) only promises convergence, which causal alone doesn't guarantee.
- Linearizability: single-object recency — once a write completes, every later read (in real time) sees it or a newer value.
- [Serializability](https://jepsen.io/consistency/models/serializable): multi-object transaction isolation — equivalent to *some* serial order, not necessarily real-time order.
- [Strict serializability](https://jepsen.io/consistency/models/strict-serializable) adds real-time order ([Spanner](https://cloud.google.com/spanner/docs/true-time-external-consistency), [FoundationDB](https://apple.github.io/foundationdb/consistency.html)); [CockroachDB](https://www.cockroachlabs.com/blog/consistency-model/) is serializable but linearizable only per key.

### Session guarantees

- [Read-your-writes](https://jepsen.io/consistency/models/read-your-writes), [monotonic reads](https://jepsen.io/consistency/models/monotonic-reads), [monotonic writes](https://jepsen.io/consistency/models/monotonic-writes), [writes-follow-reads](https://jepsen.io/consistency/models/writes-follow-reads) — per-client guarantees layered on eventual consistency.
- Typical implementations: sticky routing to one replica, or reading from a replica that has caught up to the client's last-seen version.

## Replication

### Single-leader replication

- All writes go to one leader; [sync](https://www.postgresql.org/docs/current/warm-standby.html#SYNCHRONOUS-REPLICATION) followers are durable but add latency, async followers are fast but lose recent writes on failover.
- [Semi-sync](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html) waits for at least one follower.
- Replication lag breaks read-your-writes: a user can't see their own update right after writing.

### Multi-leader and leaderless

- [Multi-leader](https://en.wikipedia.org/wiki/Multi-master_replication): several nodes accept writes (one per region) — needs conflict resolution.
- Leaderless ([Dynamo-style](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)): the client writes to and reads from several replicas, tuned with quorums.

### Quorums

- [`W + R > N`](https://en.wikipedia.org/wiki/Quorum_%28distributed_computing%29) makes read and write sets overlap, e.g. N=3, W=2, R=2.
- [Sloppy quorum + hinted handoff](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf): during an outage, accept writes on stand-in nodes and hand them back later — overlap is no longer guaranteed.

### Replica repair

- [Read repair](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/read_repair.html) fixes stale replicas seen during a read.
- [Anti-entropy](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/repair.html) compares [Merkle trees](https://en.wikipedia.org/wiki/Merkle_tree) in the background so only differing key ranges transfer.

## Partitioning

### Hash vs range partitioning

- Hash spreads load evenly but loses range scans; range keeps keys sorted but sequential keys (timestamps) create [hot spots](https://en.wikipedia.org/wiki/Partition_%28database%29).
- Compound keys combine both: hash the first component to pick a partition, keep rows sorted by the rest ([Cassandra partition + clustering key](https://cassandra.apache.org/doc/latest/cassandra/developing/cql/ddl.html#primary-key)).

### Consistent and rendezvous hashing

- [Consistent hashing](https://en.wikipedia.org/wiki/Consistent_hashing): nodes and keys on a ring; a key belongs to the next node clockwise, so adding a node moves ~`1/N` of keys. [Virtual nodes](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html) smooth the load.
- [Rendezvous hashing](https://en.wikipedia.org/wiki/Rendezvous_hashing): owner = node with the highest `hash(node, key)` — no ring, same minimal movement.

### Hot keys and secondary indexes

- A single hot key isn't fixed by more partitions — [salt](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html) it into sub-keys and merge on read.
- Local [secondary indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SecondaryIndexes.html) (per partition) need scatter-gather unless the query fixes the partition key; global ones are partitioned by the indexed value, so a write touches several partitions — asynchronous in DynamoDB, transactional in [Spanner](https://cloud.google.com/spanner/docs/secondary-indexes).

## Consensus and coordination

### Quorum sizing

- [Consensus](https://en.wikipedia.org/wiki/Consensus_%28computer_science%29) needs a majority (`⌊N/2⌋ + 1`): `2f + 1` nodes tolerate `f` crashes — hence 3 or 5 nodes.
- An even size adds no tolerance: 4 nodes still tolerate only 1 failure.

### Raft

- [Leader election](https://raft.github.io/raft.pdf): randomized timeouts avoid split votes; one vote per node per term.
- Log replication: a leader commits an entry once a majority stores it — only for current-term entries; older ones commit indirectly with them.
- Election restriction: only a candidate with an up-to-date log can win, so committed entries survive.

### Raft reads and membership

- A leader can't just read locally — a deposed leader may not know it yet. [ReadIndex](https://web.stanford.edu/~ouster/cgi-bin/papers/OngaroPhD.pdf) confirms leadership with a heartbeat round; lease reads skip it but rely on bounded clock drift.
- Membership changes go one server at a time (or via [joint consensus](https://raft.github.io/raft.pdf)); snapshots truncate the log.

### Paxos

- [Two phases](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf) across proposers and acceptors: prepare/promise, then accept/accepted.
- Same safety as Raft but harder to implement; [Multi-Paxos](https://en.wikipedia.org/wiki/Paxos_%28computer_science%29#Multi-Paxos) adds a stable leader to skip the first phase.

### Leases and fencing tokens

- A [lease](https://en.wikipedia.org/wiki/Lease_%28computer_science%29) is a lock with a TTL; if the holder dies, it expires and someone else takes over.
- A holder paused past expiry (long GC) still thinks it's the leader — [split brain](https://en.wikipedia.org/wiki/Split-brain_%28computing%29). [Fencing tokens](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) (increasing per lease, checked by the storage) reject its stale writes.
- [Redlock](https://redis.io/docs/latest/develop/use/patterns/distributed-locks/) depends on timing assumptions; use a consensus store ([etcd](https://etcd.io/docs/), [ZooKeeper](https://zookeeper.apache.org/)) when correctness matters.

## Time, ordering, and IDs

### Physical clocks and TrueTime

- Clocks drift and [NTP](https://en.wikipedia.org/wiki/Network_Time_Protocol) can step them backward, so wall-clock timestamps can't order events across nodes — last-write-wins silently loses data.
- Spanner's [TrueTime](https://cloud.google.com/spanner/docs/true-time-external-consistency) returns an uncertainty interval; a commit waits out the uncertainty (~ms) before becoming visible, giving external consistency.
- Measure durations, timeouts, and leases with the monotonic clock ([`CLOCK_MONOTONIC`](https://man7.org/linux/man-pages/man2/clock_gettime.2.html), Go's [`time.Since`](https://pkg.go.dev/time#hdr-Monotonic_Clocks), [`performance.now()`](https://developer.mozilla.org/en-US/docs/Web/API/Performance/now)), which never jumps; wall-clock time steps on NTP corrections, manual changes, and VM migration.

### Logical clocks

- [Lamport clock](https://en.wikipedia.org/wiki/Lamport_timestamp): increment per event; on receive, `max(local, received) + 1`. With node ID as tie-breaker, a total order consistent with causality, but can't detect concurrency.
- [Vector clock](https://en.wikipedia.org/wiki/Vector_clock): one counter per node; comparing two vectors tells [happened-before](https://en.wikipedia.org/wiki/Happened-before) from concurrent.
- [Hybrid logical clock](https://cse.buffalo.edu/tech-reports/2014-04.pdf) (HLC): physical time + logical counter — causal and close to wall time ([CockroachDB](https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer)).

### Distributed IDs

| Scheme | Layout | Note |
|---|---|---|
| [Snowflake](https://en.wikipedia.org/wiki/Snowflake_ID) | 41-bit ms timestamp + 10-bit machine + 12-bit sequence | 4,096 IDs/ms/machine, fits `bigint` |
| [UUIDv7](https://www.rfc-editor.org/rfc/rfc9562#name-uuid-version-7) | 48-bit ms timestamp + random | time-ordered, good B-tree locality |
| [ULID](https://github.com/ulid/spec) | timestamp + random, 26-char string | sortable text form |
| [UUIDv4](https://www.rfc-editor.org/rfc/rfc9562#name-uuid-version-4) | 122 random bits | scatters index inserts |

## Transactions across services

### Two-phase commit

- [Coordinator](https://en.wikipedia.org/wiki/Two-phase_commit_protocol) asks participants to prepare (vote and hold locks), then commit or abort.
- Atomic but blocking: if the coordinator dies after prepare, participants hold locks until it returns. [3PC](https://en.wikipedia.org/wiki/Three-phase_commit_protocol) avoids that only without partitions, so it's rarely used.

### Sagas

- A [chain of local transactions](https://microservices.io/patterns/data/saga.html), each with a [compensating action](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction); eventual consistency, no isolation (others see intermediate states).
- Orchestration (a central coordinator) vs choreography (services react to each other's events).

### Delivery guarantees

- [At-most-once](https://kafka.apache.org/43/design/design/#message-delivery-semantics): ack (or commit the offset) before processing — a crash mid-processing loses the message.
- At-least-once: ack after processing — a crash between the effect and the ack redelivers it, so handlers see duplicates.
- Exactly-once *delivery* is impossible; an exactly-once effect = at-least-once + [idempotent](https://en.wikipedia.org/wiki/Idempotence#Computer_science_meaning) handling, or one transaction covering both the effect and the offset.
- Publish events atomically with the local write via the transactional outbox; dedupe on the consumer via an inbox — both in [backend.md](backend.md).

## Conflict resolution

### Last-write-wins and siblings

- LWW is simplest but silently drops concurrent writes and depends on clocks.
- [Version vectors](https://en.wikipedia.org/wiki/Version_vector) detect concurrent writes and keep [siblings](https://docs.riak.com/riak/kv/latest/learn/concepts/causal-context/index.html#siblings) for the app or user to merge.

### CRDTs

- [State-based](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#State-based_CRDTs): merges are commutative, associative, idempotent, so replicas converge without coordination.
- [Op-based](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#Operation-based_CRDTs): replicas broadcast operations that must commute; delivery must be exactly-once and usually causal.
- [G-Counter](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#G-Counter_%28Grow-only_Counter%29) (per-node counts, summed), PN-Counter (two G-Counters), OR-Set (add wins over concurrent remove), LWW-Register.

### OT vs CRDT for collaborative editing

- [OT](https://en.wikipedia.org/wiki/Operational_transformation) transforms concurrent operations against each other, usually via a central server (Google Docs).
- [CRDTs](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type) merge peer-to-peer with larger metadata ([Automerge](https://automerge.org/), [Yjs](https://docs.yjs.dev/)).

## Failure handling

### Timeouts and retries

- Put a timeout on every remote call.
- Retry only idempotent operations, with [exponential backoff + jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) so retries don't synchronize.
- A [retry budget](https://sre.google/sre-book/handling-overload/) (e.g. retries ≤ 10% of requests) stops retries from multiplying load during an outage.

### Circuit breakers

- [Closed](https://martinfowler.com/bliki/CircuitBreaker.html) (normal) → open after an error threshold (fail fast) → half-open (let a probe through, then close or reopen).
- Keep one breaker per dependency and pair it with a fallback (cached or default response).

### Bulkheads, backpressure, load shedding

- [Bulkheads](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead) give each dependency its own pool (threads, connections), so one slow dependency can't exhaust everything.
- [Backpressure](https://www.reactivemanifesto.org/glossary#Back-Pressure) slows producers; [load shedding](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/) rejects excess work early rather than queueing it without bound.

### Tail latency and hedging

- Waiting on all `n` servers, each independently slow with probability `p`, a request is slow with probability `1 − (1 − p)ⁿ` — at 100 servers, [a 1% tail hits 63% of requests](https://research.google/pubs/the-tail-at-scale/).
- Hedged requests: send a second copy after ~p95 latency and take the first reply.

### Failure detection

- Fixed-timeout [heartbeats](https://en.wikipedia.org/wiki/Heartbeat_%28computing%29) trade detection speed against false positives.
- [Phi-accrual](https://doc.akka.io/libraries/akka-core/current/typed/failure-detector.html) (Cassandra, Akka) outputs a suspicion level from heartbeat history.
- [SWIM](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf) ([Consul](https://developer.hashicorp.com/consul/docs/architecture/gossip), [Serf](https://github.com/hashicorp/serf)) pings a random member, then asks `k` peers to probe it indirectly before suspecting it.

## Stream processing

### Event time, watermarks, and windows

- [Event time](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/) (when it happened) vs processing time (when it arrived) — late events break processing-time windows.
- A [watermark](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/#event-time-and-watermarks) says "no events older than T are expected", letting a window close; later stragglers go to a [side output](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/side_output/) or update results.
- [Windows](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/): tumbling (fixed, non-overlapping), sliding or hopping (fixed, overlapping), session (closed by an inactivity gap).

### Change data capture

- [Log-based CDC](https://debezium.io/documentation/reference/stable/features.html) (Debezium) tails the [WAL](https://www.postgresql.org/docs/current/wal-intro.html) or [binlog](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html): every committed change in commit order, deletes included, with no dual writes in the application.
- Polling an `updated_at` column misses hard deletes and rows that commit late with an older timestamp.
- Bootstrap from a [consistent snapshot](https://debezium.io/documentation/reference/stable/connectors/postgresql.html#postgresql-snapshots), then stream from the log position it was taken at.
- Events are ordered per key (partition by primary key); connectors deliver at least once, so consumers must be idempotent.

### Kafka ordering and consumer groups

- Order is guaranteed only within a [partition](https://kafka.apache.org/43/getting-started/introduction/#main-concepts-and-terminology); key by entity ID to keep one entity's events in order.
- A [consumer group](https://kafka.apache.org/43/design/design/#the-consumer) splits partitions among its members — parallelism is capped at the partition count.
- Adding partitions changes `hash(key) % partitions`, so existing keys move and per-key ordering breaks; the count can't be decreased — size it up front.
- [Consumer lag](https://kafka.apache.org/43/operations/monitoring/) (latest offset − committed offset) is the health metric to alert on.

### Kafka producer semantics

- [Idempotent producer](https://kafka.apache.org/43/configuration/producer-configs/#producerconfigs_enable.idempotence) (default since [Kafka 3.0](https://cwiki.apache.org/confluence/display/KAFKA/KIP-679%3A+Producer+will+enable+the+strongest+delivery+guarantee+by+default)) dedupes retried sends per partition.
- [Transactions](https://kafka.apache.org/43/design/design/#using-transactions) make writes across partitions and the consumer offset commit atomic — exactly-once for read-process-write within Kafka.

### Kafka durability

- Each partition has a leader and followers; the [ISR](https://kafka.apache.org/43/design/design/#replication) (in-sync replicas) is the leader plus followers caught up within [`replica.lag.time.max.ms`](https://kafka.apache.org/43/configuration/broker-configs/#brokerconfigs_replica.lag.time.max.ms).
- [`acks=all`](https://kafka.apache.org/43/configuration/producer-configs/#producerconfigs_acks) waits for every current ISR member; [`min.insync.replicas=2`](https://kafka.apache.org/43/configuration/broker-configs/#brokerconfigs_min.insync.replicas) (with replication factor 3) rejects writes when the ISR shrinks below 2 — survives one broker loss without losing acknowledged data.
- [`unclean.leader.election.enable=false`](https://kafka.apache.org/43/configuration/broker-configs/#brokerconfigs_unclean.leader.election.enable) (default) refuses to elect an out-of-sync replica, choosing unavailability over data loss.

### Kafka rebalancing, compaction, KRaft

- A rebalance reassigns partitions when consumers join or leave; the [KIP-848](https://kafka.apache.org/43/operations/consumer-rebalance-protocol/) consumer protocol (GA in [Kafka 4.0](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/)) makes it incremental and broker-driven instead of stop-the-world.
- [Log compaction](https://kafka.apache.org/43/design/design/#log-compaction) removes superseded records in the background, keeping at least the latest record per key (a delete = `null` tombstone) — for changelogs and state restoration.
- Kafka 4.0 (March 2025) removed ZooKeeper: metadata lives in a Raft quorum of controllers ([KRaft](https://kafka.apache.org/43/operations/kraft/)).

### Event sourcing and CQRS

- [Event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) stores every change as an immutable event and rebuilds state by replay, with snapshots for speed.
- [CQRS](https://martinfowler.com/bliki/CQRS.html) splits the write model from read models; if read models update asynchronously (often from events), reads are eventually consistent.
- Event schemas must stay readable forever: only add fields, or upcast old events.
