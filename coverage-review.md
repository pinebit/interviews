# Brief coverage review

Temporary working file (2026-09-29): tick the items to act on, then delete this file before merging.

**Status (2026-09-30):** all 72 P1 items are applied (619 → 675 concepts) and ticked below; notes in *italics* say where placement differs from the proposal. The section limit in AGENTS.md is now 5–20. P2, P3, and trim items are untouched.

**Legend**

- **P1**: commonly asked and missing (or only implied). Add first.
- **P2**: comes up in senior or deep-dive rounds. Worth a bullet or a short concept.
- **P3**: niche or role-specific. Add only if it matches the roles you target.
- **new** = new `###` concept in the *section* named · **extend** = add bullets to an existing concept · **cut / merge** = trim candidates.
- Each item carries the proposed facts so it can be judged on its own. Versions and numbers come from memory; re-verify them when writing the prose.
- Where a new concept would push a section past 8 concepts, the item says what to merge or split.

## Summary

| Brief | Concepts | Verdict | Biggest gaps (P1) |
|---|---|---|---|
| Algorithms | 35 | Solid core | input-size heuristics, heap patterns, Kadane, random sampling |
| Databases | 39 | Strong PostgreSQL/InnoDB internals | join pitfalls, "why isn't my index used", Redis memory, document stores |
| Distributed Systems | 38 | Strong | delivery guarantees, CDC, monotonic clocks, Kafka partition changes |
| Networking | 22 | Good, smallest brief | failure signatures, TCP loss recovery, routing tables, client IP behind proxies |
| Operating Systems | 28 | Good | process states, atomic file replace, CAS/ABA, memory hierarchy |
| System Design | 37 | Strong | Little's law, percentile/cardinality pitfalls, multi-region/DR, video streaming |
| Go | 32 | Strong runtime; some tooling trivia | JSON gotchas, nil maps, context cancel, work stealing |
| JavaScript | 32 | Good; stdlib listings | async ordering, `fetch` semantics, hidden classes |
| Python | 32 | Strong | spawn/pickling, shared class attributes, numeric gotchas, recursion limit |
| Rust | 33 | Strong; "Unsafe and FFI" has no FFI | overflow and casts, Eq/Ord/Hash, layout/niches, `tokio::spawn` bounds |
| Solidity | 36 | Very thorough; longest file; version trivia | clones, admin keys and governance, ERC-1271 checks, slippage |
| TypeScript | 28 | Good | runtime validation, `{}`/`object`, function assignability |
| Backend | 30 | Good | schema evolution, multi-tenancy, time handling |
| Frontend | 36 | Good | effect data fetching, state snapshots, browser storage, error boundaries |
| Security | 40 | Strong | CORS simple requests, CSPRNG, password reset, resource-exhaustion attacks |
| AWS | 24 | Good, compact | ALB vs NLB, cross-account access, S3/CloudFront access, cost drivers |
| DevOps | 33 | Good | Pod security, `count` vs `for_each`, HPA mechanics, incident response |
| AI Engineering | 38 | Strong on serving and RAG | training pipeline, parallelism and GPU memory, filtered vector search |
| Ethereum | 26 | Good | precompiles, RPC block tags and reorgs, SNARK vs STARK, EIP-7702 risks |

## Cross-cutting

### New briefs to consider

- [ ] **P1 if your loop has a low-level design round**: `ood.md` (Fundamentals). SOLID with one concrete violation each (Square/Rectangle for LSP), composition over inheritance, the GoF patterns interviewers name (strategy, observer, decorator, adapter, factory, builder, state, command, chain of responsibility; singleton pitfalls), dependency injection, the LLD interview flow (use cases → entities → interfaces → state and concurrency), classic prompts (parking lot, elevator, vending machine, expense splitting).
- [ ] P3: split `devops.md` into `kubernetes.md` + `devops.md` if Kubernetes keeps growing (it is now 5 of 9 sections).
- [ ] P3 if targeting data roles: `data.md`. Batch vs stream (Lambda/Kappa), Spark shuffle and skew, columnar files (Parquet) and table formats (Iceberg, Delta), orchestration and idempotent backfills.
- Not recommended: a separate concurrency brief. It's covered across os, golang, and rust; add CAS/ABA to os.md instead.

### Ownership gaps

No file owned these; each is now named in the AGENTS.md ownership table (merged into the existing owner rows).

- [x] Change data capture → distributed (stream processing); referenced from database, system, backend (all three already mention CDC).
- [x] Little's law and capacity math → system; referenced from os (thread pools) and backend (pool sizing).
- [x] Monotonic vs wall-clock time → distributed (clocks); referenced from os and golang.
- [x] Schema evolution and compatibility (Protobuf, Avro, JSON) → backend; referenced from distributed (event schemas).
- [x] Timestamps and time zones → backend for app rules; database owns `timestamptz` behavior.
- [x] Disaster recovery tiers → system; aws lists only the AWS services.
- [x] Browser storage APIs → frontend; security keeps the token-storage guidance.

### Duplicates

- [ ] solidity `Oracle integration` bullet 1 repeats ethereum `Oracle manipulation` bullet 1 (owner: ethereum). Keep only the link in solidity.
- [ ] backend `File uploads` bullet 1 repeats system `CDN and object storage` bullet 2 (presigned URLs, metadata only). Keep one.
- [ ] aws `KMS and envelope encryption` bullet 1 re-explains envelope encryption (owner: security). Keep the AWS-specific facts: `GenerateDataKey` and the 4 KB `Encrypt` limit.
- [x] distributed `Effectively-once processing` would overlap the proposed Delivery guarantees concept. Merge them. *Done: replaced by Delivery guarantees.*

### Structure

- Section counts: no brief exceeds the new 20-section limit (javascript has 12, system 11), so no merges are needed for that reason.
- [ ] Many sections have only 2 concepts (guide: 3–8). The P1 items filled backend Service calls, ai Training and fine-tuning, and rust Error handling; *new* P2 items would fill devops CI/CD, ethereum Consensus, rust Unsafe and FFI, and security Supply chain. Merge the rest where they stay thin.
- [ ] Growth budget: P1 added 56 concepts (619 → 675). The remaining 107 P2 and 51 P3 items include 59 *new* P2 concepts; the cut/merge items remove about 24 whole concepts plus many bullets. Pairing each add with a trim in the same brief keeps skimming and quizzes fast.

## Fundamentals

### Algorithms

Solid on arrays, DP, and graphs. Missing the problem-solving heuristics and a few patterns that come up constantly in coding rounds.

**Add**

- [x] P1 · new · *Complexity and problem solving* › **Input size → target complexity**: at ~10⁸ simple operations per second, n ≤ 10 → O(n!), n ≤ 20 → O(2ⁿ), n ≤ 500 → O(n³), n ≤ 5,000 → O(n²), n ≤ 10⁶ → O(n log n), beyond → O(n) or O(log n). Reading the constraints picks the algorithm.
- [x] P1 · new · *Data structures* › **Heap patterns**: **k-way merge** of k sorted lists with a size-k min-heap, O(n log k); **two heaps** (max-heap for the lower half, min-heap for the upper) give a running median in O(log n) per insert; lazy deletion for removals.
- [x] P1 · new · *Arrays and sequences* › **Maximum subarray (Kadane)**: `cur = max(x, cur + x)`, `best = max(best, cur)`, O(n) time and O(1) space; circular variant = max(best, total − minimum subarray) unless every value is negative. The section reaches 8 concepts.
- [x] P1 · new · *Sorting and selection* (rename "Sorting, selection, and sampling") › **Random sampling and shuffling**: **reservoir sampling** keeps the i-th item with probability k/i (one pass, O(k) memory, unknown stream length); **Fisher–Yates** swaps `a[i]` with `a[rand(0..i)]`; drawing from the whole array at each step is biased.
- [ ] P2 · extend · **Recurrence patterns** with the **Master theorem**: `T(n) = aT(n/b) + f(n)`; compare f(n) with n^(log_b a): smaller → Θ(n^(log_b a)), equal → Θ(n^(log_b a) · log n), larger → Θ(f(n)). Replaces the two worked examples.
- [ ] P2 · extend · **Knapsack and one-dimensional DP**: coin change with coins in the outer loop counts **combinations**; with the amount in the outer loop it counts **permutations**.
- [ ] P2 · extend · **Shortest-path choices** table: 0/1 weights → **0-1 BFS** with a deque, O(V+E); all pairs → **Floyd–Warshall** O(V³) (negative edges fine; a negative diagonal entry means a negative cycle); Dijkstra skips stale heap entries (lazy deletion).
- [ ] P2 · new · *Trees and graphs* › **Cycle detection and bipartiteness**: directed → DFS with three colors (reaching a gray node = back edge = cycle); undirected → a visited neighbor that isn't the parent, or union-find; bipartite ⇔ BFS 2-coloring succeeds ⇔ no odd cycle.
- [ ] P2 · new · *Trees and graphs* › **Grid and multi-source BFS**: a grid is an implicit graph (4 or 8 neighbors), O(rows × cols); seed the queue with every source at distance 0 to get "distance to the nearest X" in one pass.
- [ ] P2 · extend · **Tree traversal and BST ordering**: validate a BST with inherited (min, max) bounds, not parent–child comparisons; lowest common ancestor from post-order return values, or **binary lifting** for O(log n) repeated queries.
- [ ] P2 · extend · **Comparison sorts** with what standard libraries use: Python **Timsort** (stable), C++ `std::sort` introsort (unstable), Go pdqsort (unstable, since 1.19), Rust `sort` driftsort / `sort_unstable` ipnsort (since 1.81), JavaScript stable since ES2019.
- [ ] P2 · extend · **Binary search boundaries**: in a rotated sorted array one half is always sorted; check whether the target lies in it. Duplicates degrade the worst case to O(n).
- [ ] P2 · extend · **Quickselect and top-k**: **3-way partition** (Dutch national flag: `<`, `=`, `>` regions in one pass) keeps quicksort and quickselect fast with many duplicates.
- [ ] P3 · new · *Trees and graphs* › **Strongly connected components**: Tarjan (one DFS with low-links) or Kosaraju (DFS on the graph, then on its reverse), O(V+E); the condensation is a DAG.
- [ ] P3 · new · *Greedy, backtracking, and hardness* › **Number theory toolkit**: Euclid's gcd O(log min(a, b)), fast modular exponentiation O(log e), sieve of Eratosthenes O(n log log n), modular inverse via Fermat when the modulus is prime.
- [ ] P3 · extend · **LRU cache** with LFU in O(1): frequency → doubly linked list of keys, plus a pointer to the minimum frequency.

**Trim**

- [ ] cut · **Time and space bounds** bullet 1's opening ("state the input size…"): generic advice. Keep the Ω(k) output-size point.
- [ ] cut · **Recurrence patterns** bullets 1–2: two textbook recurrences, superseded by the Master theorem.
- [ ] cut · **LRU cache** bullet 2: library API listing (low confidence; handy mid-interview).

### Databases

Strong on PostgreSQL and InnoDB internals. Weaker on everyday SQL pitfalls, index diagnosis, and non-relational breadth (no document store).

**Add**

- [x] P1 · new · *SQL gotchas* › **Join pitfalls**: a condition on the right table in `WHERE` turns a `LEFT JOIN` into an inner join, so put it in `ON`; joining two one-to-many children multiplies rows and inflates `SUM`/`COUNT` (aggregate each in a subquery first); `EXISTS`/`NOT EXISTS` are semi/anti-joins and never duplicate rows.
- [x] P1 · new · *Query execution and tuning* › **Why an index isn't used**: low selectivity (the planner prefers a sequential scan when many rows match), leading-wildcard `LIKE '%x'` (needs a trigram GIN index), `LIKE 'x%'` needs C collation or `text_pattern_ops`, implicit casts, `OR` across columns, stale statistics. Scan types: Seq, Index, Index Only, **Bitmap Heap** (combines several indexes). Absorbs **Reading EXPLAIN ANALYZE**.
- [x] P1 · new · *Non-relational stores* › **Redis eviction, expiry, and messaging**: `maxmemory-policy` defaults to **`noeviction`**, so writes fail when memory is full; caches use `allkeys-lru`/`allkeys-lfu`, while `volatile-*` evicts only keys with a TTL; expired keys are removed lazily on access plus by periodic sampling; pub/sub is fire-and-forget, Streams add persistence, consumer groups, and acks.
- [x] P1 · new · *Non-relational stores* › **Document stores (MongoDB)**: embed what's read together, reference unbounded or shared data; **16 MB** document limit; write concern `w: "majority"` (default since 5.0), since `w: 1` can lose acknowledged writes on failover; multi-document transactions (4.0 for replica sets, 4.2 sharded) are costly, so design for single-document atomicity.
- [ ] P2 · new · *Transactions and isolation* › **Implementing serializability**: actual serial execution (Redis, VoltDB: one thread, short transactions), **two-phase locking** (readers and writers block each other; MySQL `SERIALIZABLE`, SQL Server), **SSI** (optimistic, aborts on dangerous conflicts; PostgreSQL, CockroachDB).
- [ ] P2 · extend · **Anomalies × isolation levels** table: add lost-update and write-skew columns and a snapshot-isolation row, so PostgreSQL RR vs MySQL RR read off one matrix; then shorten the two engine concepts.
- [ ] P2 · new · *Schema design* › **Timestamps and time zones**: `timestamptz` stores a UTC instant and converts on display; `timestamp` (no zone) silently changes meaning when the session zone changes; `now()` is the transaction start time, `clock_timestamp()` the actual time. App-level rules go in backend.
- [ ] P2 · new · *SQL gotchas* › **Hierarchies and recursive CTEs**: `WITH RECURSIVE` = anchor + recursive term (`UNION`, or the `CYCLE` clause in PostgreSQL 14+, stops cycles); models: adjacency list (simple writes), materialized path/`ltree` (fast subtree reads), closure table (all ancestor pairs; fast reads, heavy writes).
- [ ] P2 · extend · **Physical vs logical replication**: an inactive **replication slot** retains WAL until the disk fills (`max_slot_wal_keep_size`, PostgreSQL 13+); long queries on a hot standby get canceled by replay conflicts unless `hot_standby_feedback` is on, which bloats the primary.
- [ ] P2 · extend · **Surrogate keys**: sequences are non-transactional, so rollbacks leave **gaps** and IDs don't follow commit order; gapless invoice numbers need a counter row updated under a lock.
- [ ] P2 · extend · **Upsert**: `ON CONFLICT DO NOTHING ... RETURNING` returns nothing for existing rows; `MERGE` (PostgreSQL 15+) isn't a concurrency-safe upsert, since concurrent inserts can still raise unique violations.
- [ ] P2 · new · *MVCC and locking* › **Slow COUNT(*)**: PostgreSQL checks each row's visibility, so `COUNT(*)` scans (an index-only scan helps while the visibility map is current); dashboards use `pg_class.reltuples` estimates or a counter table.
- [ ] P2 · new · *Schema design* › **JSONB vs columns**: JSONB for sparse or variable attributes, GIN (`jsonb_path_ops`) for containment queries; no per-key statistics (bad estimates), and updating one key rewrites the whole value, so promote hot keys to columns.
- [ ] P3 · new · *Storage engines and durability* › **Buffer pool vs page cache**: InnoDB's buffer pool takes ~50–80% of RAM with `O_DIRECT`; PostgreSQL's `shared_buffers` ~25%, relying on the OS page cache (double buffering); TOAST stores values over ~2 KB compressed and out of line.
- [ ] P3 · extend · **Write-ahead log**: relaxed durability (`synchronous_commit = off`, `innodb_flush_log_at_trx_commit = 2`) loses the last moments of commits on a crash but never corrupts data.
- [ ] P3 · extend · **PostgreSQL MVCC**: `VACUUM FULL` rewrites the table under `ACCESS EXCLUSIVE`; `pg_repack` rebuilds it online.
- [ ] P3 · extend · **Connection pooling**: prepared statements may switch to a generic plan after five executions (`plan_cache_mode`), which can be far worse for skewed values.

**Trim**

- [ ] cut · **Redis persistence and licensing** bullet 3: license history is trivia; at most "Valkey is the drop-in open-source fork".
- [ ] cut · **OLTP vs OLAP** bullet 1: definition-level. Keep the column-store bullet.
- [ ] merge · **InnoDB MVCC** (one bullet) into **MySQL InnoDB isolation**.
- [ ] merge · **Deep pagination cost** (one bullet) into the new index concept; backend owns pagination.
- [ ] merge · **Materialized views** (one bullet) into **OLTP vs OLAP** or the denormalization bullet in **Normalization**.

### Distributed Systems

Strong and dense.

**Add**

- [x] P1 · new · *Transactions across services* › **Delivery guarantees** (absorbs Effectively-once processing): at-most-once = ack or commit the offset **before** processing; at-least-once = after (a crash between effect and ack redelivers); exactly-once *delivery* is impossible, exactly-once *effect* = at-least-once + idempotent handling, or one transaction covering the effect and the offset.
- [x] P1 · extend · **Physical clocks and TrueTime**: measure durations, timeouts, and leases with the **monotonic clock** (`CLOCK_MONOTONIC`, Go's `time.Since`, `performance.now()`); wall-clock time jumps on NTP steps, leap-second smearing, and VM migration.
- [x] P1 · new · *Stream processing* › **Change data capture**: log-based CDC (Debezium) reads the WAL or binlog, so it sees every change in commit order, deletes included, with no dual writes; polling `updated_at` misses deletes and same-timestamp rows; start from a consistent snapshot, then stream from its log position; ordering holds per key.
- [x] P1 · extend · **Kafka ordering and consumer groups**: adding partitions remaps `hash(key) % partitions` and **breaks per-key ordering** for existing keys, and the count can't be decreased, so size partitions up front; consumer **lag** is the health metric to alert on.
- [ ] P2 · new · *Partitioning* › **Rebalancing partitions**: `hash % N` moves almost every key when N changes; either a **fixed, large number of partitions** moved whole between nodes (Kafka, Elasticsearch, Couchbase) or **dynamic splitting** of large ranges (HBase, MongoDB, CockroachDB, Spanner); automatic rebalancing during a failure can cascade.
- [ ] P2 · new · *Consensus and coordination* › **Coordination services**: ZooKeeper ephemeral nodes and etcd leases vanish with the session, tying membership and locks to liveness; watches notify on change; a lock = sequential node + watching only the predecessor (no herd effect); ZooKeeper reads come from any replica and can be stale (`sync()` first), etcd reads are linearizable by default.
- [ ] P2 · extend · **Raft**: **Pre-Vote** stops a node rejoining after a partition from bumping the term and deposing a healthy leader; typical timing is a ~100 ms heartbeat and ~1 s election timeout (etcd defaults).
- [ ] P2 · new · *Stream processing* › **Exactly-once in stream processors**: Flink injects checkpoint **barriers** (Chandy–Lamport style) and snapshots operator state together with source offsets; end-to-end exactly-once needs a replayable source and a transactional (two-phase commit) or idempotent sink; transactional output becomes visible only when the checkpoint commits.
- [ ] P2 · extend · **Two-phase commit**: when each participant is itself a consensus group (Spanner runs 2PC over Paxos groups), a coordinator crash no longer blocks; XA across heterogeneous systems still does.
- [ ] P3 · extend · **Session guarantees**: consistent prefix reads (writes are seen in the order they happened); breaks when partitions replicate independently.
- [ ] P3 · extend · **Quorums**: `W + R > N` alone isn't linearizable; a concurrent write can be seen by one read and missed by a later one unless readers repair before returning.
- [ ] P3 · extend · **Multi-leader and leaderless**: give each record a **home region** that takes its writes, avoiding conflicts; move the home when a region fails.
- [ ] P3 · new · *Failure handling* › **Metastable failures**: a trigger (spike, cache flush) pushes a system into an overload that retries and timeouts sustain after the trigger is gone; recovery needs explicit load shedding, and retry budgets and bounded queues prevent it.
- [ ] P3 · extend · **Failure detection**: gossip spreads membership and metadata to all N nodes in O(log N) rounds (Cassandra, Serf).

**Trim**

- [ ] merge · **Window types** (one bullet) into **Event time and watermarks**; frees a slot in Stream processing for CDC.
- [x] merge · **Effectively-once processing** into the Delivery guarantees concept above.

### Networking

The smallest brief (5 sections, 22 concepts). Good fundamentals, light on troubleshooting and routing.

**Add**

- [x] P1 · new · *End to end* › **Connection failure signatures**: **refused** = RST (host reachable, nothing listening); **timeout** = SYN dropped (firewall, security group, dead host), and Linux retries a SYN for ~**127 s** by default, so set connect timeouts; **reset by peer** mid-stream = the peer crashed or a middlebox hit its idle timeout; a proxy's **502** = upstream refused or reset, **504** = upstream too slow.
- [x] P1 · new · *TCP* › **Retransmission and loss recovery**: the RTO comes from smoothed RTT, with a Linux floor of **200 ms** (initial 1 s) and doubling per retry, so one lost packet on a quiet connection adds ≥ 200 ms (a classic p99 spike); **fast retransmit** after 3 duplicate ACKs; SACK names exactly which segments are missing.
- [x] P1 · new · *IP and routing* › **Routing tables**: the most specific route wins (**longest prefix match**: `/32` beats `/24` beats `0.0.0.0/0`); the default route points at the gateway; ARP resolves the next hop's MAC on the local link, so MACs change per hop while IPs stay end to end unless NAT rewrites them.
- [x] P1 · new · *HTTP versions* (rename "HTTP") › **Client IP behind proxies**: L7 proxies append `X-Forwarded-For`, and clients can forge the earlier entries, so trust only those added by your own proxies (count from the right); L4 load balancers preserve the source IP or pass it with the **PROXY protocol**; rate limits and audit logs depend on getting this right.
- [ ] P2 · new · *TCP* › **Connection states for debugging** (table): SYN_SENT (no SYN-ACK: filtered?), SYN_RECV (half-open: SYN flood?), ESTABLISHED, FIN_WAIT_2 (peer hasn't closed), CLOSE_WAIT (your app hasn't closed), TIME_WAIT (you closed first). Absorbs the CLOSE_WAIT bullet from **Teardown and TIME_WAIT**.
- [ ] P2 · extend · **Handshake and connection queues**: the listen backlog is capped by `net.core.somaxconn` (4096 since Linux 5.4); `SO_REUSEPORT` lets several processes bind one port, each with its own kernel-balanced accept queue (Nginx, Envoy).
- [ ] P2 · extend · **Resolution path**: Kubernetes Pods resolve with `ndots:5`, so an external name with fewer dots first tries every search domain (several wasted lookups per call); use FQDNs with a trailing dot or lower `ndots`.
- [ ] P2 · extend · **NAT**: NAT traversal. STUN learns the public mapping for UDP hole punching; symmetric NATs defeat it, so WebRTC falls back to a **TURN** relay (ICE tries candidates in order).
- [ ] P3 · new · *IP and routing* › **L3/L4 load distribution**: ECMP hashes flows across equal-cost paths; L4 balancers use consistent hashing (Maglev) so flows survive balancer changes; direct server return sends responses straight from the backends.
- [ ] P3 · extend · **Loading a URL**: light in fiber covers ~200 km per ms, about 1 ms of RTT per 100 km, so a transatlantic round trip costs ~70 ms whatever the bandwidth.
- [ ] P3 · extend · **HTTP/2**: Rapid Reset (2023). Clients open and immediately cancel streams to exhaust servers; servers now cap resets per connection.

**Trim**

- [ ] merge · **UDP**: definition-level. Move "DNS, VoIP, games, QUIC" into **HTTP/3 and QUIC** or **Head-of-line blocking**.
- [ ] cut · **HTTP/1.1** bullet 2's history (domain sharding, sprite sheets). Keep "~6 connections per host".
- [ ] merge · **Debugging tools**: a tool list. Fold it into the failure-signatures concept as symptom → tool.

### Operating Systems

Good coverage of memory and I/O. Missing process states, a safe file-replace pattern, lock-free basics, and latency intuition.

**Add**

- [x] P1 · extend · **Durability and fsync**: **atomic file replace**. Write a temp file → `fsync` it → `rename` it over the target (atomic on POSIX) → `fsync` the directory; readers see the old or the new file, never a torn one. *Done as a separate concept,* Atomic file replace.
- [x] P1 · new · *Processes and threads* › **Process states** (table): R (running or runnable), S (interruptible sleep), **D** (uninterruptible, usually disk or NFS I/O; even `SIGKILL` waits, and it counts in load average), Z (zombie), T (stopped).
- [x] P1 · new · *Synchronization* › **Atomics, CAS, and the ABA problem**: compare-and-swap loops build lock-free structures and mutex fast paths; **ABA** = a value goes A → B → A and a stale CAS succeeds, fixed with version-tagged pointers or safe reclamation (hazard pointers, epochs); under heavy contention CAS loops thrash the cache line; x86 is TSO, ARM weakly ordered (orderings in [rust.md](rust.md)).
- [x] P1 · new · *Performance analysis* › **Memory hierarchy latencies**: L1 ~1 ns, L2 ~4 ns, L3 ~10–40 ns, DRAM ~100 ns, NVMe read ~10–100 µs; sequential access and contiguous layouts (arrays over linked lists, struct-of-arrays) win through prefetching and cache lines. system.md keeps its short interview list.
- [ ] P2 · new · *Processes and threads* › **IPC mechanisms**: pipes (one-way byte stream), Unix domain sockets (two-way, faster than loopback TCP, pass file descriptors via `SCM_RIGHTS`), shared memory + a lock (no copies), signals (no payload); the Docker and containerd APIs listen on Unix sockets.
- [ ] P2 · new · *Memory* › **Heap allocators and RSS growth**: `malloc` serves large requests (≥ 128 KB by default) with `mmap` and small ones from arenas; glibc creates up to 8 arenas per core on 64-bit, so multi-threaded services fragment and RSS only grows; `MALLOC_ARENA_MAX=2`, or jemalloc/tcmalloc/mimalloc. Memory already has 8 concepts: merge **Page faults** into **Virtual memory and the TLB** to make room.
- [ ] P2 · extend · **CPU quotas and throttling**: pool sizing. CPU-bound ≈ number of cores (or the quota); blocking I/O ≈ cores × (1 + wait/compute), or derive it from **Little's law** (see system.md).
- [ ] P3 · new · *Files and I/O* › **File locks**: `flock` locks a whole file per open file description; POSIX `fcntl` locks are per process and **released when any descriptor to the file closes**; both are advisory.
- [ ] P3 · new · *Files and I/O* › **Write-back and direct I/O**: dirty pages flush in the background past `dirty_background_ratio` and throttle writers at `dirty_ratio`, so a bulk write can stall unrelated writes; `O_DIRECT` bypasses the page cache (databases with their own buffer pool).
- [ ] P3 · new · *Processes and threads* › **Process memory layout**: text, data/BSS, heap, mmap region (shared libraries, large allocations, thread stacks), stack with a guard page (overflow → `SIGSEGV`); ASLR randomizes the bases.
- [ ] P3 · new · *Performance analysis* › **Virtualization**: VMs (own kernel, hardware isolation) vs containers (shared kernel) vs microVMs (Firecracker, behind Lambda and Fargate) vs gVisor (user-space kernel); `st` time shows what the hypervisor takes.

**Trim**

- [ ] cut · **Processes vs threads** bullet 1: definition-level. Keep the `clone()` bullet, merged into **fork, exec, copy-on-write**.
- [ ] cut · **Priority inversion**: rarely asked outside real-time roles (low confidence; Mars Pathfinder is a good memory hook).
- [ ] cut · **Linux observability tools** bullet 1: a tool list. Keep the perf/eBPF/strace bullets, or turn the concept into a symptom → tool table.

### System Design

Strong building blocks and classic designs. Missing capacity math, metric aggregation pitfalls, multi-region/DR, and a couple of classic prompts.

**Add**

- [x] P1 · extend · **Back-of-envelope conversions**: **Little's law** L = λ × W, so in-flight requests = throughput × latency (1,000 RPS × 200 ms = 200 concurrent requests → threads, connections, pool sizes).
- [x] P1 · extend · **Observability**: percentiles **can't be averaged** across hosts or windows, so merge histograms and then take p99; **high-cardinality labels** (user ID, request ID) multiply Prometheus time series, so keep them in logs and traces.
- [x] P1 · new · *Reliability and operations* › **Multi-region and disaster recovery**: tiers by RTO/RPO, from backup and restore (hours) → pilot light → warm standby → active-active (near zero); async cross-region replication means RPO > 0; active-active needs conflict handling or per-record home regions, plus global routing (GeoDNS, anycast); rehearse failover. Absorbs the RPO/RTO bullet from **Availability math**.
- [x] P1 · new · *Classic designs: user-facing* › **Video streaming**: upload to object storage → transcoding DAG (split into chunks, encode in parallel) → renditions at several bitrates → **HLS/DASH** segments (2–10 s) plus a manifest → CDN; the player picks a rendition per segment (**adaptive bitrate**); pre-warm popular content at the edge.
- [ ] P2 · extend · **Load balancing**: **power of two choices**. Sample two backends and pick the less loaded: near-optimal balance without global state, and no herding onto the one server stale stats call "least loaded".
- [ ] P2 · new · *Classic designs: user-facing* › **Top-K and trending**: per-window counts in a stream processor; exact counts + a min-heap for moderate cardinality, **count-min sketch + heap** for huge key spaces; merging per-partition top-k is approximate, so fetch k′ > k per partition; sharded counters for view and like counts.
- [ ] P2 · new · *Classic designs: data and infrastructure* › **Distributed key-value store**: the Dynamo-style synthesis. Consistent hashing + virtual nodes, N replicas with W/R quorums, hinted handoff, Merkle anti-entropy, vector clocks or LWW, gossip membership; each piece links to distributed.md.
- [ ] P2 · new · *Data storage choices* › **Replication vs erasure coding**: 3× replication survives 2 losses at 200% overhead; Reed–Solomon 6+3 survives 3 losses at 50% overhead, but reads and repairs touch many nodes, so it suits cold and blob storage (S3, HDFS EC).
- [ ] P2 · new · *Reliability and operations* › **Blast-radius reduction**: **cell-based architecture** (independent full stacks, each serving a slice of customers); **shuffle sharding** (each customer gets a random subset of workers, so one poison tenant rarely shares all of another's); static stability (keep serving when the control plane is down).
- [ ] P3 · new · *Asynchronous processing* › **Lambda vs Kappa architecture**: Lambda = batch layer (complete, recomputable) + speed layer (fresh, approximate), two codebases to keep in sync; Kappa = one streaming pipeline that reprocesses by replaying the log into a new output.
- [ ] P3 · extend · **CDN and object storage**: an origin shield collapses edge misses into one origin fetch; normalize the cache key (drop tracking parameters); `stale-while-revalidate` and `stale-if-error` at the edge.
- [ ] P3 · new · *Classic designs: data and infrastructure* › **Order matching**: one single-threaded matching engine per symbol with an in-memory order book (price-time priority), fed by a sequencer and an event log for recovery and replicas (fintech and crypto loops).
- [ ] P3 · extend · **Back-of-envelope conversions**: 2¹⁰ ≈ 10³, 2²⁰ ≈ 10⁶, 2³⁰ ≈ 10⁹, 2⁴⁰ ≈ 10¹².

**Trim**

- [ ] cut · **Leaderboard** bullet 2: Redis command deprecation trivia.
- [ ] cut · **SQL vs NoSQL** bullet 1: definition-level.
- [ ] cut · **Monolith vs microservices** bullets 1–2: well-known pros and cons. Keep "modular monolith by default" and Conway's law.

## Languages

### Go

Strong runtime and concurrency coverage. Missing several everyday gotchas; a few tooling and syntax items are low value.

**Add**

- [x] P1 · new · *Standard library gotchas* › **encoding/json gotchas**: numbers decode into `any` as **float64**, so IDs above 2⁵³ lose precision (`Decoder.UseNumber`); a nil slice encodes as `null`, an empty one as `[]`; unexported fields are silently skipped; `omitempty` never omits a struct, `omitzero` (1.24) does; unknown fields are ignored unless `DisallowUnknownFields`.
- [x] P1 · extend · **Maps**: reading a nil map returns zero values, but **writing panics**, so `make` it first (a nil slice, by contrast, works with `append`).
- [x] P1 · extend · **context.Context**: every `WithCancel`/`WithTimeout`/`WithDeadline` returns a `cancel` you must call (`defer cancel()`), or the child and its timer live until the parent ends; `go vet` reports it (`lostcancel`).
- [x] P1 · extend · **Scheduler (GMP)**: each P has a local run queue (256 goroutines) plus a `runnext` slot; an idle P **steals half** of another P's queue; the global queue is checked every 61st scheduling round for fairness.
- [ ] P2 · new · *Standard library gotchas* › **time gotchas**: `time.Time` carries a location and a monotonic reading, so compare with `Equal`, not `==`, and don't use it as a map key; `time.Since` uses the monotonic clock; bare integers are nanoseconds (`time.Sleep(5)` sleeps 5 ns).
- [ ] P2 · new · *Standard library gotchas* › **Graceful shutdown**: `signal.NotifyContext` for SIGTERM → `srv.Shutdown(ctx)` stops accepting and waits for in-flight requests, but not for hijacked connections (WebSockets); `net/http` recovers a handler panic per request, but a panic in a goroutine you started kills the process.
- [ ] P2 · extend · **Error wrapping**: `%w` makes the wrapped error part of your API (callers can match it), `%v` hides it; sentinel (`io.EOF`) vs typed (`*fs.PathError`) vs opaque errors; `:=` inside a block shadows the outer `err`.
- [ ] P2 · extend · **Garbage collector**: **GC assist**. Goroutines that allocate during a cycle are drafted into marking, so allocation-heavy paths see latency spikes; background marking targets ~25% of `GOMAXPROCS`.
- [ ] P2 · new · *Modules and tooling* › **Static binaries and cgo**: `CGO_ENABLED=0` gives a fully static binary (for `scratch` or distroless images); with cgo, DNS may go through libc's resolver (`netgo` vs `netcgo`); cgo calls cost tens of nanoseconds and occupy a thread; cross-compile with `GOOS`/`GOARCH`.
- [ ] P3 · extend · **Method sets and embedding**: use pointer receivers when methods mutate, the struct is large, or it holds a `sync.Mutex`; don't mix receiver kinds on one type.
- [ ] P3 · new · *Types and interfaces* › **Package initialization**: imported packages initialize first, then package-level variables in dependency order, then `init()` functions in file order; keep `init` free of I/O.

**Trim**

- [ ] cut · **Newer language features**: syntax trivia (`min`/`max`, range over int, generic type aliases). Keep `new(expr)` at most.
- [ ] cut · **Toolchains and tools**: `GOTOOLCHAIN`, `tool` directives, and `go fix` modernizers are rarely asked.
- [ ] cut · **Routing, JSON, logging** bullets 2–3: json/v2's status keeps moving and "`log/slog` exists" is trivia. Replace them with the encoding/json gotchas concept.
- [ ] cut · **Test tooling** bullet 1: table-driven tests and `t.Run`/`t.Parallel`/`t.Cleanup` are basics.
- [ ] cut · **Cleanups, weak pointers, interning**: niche runtime APIs (low confidence).

### JavaScript

Good language-semantics coverage, but light on async ordering and engine internals; several concepts are standard-library listings.

**Add**

- [x] P1 · new · *Async* › **async/await ordering**: the `Promise` executor runs **synchronously**; `.then` callbacks and the code after `await` always run as microtasks, even for resolved values; inside `try`, `return promise` bypasses the `catch`, so write `return await`; an `async` function always returns a new promise.
- [x] P1 · new · *Async* › **fetch semantics**: `fetch` rejects only on network failure; HTTP 4xx/5xx resolve with `res.ok === false`; the body can be read once (`res.clone()` to reuse it); there's no default timeout (`AbortSignal.timeout`).
- [x] P1 · new · *Memory* › **Hidden classes and inline caches**: V8 gives objects built with the same properties in the same order a shared hidden class (shape); property-access sites cache shapes: monomorphic is fast, more than 4 shapes goes **megamorphic**; initialize every field in the constructor and avoid `delete` on hot objects.
- [ ] P2 · new · *Coercion and equality* › **Strings and Unicode**: strings are UTF-16, so `'😀'.length === 2` and indexing can split a surrogate pair; `for...of` and spread iterate code points; user-perceived characters need `Intl.Segmenter`; `normalize('NFC')` before comparing.
- [ ] P2 · new · *Coercion and equality* › **Object vs Map**: object keys are strings or symbols (numbers coerce), ordered integer-like keys ascending, then strings by insertion, then symbols; `Map` keeps any key type in insertion order, has `size`, and handles frequent adds and deletes better; `JSON.stringify` turns a `Map` into `{}`.
- [ ] P2 · new · *Node.js runtime* › **EventEmitter gotchas**: listeners run **synchronously** in registration order; an `'error'` event without a listener **throws** and crashes the process; more than 10 listeners logs a leak warning; `events.once()` returns a promise.
- [ ] P2 · extend · **Microtasks vs macrotasks**: nested `setTimeout` is clamped to ≥ **4 ms** after 5 levels; hidden tabs throttle timers to once per second, and Chrome can throttle chained timers to once per minute after 5 minutes hidden.
- [ ] P2 · extend · **Type-check quirks**: `Array.prototype.sort` is stable since ES2019 and sorts in place (`toSorted` copies); `??` replaces only `null`/`undefined`, while `||` also replaces `0` and `''`.
- [ ] P2 · extend · **CommonJS vs ESM**: in an import cycle ESM sees uninitialized bindings (TDZ `ReferenceError`), CommonJS a partially filled `exports` object.
- [ ] P3 · extend · **Typed arrays**: browsers expose `SharedArrayBuffer` only to cross-origin-isolated pages (COOP `same-origin` + COEP `require-corp`).

**Trim**

- [ ] cut · **Array and object helpers**: standard-library listing (`toSorted`, `with`, `groupBy`).
- [ ] cut · **Promise helpers**: API listing (`withResolvers`, `try`).
- [ ] cut · **Sets and iterators** bullet 1: Set method list. Keep the lazy iterator-helpers bullet.
- [ ] cut · **Temporal** bullet 2: browser support status goes stale within months.
- [ ] cut · **Workers, cluster, child processes** bullet 3: `spawn` vs `exec` basics.

### Python

Strong on the runtime, object model, and asyncio. Missing a few classic gotchas and the server and deployment angle.

**Add**

- [x] P1 · extend · **multiprocessing start methods**: with `spawn`/`forkserver` (defaults on macOS since 3.8 and on Linux since 3.14) children **re-import the main module**, so guard entry code with `if __name__ == "__main__":`; arguments and results must pickle (no lambdas, local functions, or open sockets).
- [x] P1 · new · *Gotchas* › **Shared class attributes**: a mutable class attribute (`items = []` in the class body) is shared by every instance; `self.items.append(x)` mutates the shared list, while `self.items = [...]` creates an instance attribute that shadows it. *Done in* Object model *instead, to keep Gotchas at 8.*
- [x] P1 · new · *Gotchas* › **Numeric gotchas**: `//` and `%` floor toward −∞ (`-7 // 2 == -4`, `-7 % 2 == 1`), unlike C, Go, Rust, and JavaScript; `round()` rounds half to even (`round(2.5) == 2`); ints never overflow; use `decimal.Decimal` for money.
- [x] P1 · new · *Gotchas* › **Recursion depth**: the default limit is **1000** (`RecursionError`) and there's no tail-call optimization, so deep DFS or memoized recursion needs an explicit stack or a careful `sys.setrecursionlimit`.
- [ ] P2 · new · *Concurrency* › **WSGI vs ASGI servers**: WSGI (Flask, Django) handles one request per worker thread or process; ASGI (FastAPI, Starlette) runs an event loop per worker; Gunicorn pre-forks workers, and refcount updates dirty the copy-on-write pages; `gc.freeze()` (3.7) before forking and **immortal objects** (3.12, PEP 683) keep them shared.
- [ ] P2 · new · *Concurrency* › **contextvars**: a `ContextVar` carries request-scoped state; each asyncio task runs in a **copy** of the context taken at creation, making it the async-safe replacement for thread-locals.
- [ ] P2 · extend · **Descriptors** (or new **Attribute lookup**): `obj.x` checks data descriptors on the type → the instance `__dict__` → non-data descriptors and class attributes → `__getattr__` (only on failure); `__getattribute__` runs on every access.
- [ ] P2 · extend · **Context managers and exceptions**: `raise New() from err` sets `__cause__`, implicit chaining sets `__context__`; `return` or `break` in `finally` swallows the exception (SyntaxWarning since 3.14, PEP 765).
- [ ] P2 · extend · **dict and set internals**: `defaultdict` **inserts** the key on any missing-key read, so `if d[k]:` grows the dict; use `k in d` or `.get`.
- [ ] P2 · extend · **Threads vs processes vs asyncio**: `concurrent.futures` executors are the high-level API for threads and processes; `asyncio.Semaphore` bounds concurrency; `asyncio.timeout()` (3.11) sets deadlines.
- [ ] P3 · extend · **Gradual typing and protocols**: `TypeIs` (3.13) narrows both branches, `TypeGuard` only the true one; runtime validation needs Pydantic or similar, since dataclasses don't validate.

**Trim**

- [ ] cut · **Refcounting and the cyclic GC** bullet 2: patch-release GC history won't be asked.
- [ ] cut · **Mutation during iteration** bullet 2: "dict order since 3.7" repeats dict internals.
- [ ] merge · **Late-binding closures** (one bullet) into **Mutable default arguments** (same `i=i` fix) or **Scope and `UnboundLocalError`**.
- [ ] cut · **Specializing interpreter and JIT** bullet 2: the JIT is off by default (low confidence).
- [ ] restructure · merge Recent language features + Typing (2 concepts each).

### Rust

Strong on ownership, traits, and async. Missing numeric semantics, the standard trait contracts, layout, and any actual FFI content.

**Add**

- [x] P1 · new · *Error handling* › **Integer overflow and casts**: overflow **panics in debug and wraps in release** (unless `overflow-checks = true`), so state intent with `checked_`, `wrapping_`, `saturating_`, or `overflowing_`; `as` truncates between integer types and saturates float → int (NaN → 0).
- [x] P1 · new · *Traits and generics* › **Eq, Ord, and Hash**: `PartialEq`/`PartialOrd` allow incomparable values (NaN), `Eq`/`Ord` promise a total order; `f64` implements neither, nor `Hash`, so it can't key a `HashMap` or use `.sort()` (use `total_cmp` or an ordered wrapper); `Hash` must agree with `Eq`; derived `Ord` compares fields in declaration order.
- [x] P1 · new · *Smart pointers and memory* › **Layout and niche optimization**: `Option<&T>`, `Option<Box<T>>`, and `Option<NonZeroU32>` are the size of the inner type (the null or zero niche encodes `None`); the default `repr(Rust)` may reorder fields, `repr(C)` is for FFI; `&str`, `&[T]`, and `&dyn Trait` are two words; an enum is its largest variant plus a tag.
- [x] P1 · extend · **Futures and executors**: `tokio::spawn` needs a `Send + 'static` future, so move owned data or `Arc` clones in; Tokio's default runtime is multi-threaded work-stealing, and `current_thread` + `LocalSet` runs non-`Send` futures; `JoinSet` manages groups of tasks.
- [ ] P2 · new · *Unsafe and FFI* › **FFI boundaries**: `#[repr(C)]` types and `extern "C"` functions; `CString`/`CStr` for NUL-terminated strings (a pointer from a temporary `CString` dangles); a panic escaping an `extern "C"` function **aborts since 1.81** (UB before), so use `extern "C-unwind"` or `catch_unwind`; bindgen and cbindgen generate the bindings.
- [ ] P2 · new · *Lifetimes* › **Variance and PhantomData**: `&'a T` is covariant; `&'a mut T` is **invariant** in `T` (otherwise a shorter-lived reference could be written through it); `Cell<T>` is invariant; `PhantomData<T>` declares ownership and variance for types that hold raw pointers.
- [ ] P2 · new · *Smart pointers and memory* › **Collections gotchas**: `HashMap` hashes with randomly keyed SipHash-1-3, which resists HashDoS but is slow, so swap in FxHash or ahash for trusted keys; the `entry` API avoids a double lookup; `BTreeMap` for ordered iteration and ranges; `swap_remove` is O(1).
- [ ] P2 · extend · **Borrow rules and NLL**: borrows split across struct fields but not slice indices (`split_at_mut`, or `get_disjoint_mut` since 1.86); closures capture disjoint fields since edition 2021.
- [ ] P2 · extend · **Static vs dynamic dispatch**: a closed set of variants → enum + `match` (exhaustive, no allocation); an open set → `dyn Trait`; trait upcasting (`&dyn Sub` → `&dyn Super`) since 1.86.
- [ ] P3 · extend · **Interior mutability** table: `LazyLock`/`LazyCell` (1.80) replace `lazy_static` and `once_cell::Lazy`.
- [ ] P3 · new · *Macros and Cargo* › **Tests and release builds**: unit tests in `#[cfg(test)] mod tests` reach private items, `tests/` sees only the public API, doc tests run too; release profile knobs (`lto`, `codegen-units = 1`, `panic = "abort"`); debug builds can be 10–100× slower, so benchmark in release.

**Trim**

- [ ] cut · **Iterators** bullet 2: `iter`/`iter_mut`/`into_iter` basics.
- [ ] cut · **String vs &str** bullet 1: basics. Keep the no-indexing and char-boundary panic bullet.
- [ ] cut · **Lock files and editions** bullet 2's version note ("edition 2024 since 1.85"). Keep what edition 2024 changes.
- [ ] merge · **Async closures** (one bullet) into **Futures and executors** or **Fn, FnMut, FnOnce**.

### Solidity

The most thorough brief (254 lines). Few additions; trimming version trivia matters more here.

**Add**

- [x] P1 · new · *Gas optimization* (deployment cost) or *Upgradeability* › **Clones and factories**: an **EIP-1167 minimal proxy** (45 bytes of runtime code delegating to a fixed implementation) makes deploying many instances cheap; `CREATE2` + salt gives addresses known before deployment; clones can't be upgraded and need an initializer; bind the salt to the deployer and parameters so a front-runner can't claim the address with other arguments. *Done in* Gas optimization.
- [x] P1 · extend · **Access control** with admin keys and governance: `Ownable2Step` makes the new owner accept, so a typo can't brick ownership; admin actions go through a **timelock** (plus a multisig) that gives users an exit window; flash-loan governance attacks (Beanstalk, April 2022, ~$182M) are stopped by snapshotting voting power at proposal creation (`ERC20Votes` checkpoints) and by voting delays. *Done as a separate concept,* Admin keys and governance.
- [x] P1 · extend · **Signature replay and malleability**: to accept signatures from smart-contract wallets (Safe, ERC-4337, 7702-delegated EOAs), verify through **`SignatureChecker`** (ECDSA or ERC-1271 `isValidSignature`); ERC-6492 wraps signatures from wallets not yet deployed.
- [x] P1 · new · *Security* › **Front-running and slippage**: public-mempool transactions can be front-run or sandwiched, so swap and liquidity functions take a `minAmountOut` and a `deadline` chosen off-chain (never derived on-chain from the manipulable spot price); commit-reveal for bids and games. MEV mechanics live in ethereum.md. Security reaches 9 concepts: split it into *Security* (reentrancy, access, signatures, randomness, DoS) and *Integration risks* (tokens, oracles, front-running, rounding). *Security is now split into* Security *and* Integration risks.
- [ ] P2 · new · *Gas optimization* › **Merkle allowlists**: store one root instead of a mapping and verify proofs with OpenZeppelin `MerkleProof`; **double-hash the leaves** so a 64-byte internal node can't pass as a leaf (second preimage); record claims in a bitmap to block double claims.
- [ ] P2 · extend · **Proxy storage and initializers**: legacy **storage gaps** (`uint256[50] __gap`) in upgradeable base contracts; shrink the gap by the slots you add. ERC-7201 namespaces replace them.
- [ ] P3 · new · *Security* › **Emergency controls**: `Pausable` with a guardian role, per-window outflow limits (bridges, lending) to cap losses during an exploit; pausing is itself a centralization risk to disclose.

**Trim** (keep the mechanism, drop the release number)

- [ ] cut · **Modifiers** bullet 4: `virtual` modifier deprecation (0.8.31).
- [ ] cut · **Libraries and user-defined types**: the `global` (0.8.13) and operator-binding (0.8.19) version details.
- [ ] cut · **Transient and relocated storage** bullet 3: `layout at` (0.8.29/0.8.35) is niche.
- [ ] cut · **Error types** bullet 4: the 0.8.26 vs 0.8.27 split for `require(cond, Error())`.
- [ ] cut · **Assembly gotchas** bullet 2's deprecated-comment clause, and **Gas optimization patterns** bullet 5's 0.8.22 note.
- [ ] cut · **Code size limit** bullet 3: EIP-7954 and Glamsterdam are still moving; re-add once shipped.
- [ ] cut · **Oracle integration** bullet 1: duplicate of ethereum.md (owner).
- [ ] cut · **Randomness and block data** bullet 4: the timestamp slot detail is minor.

### TypeScript

Good type-system depth. The biggest gap is the runtime boundary (types vanish), plus two assignability surprises.

**Add**

- [x] P1 · new · *Typing patterns* › **Runtime validation at boundaries**: types are erased, so `JSON.parse`, `res.json()`, env vars, and `as` casts yield unchecked data; parse with a schema library (Zod, Valibot, ArkType) and derive the type from the schema (`z.infer<typeof S>`) so the two can't drift; type untrusted input as `unknown`, not `any`.
- [x] P1 · new · *Type system semantics* › **`{}`, `object`, and index signatures**: **`{}` means any non-nullish value** (strings and numbers included), not "empty object"; `object` = any non-primitive; `Record<string, never>` is a truly empty object; an index signature makes every key "present" unless `noUncheckedIndexedAccess` is on.
- [x] P1 · new · *Type system semantics* › **Function assignability**: a function returning a value is assignable to one returning `void` (so `arr.forEach(x => out.push(x))` compiles); a function with fewer parameters is assignable to one with more (callbacks may ignore arguments).
- [ ] P2 · new · *Declarations and runtime features* › **`private` vs `#private`**: TS `private`, `protected`, and `readonly` are compile-time only, visible at runtime and reachable via `obj['x']`; ECMAScript `#x` is engine-enforced and hidden from `Object.keys` and JSON.
- [ ] P2 · new · *Narrowing* (rename "Narrowing and widening") › **Literal widening**: `let x = 'a'` is `string`, `const x = 'a'` is `'a'`; object literal properties widen (`{ kind: 'a' }` → `{ kind: string }`) unless `as const`, `satisfies`, or a contextual type applies; the usual cause of "string is not assignable to 'a' | 'b'".
- [ ] P2 · extend · **Conditional types**: `C<never>` distributes over an empty union and yields `never`, so test with `[T] extends [never]`; `infer U extends string` (4.7) constrains the inferred type.
- [ ] P2 · extend · **The `strict` family**: `useUnknownInCatchVariables` (in `strict` since 4.4) types `catch (e)` as `unknown`; narrow with `instanceof Error` before reading `.message`.
- [ ] P2 · extend · **Custom type guards**: a hand-written `x is T` isn't verified, so a wrong predicate lies to the compiler just like `as`.
- [ ] P2 · new · *Compilation and tooling* › **Project references and build speed**: `composite` projects built with `tsc -b` compile a monorepo incrementally in dependency order; slow checks come from huge unions, deep conditional types, and large inferred literals (`--extendedDiagnostics`, `--generateTrace`).

**Trim**

- [ ] merge · **Structural typing** (one definition-level bullet) into **Branded types**, which exists because of it.
- [ ] cut · **TypeScript 7 native compiler** bullet 2: tooling compatibility status will change within months.
- [ ] merge · **Exhaustiveness with `never`** (one bullet) into **Control-flow narrowing** (low confidence).

## Web

### Backend

Good API and reliability patterns. Missing schema evolution, tenancy, time handling, and service-to-service auth.

**Add**

- [x] P1 · new · *API design* › **Schema evolution**: **backward compatible** = new readers read old data, **forward compatible** = old readers read new data; Protobuf: never reuse or renumber a field (mark it `reserved`), adding fields is safe, proto3 has no `required`, unknown fields survive round trips; Avro + Schema Registry enforces BACKWARD/FORWARD/FULL modes; JSON consumers must ignore unknown fields (tolerant reader). *Done in* Service calls *instead, since API design already had 8.*
- [x] P1 · new · *Data access* › **Multi-tenancy models**: shared tables with a `tenant_id` (cheapest; every query must filter, so enforce it with PostgreSQL **row-level security**, which the table owner bypasses unless `FORCE ROW LEVEL SECURITY`) → schema per tenant → database per tenant (strongest isolation, per-tenant restore, most operations work); move noisy tenants to their own shard.
- [x] P1 · new · *Data access* › **Time handling**: store and send instants in UTC (RFC 3339 with an offset); for future local-time events (meetings, schedules) store the local time + an **IANA zone**, since offsets and DST rules change; a DST switch skips or repeats local times, so a 02:30 cron runs twice or never.
- [ ] P2 · new · *Service calls* › **Service-to-service authentication**: mTLS with workload identities (SPIFFE, a mesh), OAuth client credentials (short-lived JWTs with `aud`), or signed requests (HMAC, AWS SigV4); API keys are long-lived bearer secrets, so store them hashed, give them a scannable prefix, and rotate them. Mechanisms in security.md.
- [ ] P2 · extend · **Timeouts and deadline propagation**: a short connect timeout (~1 s) separate from the read or overall timeout; propagate the W3C `traceparent` header along with the deadline.
- [ ] P2 · new · *Lifecycle and config* › **Service internals**: hexagonal architecture (ports and adapters) keeps the domain free of framework and database imports; a DDD **aggregate** is the consistency and transaction boundary (one aggregate per transaction, others referenced by ID); **bounded contexts** map to service boundaries.
- [ ] P3 · new · *API design* › **Batch endpoints**: per-item results (207 Multi-Status or a result array), per-item idempotency, and a maximum batch size.
- [ ] P3 · extend · **Integration tests with real dependencies**: prefer fakes (working in-memory implementations) over mocks for stateful dependencies; mocks couple tests to call sequences.

**Trim**

- [ ] cut · **Resource modeling**: REST naming basics.
- [ ] cut · **Configuration and secrets**: 12-factor generics. Keep "validate config at startup" at most.
- [ ] cut · **File uploads** bullet 1: duplicates system.md. Keep the multipart/resumable bullet.
- [ ] cut · **Queue vs direct call**: system.md's **Queue semantics** covers it (low confidence).

### Frontend

Good breadth. Missing the React data-fetching and state-update gotchas that interviews probe, plus browser storage.

**Add**

- [x] P1 · new · *React hooks pitfalls* › **Data fetching in effects**: responses can arrive out of order, so ignore stale ones in cleanup (an `ignore` flag or `AbortController`); effect-based fetching causes **waterfalls** (parent fetch → child mounts → child fetch), so hoist fetching to route loaders or a query library; Strict Mode fires the request twice in development.
- [x] P1 · new · *React rendering model* › **State snapshots and keys**: state is a **snapshot** per render, so `setCount(count + 1)` twice adds 1 while `setCount(c => c + 1)` twice adds 2; changing a component's `key` resets its state; `useRef` holds mutable values without re-rendering.
- [x] P1 · new · *Caching* › **Browser storage**: cookies (~4 KB, sent with every request), `localStorage` (~5 MB per origin, **synchronous**, strings only), `sessionStorage` (per tab), **IndexedDB** (async, large, structured, available in workers), the Cache API (for service workers); any XSS can read all of them (tokens in security.md).
- [x] P1 · new · *React rendering model* › **Error boundaries**: they catch render and lifecycle errors in a subtree and show a fallback; still written as **class components** (or `react-error-boundary`); they don't catch errors in event handlers or async code.
- [ ] P2 · new · *React hooks pitfalls* › **useLayoutEffect vs useEffect**: `useEffect` runs after paint; `useLayoutEffect` runs after DOM mutation but **before paint**, for measuring layout without flicker, at the cost of blocking paint.
- [ ] P2 · extend · **Core Web Vitals**: rankings use **field data** (CrUX, p75 over 28 days, mobile and desktop separately); a page-load Lighthouse run is lab data and can't measure INP, so it reports TBT as a proxy.
- [ ] P2 · new · *Performance* › **Long lists**: **virtualize** (render only the visible rows: TanStack Virtual, react-window) beyond a few hundred complex rows; keep stable keys for infinite scroll.
- [ ] P2 · new · *State management* › **Context performance** (replaces **Where state lives**): every consumer re-renders when the provider `value` changes identity, so memoize it, split state and dispatch into separate contexts, or use a store with selectors (`useSyncExternalStore`).
- [ ] P2 · new · *Performance* › **Web fonts**: `font-display: swap` shows fallback text instead of invisible text but causes a swap shift; `size-adjust` and metric overrides reduce that CLS; preload the one critical font; subset and self-host.
- [ ] P2 · extend · **Semantic HTML and ARIA**: dynamic messages (toasts, form errors) need an **`aria-live`** region; every input needs a programmatic label; test with axe and a keyboard.
- [ ] P3 · new · *State management* › **Signals**: fine-grained reactivity (Solid, Preact, Vue, Angular signals) updates only the dependents without a VDOM diff; a TC39 Signals proposal exists.
- [ ] P3 · extend · **Service workers** (or new **bfcache**): the back/forward cache restores pages instantly; `unload` listeners make a page ineligible, so use `pagehide`.
- [ ] P3 · new · *Accessibility* (rename "Accessibility and testing") › **Frontend testing**: Testing Library queries by role and label (tests behavior and rewards accessible markup); MSW mocks the network layer; Playwright covers end-to-end flows.

**Trim**

- [ ] cut · **CSS layout and specificity** bullet 1: flexbox vs grid basics.
- [ ] cut · **Modern CSS features**: feature listing and Baseline status. Keep container queries and `:has()`.
- [ ] cut · **View transitions** bullet 2: Baseline status details go stale.
- [ ] cut · **Where state lives**: generic advice (replaced by Context performance).
- [ ] cut · **Controlled vs uncontrolled inputs**: basic React (low confidence).

### Security

Strong. Missing a few browser-policy nuances, randomness, account recovery, and denial-of-service classes. Server-side attacks would reach 9 concepts: split it into *Injection* (SQL, command/template/XXE, deserialization, prototype pollution) and *Server-side request and resource attacks* (SSRF, smuggling, path traversal, resource exhaustion, race conditions, file uploads).

**Add**

- [x] P1 · extend · **CORS**: **simple requests** (GET, HEAD, or POST with form or `text/plain` bodies and no custom headers) go out without a preflight, and the server acts on them even when the browser hides the response, so CORS is no CSRF defense; everything else preflights with `OPTIONS`, cached by `Access-Control-Max-Age`.
- [x] P1 · new · *Cryptography* › **Secure randomness**: tokens, IDs, nonces, and reset codes need a **CSPRNG** (`crypto.getRandomValues`/`randomBytes`, Python `secrets`, Go `crypto/rand`); `Math.random`, `random`, and `math/rand` are predictable from a few outputs; use ≥ 128 bits for unguessable tokens.
- [x] P1 · new · *Authentication and sessions* › **Password reset and recovery**: single-use, short-lived, high-entropy tokens stored **hashed**; revoke other sessions after a reset; identical responses whether or not the account exists; build reset links from a configured origin, not the `Host` header (host-header poisoning); recovery is often the weakest login path (SIM swap, support desk).
- [x] P1 · new · *Server-side attacks* › **Resource-exhaustion attacks**: **ReDoS** (catastrophic backtracking on patterns like `(a+)+$`; use linear-time engines such as RE2 or Go's `regexp`, or timeouts), decompression and zip bombs (cap the output size), XML billion laughs, hash flooding (randomized hash seeds), unbounded JSON or GraphQL depth.
- [ ] P2 · extend · **CSRF**: "same-site" means same scheme + **registrable domain** (eTLD+1), so `evil.example.com` is same-site with `app.example.com` and SameSite doesn't stop attacks from a compromised or user-controlled subdomain; `Lax` still sends cookies on top-level GET navigations, so never change state on GET.
- [ ] P2 · new · *TLS* › **SNI, ALPN, ECH**: **SNI** carries the hostname in the ClientHello, so one IP serves many certificates and L4 proxies can route TLS without terminating it; **ALPN** negotiates `h2`/`http/1.1` in the handshake; **ECH** encrypts the inner ClientHello, hiding SNI from the network.
- [ ] P2 · new · *TLS* › **Certificate lifecycle**: the CA/Browser Forum (2025) cuts the maximum certificate lifetime to 200 days (March 2026), 100 days (2027), and **47 days (2029)**, so automate with ACME; revocation checking is weak (Let's Encrypt shut down OCSP in 2025), so short lifetimes do the work; monitor Certificate Transparency logs for your domains.
- [ ] P2 · extend · **Browser token storage**: current guidance for SPAs is a **BFF**: the backend runs the OAuth flow and keeps the tokens, and the browser gets only an `HttpOnly` session cookie.
- [ ] P2 · new · *Cryptography* › **Cipher modes and broken hashes**: **ECB** leaks patterns (equal blocks → equal ciphertext); CBC without a MAC enables **padding-oracle** decryption; use an AEAD (AES-GCM, ChaCha20-Poly1305); MD5 and SHA-1 are broken for collisions.
- [ ] P2 · new · *Supply chain* › **Secrets management**: prefer short-lived, dynamically issued credentials (Vault, cloud IAM) over static keys; scan commits and block pushes containing secrets; a leaked secret must be rotated, since deleting the commit doesn't un-leak it; env vars leak through `/proc/<pid>/environ`, crash dumps, and child processes.
- [ ] P2 · new · *Server-side attacks* › **Race-condition attacks**: limit-overrun bugs, such as redeeming a coupon or withdrawing twice with parallel requests (HTTP/2's single-packet attack lands them within ~1 ms); fix with atomic conditional updates, unique constraints, or row locks.
- [ ] P2 · extend · **XSS**: frameworks escape text, but `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `javascript:` URLs in `href`, and template `|safe` filters bypass it; **Trusted Types** make DOM sinks reject plain strings.
- [ ] P2 · new · *Server-side attacks* › **File upload handling**: check the type by content (magic bytes), not the extension or `Content-Type`; store files outside the web root under generated names; serve user files from a separate sandbox domain with `Content-Disposition: attachment` and `nosniff`; re-encode images.
- [ ] P3 · new · *Browser-side attacks* › **Web cache poisoning and deception**: an unkeyed header (`X-Forwarded-Host`) reflected into a cached page poisons it for everyone; cache deception tricks a CDN into caching a private page under a static-looking path (`/account/x.css`).
- [ ] P3 · new · *Browser-side attacks* › **Subdomain takeover**: a dangling CNAME to a deleted cloud resource lets an attacker claim it, and the subdomain is same-site for your cookies.
- [ ] P3 · extend · **OAuth 2.0 vs OIDC**: SAML still dominates enterprise SSO; XML signature-wrapping bugs are its classic flaw.

**Trim**

- [ ] cut · **Encoding vs encryption vs hashing**: definition-level table.
- [ ] merge · **Clickjacking** into **Content Security Policy** (`frame-ancestors`) (low confidence).
- [ ] cut · **OWASP Top 10:2025**: keep only if you expect "name the list" questions (low confidence).

## Infrastructure

### AWS

Compact and accurate. Missing the load balancer choice, cross-account access, S3 and CloudFront access control, and where the money goes.

**Add**

- [x] P1 · new · *Networking* › **ALB vs NLB** (table): ALB is L7 (host, path, and header routing; WebSockets; gRPC; OIDC auth; WAF); NLB is L4 TCP/UDP/TLS with a **static IP per AZ**, preserves the client IP, supports TLS passthrough and very high throughput, and fronts PrivateLink services; GWLB is for inline appliances; cross-zone balancing is on for ALB and off by default for NLB (cross-AZ charges).
- [x] P1 · new · *Identity and access* › **Cross-account access**: within one account, an allow in the identity **or** the resource policy suffices (KMS key policies and role trust policies excepted); across accounts **both** sides must allow; third parties assume your role with an **`sts:ExternalId`** condition (confused deputy); `aws:PrincipalOrgID` limits resource policies to your organization.
- [x] P1 · new · *Storage and databases* › **S3 access and CloudFront**: new buckets block public access and disable ACLs ("bucket owner enforced") since April 2023, and encrypt with SSE-S3 since January 2023; serve private buckets through CloudFront with **Origin Access Control**; signed URLs or cookies for private content at the edge.
- [x] P1 · extend · **Capacity and cost guardrails** (or new **Cost drivers**): NAT gateway data processing (~$0.045/GB; add S3/DynamoDB gateway endpoints), **cross-AZ traffic** (~$0.01/GB each way), internet egress, CloudWatch Logs ingestion; Savings Plans and RIs (up to ~72% off for 1–3 year commitments), Spot (up to ~90% off), Graviton (~20% cheaper). *Done as a new concept,* Cost drivers, *in Operations.*
- [ ] P2 · extend · **Managed database behavior**: **RDS Proxy** pools connections for Lambda bursts (each concurrent environment opens its own) and shortens failover; read replicas are asynchronous.
- [ ] P2 · new · *Events and workflows* › **Streams with Lambda**: Kinesis and DynamoDB Streams deliver in order per shard, so one failing record **blocks the shard** until it expires; set `BisectBatchOnFunctionError`, `MaximumRetryAttempts`, and an on-failure destination; a Kinesis shard takes 1 MB/s or 1,000 records/s in and 2 MB/s out; DynamoDB Streams keep 24 h; async Lambda invocations retry twice.
- [ ] P2 · new · *Compute* › **EC2 Auto Scaling**: target tracking (hold a metric such as requests per target) over step or scheduled policies; a health check grace period; lifecycle hooks for bootstrap and drain; warm pools for fast scale-out; T instances drop to baseline CPU when their credits run out (`unlimited` mode bills instead).
- [ ] P2 · extend · **DynamoDB partitions and indexes**: conditional writes (`ConditionExpression`, a version attribute) for optimistic locking and create-if-absent; on-demand vs provisioned capacity; single-table design keys items by access pattern.
- [ ] P2 · new · *Identity and access* › **Multi-account structure**: Organizations and OUs; SCPs cap member accounts' permissions (not the management account's); IAM Identity Center for human SSO; separate accounts per environment or workload as blast-radius and billing boundaries.
- [ ] P2 · extend · **Infrastructure changes and secrets**: Parameter Store's standard tier is free (4 KB values, no managed rotation); Secrets Manager charges per secret and adds rotation and cross-Region replication.
- [ ] P3 · extend · **Public and private subnets**: AZ names (`us-east-1a`) map to different physical AZs per account; align across accounts with AZ IDs (`use1-az1`).
- [ ] P3 · new · *Operations* › **Disaster recovery services**: the tiers live in system.md; here the AWS pieces: AWS Backup, S3 cross-Region replication, Aurora Global Database (typically < 1 s lag), DynamoDB global tables, Route 53 failover.
- [ ] P3 · new · *Networking* › **EKS Pod networking**: the VPC CNI gives every Pod a VPC IP, which exhausts subnets; use prefix delegation or secondary CIDRs.

**Trim**

- [ ] cut · **ECS service mechanics**: definitions (task definition, service).
- [ ] cut · **Lambda limits and concurrency** bullet 2: Managed Instances' 90-minute limit is new and niche (low confidence).
- [ ] cut · **Capacity and cost guardrails** bullet 2: Budgets vs Cost Explorer trivia.
- [ ] cut · **KMS and envelope encryption** bullet 1's re-explanation (owner: security). Keep `GenerateDataKey` and the 4 KB limit.

### DevOps

Good Kubernetes and Terraform coverage. Missing workload security, a key Terraform gotcha, autoscaling mechanics, and the delivery and incident practices DevOps interviews ask about. Kubernetes operations already has 8 concepts: move ServiceAccounts, ConfigMaps and Secrets, and NetworkPolicy into a new *Kubernetes security* section (with Pod security below), and Packaging and extension into *Kubernetes architecture*.

**Add**

- [x] P1 · new · *Kubernetes security* › **Pod security**: Pod Security Admission levels (privileged, baseline, **restricted**) per namespace, since PodSecurityPolicy was removed in 1.25; `securityContext`: `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, drop all capabilities, `seccompProfile: RuntimeDefault`; Kyverno or OPA Gatekeeper for custom policy. *Kubernetes security holds Pod security, ServiceAccounts, ConfigMaps and Secrets; NetworkPolicy stays in Kubernetes networking; Packaging and extension moved to Kubernetes architecture.*
- [x] P1 · new · *Terraform* › **count vs for_each**: `count` addresses resources by index, so removing one element shifts every later index and **recreates** those resources; `for_each` keys them by stable map or set keys.
- [x] P1 · extend · **Autoscaling**: HPA utilization is a percentage of **requests**, so without requests there's no CPU-based scaling; scale-down waits out a 5-minute stabilization window; **KEDA** scales on queue length or events, down to zero; Karpenter provisions right-sized nodes and consolidates underused ones.
- [x] P1 · new · *Deployment and release* › **Incident response**: roles (incident commander, communications, operations); **mitigate first** (roll back, flip a flag), find the root cause later; a blameless postmortem with a timeline, contributing factors, and owned action items; track MTTD and MTTR; link runbooks from alerts.
- [ ] P2 · new · *CI/CD and GitOps* › **DORA metrics**: deployment frequency, lead time for changes, change failure rate, failed-deployment recovery time; high performers improve speed and stability together; recent reports add rework rate.
- [ ] P2 · extend · **Deployment strategies** table: **shadow** (mirror live traffic to the new version and discard its responses; watch for side effects); A/B tests split by user for product metrics, not safety; Argo Rollouts and Flagger automate canary analysis.
- [ ] P2 · new · *Kubernetes workloads* › **Jobs and CronJobs**: `backoffLimit`, `activeDeadlineSeconds`, `ttlSecondsAfterFinished`; `concurrencyPolicy: Forbid` prevents overlapping runs; schedules use the controller's time zone (usually UTC) unless `timeZone` (GA 1.27) is set.
- [ ] P2 · new · *Kubernetes operations* › **Cluster upgrades**: control plane first, one minor version at a time; kubelets may lag the API server by up to 3 minor versions (since 1.28); drain nodes (PDBs apply) or roll new node groups; check for removed APIs first; each minor release gets ~14 months of patches.
- [ ] P2 · new · *Kubernetes operations* › **Quotas and priority**: `ResourceQuota` caps a namespace's total requests, limits, and object counts; `LimitRange` sets defaults for Pods without requests; `PriorityClass` lets critical Pods **preempt** others when the cluster is full.
- [ ] P2 · extend · **CI pipeline practices**: `pull_request_target` workflows that check out PR code run it with secrets (a "pwn request"); least-privilege `GITHUB_TOKEN`; OIDC to the cloud instead of stored keys; no untrusted PRs on self-hosted runners.
- [ ] P3 · new · *Deployment and release* › **Chaos engineering**: state a steady-state hypothesis, inject a failure (instance, AZ, latency) with a small blast radius, and compare against SLOs; game days rehearse incident response.
- [ ] P3 · new · *Terraform* › **Mutable vs immutable infrastructure**: configuration management (Ansible) patches servers in place and drifts; immutable images (Packer, containers) replace them.

**Trim**

- [ ] cut · **Container networking and storage**: Docker basics (`EXPOSE` vs `-p`, volumes vs bind mounts).
- [ ] cut · **Modules, workspaces, licensing** bullet 3: license history. Keep "OpenTofu is the open fork" (low confidence).
- [ ] cut · **Node components** bullet 3: kube-proxy modes by version (low confidence).
- [ ] cut · **Workload types**: definition-level for Kubernetes users. Keep "never run a bare Pod" (low confidence).

## Domains

### AI Engineering

Strong on inference, serving, RAG, and agents. Missing how models are trained (including reasoning models), multi-GPU serving, and filtered retrieval. LLM fundamentals already has 8 concepts: move **Structured output** and **Tool calling** into *Tools and integration* to make room.

**Add**

- [x] P1 · new · *Fine-tuning* (rename "Training and fine-tuning") › **Training pipeline**: **pretraining** (next-token prediction on trillions of tokens; Chinchilla-optimal is ≈ 20 tokens per parameter, and modern models train far past it to be cheaper at inference) → SFT → preference tuning (RLHF, DPO) → **RL with verifiable rewards** (math and code graded automatically, e.g., GRPO), which is how reasoning models learn long chains of thought.
- [x] P1 · new · *Inference and serving* › **Model parallelism and GPU memory**: memory ≈ weights + KV cache + activations; **tensor parallelism** splits each layer across GPUs (needs NVLink-class links, so within a node); **pipeline parallelism** splits layers across nodes (pipeline bubbles); data parallelism replicates for throughput; **disaggregated serving** runs prefill and decode on separate GPU pools.
- [x] P1 · extend · **Vector index types**: **filtered search**. Post-filtering the top-k returns too few hits for selective filters, and pre-filtering breaks HNSW graph connectivity; use filter-aware engines or partition indexes by tenant.
- [ ] P2 · new · *LLM fundamentals* › **Positional encoding**: attention is order-blind; **RoPE** rotates query and key vectors by position so scores depend on relative distance; longer contexts come from RoPE scaling (position interpolation, YaRN) plus long-context training, and quality degrades past the trained length.
- [ ] P2 · new · *Fine-tuning* › **Distillation**: train a small student on a large teacher's outputs or logits for most of the quality at a fraction of the serving cost (also how small reasoning models are made); fine-tuning can cause catastrophic forgetting, which LoRA limits by freezing the base.
- [ ] P2 · extend · **Eval sets and metrics**: **pass@k** for code and agent tasks (the probability that at least one of k samples passes); precision/recall (PR-AUC when labels are imbalanced) for classifier-style checks; public benchmarks suffer from contamination.
- [ ] P2 · new · *Retrieval and RAG* › **Query transformation**: rewrite follow-ups into standalone queries; **HyDE** embeds a hypothetical answer instead of the question; decompose multi-hop questions; extract metadata filters (dates, product) from the query.
- [ ] P2 · extend · **Prompt injection**: jailbreaks (the user attacks the model's policy) vs prompt injection (third-party content attacks your application) are different threat models with different defenses.
- [ ] P2 · extend · **Batching and PagedAttention**: bigger batches raise tokens/s per GPU but also time per output token, so the latency SLO sets the batch size.
- [ ] P3 · new · *LLM fundamentals* › **Attention variants**: sliding-window attention, multi-head latent attention (DeepSeek; compresses the KV cache), and state-space or linear-attention hybrids (Mamba) with constant memory per token.
- [ ] P3 · extend · **Embeddings and similarity**: Matryoshka embeddings truncate to fewer dimensions; int8 or binary quantized vectors shrink the index 4–32×, then the top candidates are rescored at full precision.
- [ ] P3 · new · *Evaluation* › **Classic ML basics** (only for ML-adjacent roles): bias–variance and overfitting, regularization, train/validation/test splits and leakage, ROC-AUC vs PR-AUC.

**Trim**

- [ ] cut · **Browser automation as a fallback**: generic. Move "approve irreversible submits" into **Human approval gates**.
- [ ] cut · **Model routing and caching** bullet 3: "measure cost per completed task" is generic (low confidence).
- [ ] cut · **Stop conditions** bullet 2: generic (low confidence).

### Ethereum

Good protocol coverage. Missing precompiles, node and RPC practicalities, ZK proof systems, and EIP-7702's risks.

**Add**

- [x] P1 · new · *EVM* › **Precompiles**: fixed low addresses for cryptography too costly in bytecode: `0x01` ecrecover, `0x02` SHA-256, `0x05` modexp, `0x06`–`0x08` BN254 add/mul/pairing (SNARK verifiers), `0x0a` KZG point evaluation (EIP-4844), **BLS12-381** (Pectra, EIP-2537), **P-256** verification (Fusaka, EIP-7951; passkey wallets); they have no code, so `extcodesize` is 0.
- [x] P1 · new · *Accounts and transactions* › **RPC block tags and reorgs**: `latest` can reorg, **`safe`** (justified) rarely does, and **`finalized`** can't without slashing ⅓ of the stake; `eth_call` simulates against a block; `eth_estimateGas` binary-searches and can underestimate state-dependent paths, so add headroom; indexers store block hashes and roll back on reorg, or index only finalized blocks.
- [x] P1 · new · *Scaling* › **ZK proof systems**: **SNARKs** (Groth16, PLONK) have small proofs, cheap L1 verification via BN254 pairings, and often a trusted setup; **STARKs** need no trusted setup, are hash-based (plausibly post-quantum), and have larger proofs, often wrapped in a SNARK for L1; zkEVM types trade Ethereum equivalence against proving cost.
- [x] P1 · extend · **Account abstraction**: EIP-7702 risks. One authorization signature hands the EOA to the delegate's code (a phishing target); an authorization with `chain_id = 0` is valid on **every chain**; the delegate's storage lives in the EOA, so switching delegates can collide layouts (use namespaced storage).
- [ ] P2 · new · *Consensus (PoS)* › **Execution and consensus clients**: since the Merge a node = execution client (Geth, Nethermind, Besu, Erigon, Reth) + consensus client (Prysm, Lighthouse, Teku, Nimbus, Lodestar) linked by the authenticated **Engine API**; a bug in a client with > ⅔ of the stake could finalize an invalid chain, hence client diversity; full vs archive nodes.
- [ ] P2 · extend · **Transaction lifecycle**: a replacement needs the same nonce and ≥ 10% higher fees (Geth's default; 100% for blob transactions); private RPCs (Flashbots Protect) skip the public mempool.
- [ ] P2 · new · *Scaling* › **L2 fees and messaging**: an L2 fee = L2 execution + the **L1 data fee** (blob or calldata cost, usually the larger part); deposits through the canonical bridge can be force-included; withdrawals wait for the fraud window or a validity proof; L2BEAT stages 0–2 grade how much users rely on a security council vs proofs.
- [ ] P2 · new · *Consensus (PoS)* › **Validator lifecycle**: deposit → activation queue → active → exit queue → withdrawable (the churn limit rate-limits entries and exits); withdrawal credentials `0x01` (balance above 32 ETH swept) vs `0x02` compounding (Pectra); liquid staking (stETH) and restaking (EigenLayer) add contract and slashing risk.
- [ ] P2 · new · *Consensus (PoS)* › **Network upgrades** (table): Merge (Sep 2022, PoS) → Shapella (Apr 2023, withdrawals) → Dencun (Mar 2024, blobs, transient storage, EIP-6780) → Pectra (May 2025, 7702, 7251, 7623, BLS) → Fusaka (Dec 2025, PeerDAS, 7825, P-256) → Glamsterdam (planned: ePBS, block-level access lists).
- [ ] P2 · new · *DeFi and MEV* › **Bridge designs**: canonical rollup bridges (inherit L1 security, slow withdrawals), external validator or multisig bridges (fast, trust a committee, e.g., Ronin), light-client and ZK bridges, liquidity networks and intents (fast; LPs front the funds).
- [ ] P3 · new · *Signatures and standards* › **Wallet keys**: BIP-39 mnemonic → BIP-32 HD tree → path `m/44'/60'/0'/0/i`; MPC wallets split one key for threshold signing, vs multisig (on-chain M-of-N, visible, deployed per chain).
- [ ] P3 · extend · **Blobs and PeerDAS**: blob gas has its own EIP-1559-style base fee with a per-block target and max; EIP-7918 (Fusaka) ties the blob base fee floor to the execution base fee.
- [ ] P3 · new · *DeFi and MEV* › **Stablecoin designs**: fiat-backed (USDC; the issuer can freeze), overcollateralized crypto-backed (DAI), algorithmic (UST's 2022 death spiral).

**Trim**

- [ ] cut · **Bridge exploits**: historical hack list. Keep one lesson per incident, or fold it into Bridge designs (low confidence).
- [ ] cut · **Account model** bullet 1: definition-level for Ethereum roles (low confidence).
