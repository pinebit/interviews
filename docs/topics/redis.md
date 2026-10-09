# Redis

What experienced Redis users forget before an interview, grouped by subtopic. For caching strategies and rate-limiting algorithms, see [system.md](system.md); for Redlock and delivery semantics, see [distributed.md](distributed.md).

## Execution model

### Single-threaded execution

- Commands execute one at a time on the main thread, so each command is atomic and needs no locks.
- One slow command ([`KEYS *`](https://redis.io/docs/latest/commands/keys/), `SMEMBERS` on a huge set, `DEL` of a big key) blocks every other client for its duration.
- [I/O threads](https://redis.io/docs/latest/operate/oss_and_stack/management/config-file/) (`io-threads`, since 6.0; rewritten in 8.0) parse requests and write replies; commands still run on the main thread. Off by default.
- Scale CPU-bound workloads with more shards (Cluster), not bigger machines.

### Slow and blocking operations

- [`SCAN`](https://redis.io/docs/latest/commands/scan/) iterates with a cursor instead of `KEYS`; it can return a key twice and only [guarantees](https://redis.io/docs/latest/commands/scan/#scan-guarantees) keys present for the whole iteration; `COUNT` is a hint.
- [`UNLINK`](https://redis.io/docs/latest/commands/unlink/) (4.0+) frees a big value in a background thread; `DEL` frees it synchronously unless `lazyfree-lazy-user-del yes`.
- [`SLOWLOG`](https://redis.io/docs/latest/commands/slowlog/) records commands slower than 10 ms by default, counting execution time only, not network or queueing.
- Find offenders with `redis-cli --bigkeys` / `--memkeys`, and since 8.6 the [`HOTKEYS`](https://redis.io/docs/latest/commands/hotkeys/) command.

### Pipelines, transactions, and scripts

| | Atomic | Round trips | Can branch on read values |
|---|---|---|---|
| [Pipeline](https://redis.io/docs/latest/develop/using-commands/pipelining/) | no — other clients' commands interleave | one per batch | no |
| [`MULTI`/`EXEC`](https://redis.io/docs/latest/develop/using-commands/transactions/) | yes | one per batch when pipelined | no; `WATCH` aborts on change |
| [Lua script](https://redis.io/docs/latest/develop/programmability/eval-intro/) or [function](https://redis.io/docs/latest/develop/programmability/functions-intro/) | yes | one | yes |

### MULTI/EXEC and WATCH

- [Transactions](https://redis.io/docs/latest/develop/using-commands/transactions/) don't roll back: a command that fails at run time (wrong type) leaves the others applied; an error while queuing (bad syntax) aborts the whole `EXEC`.
- [`WATCH`](https://redis.io/docs/latest/commands/watch/) makes `EXEC` return null if a watched key changed — an optimistic check-and-set; retry the read-modify-write loop.
- In Cluster, every key in the transaction must hash to the same slot.

### Lua scripts and functions

- A [script](https://redis.io/docs/latest/develop/programmability/eval-intro/) runs without interleaving but doesn't roll back: a runtime error keeps the writes made before it.
- A long script blocks everyone: past [`busy-reply-threshold`](https://redis.io/docs/latest/develop/programmability/#maximum-execution-time) (5 s) other clients get `BUSY`, and `SCRIPT KILL` works only if it hasn't written yet — otherwise `SHUTDOWN NOSAVE`.
- `EVALSHA` runs a cached script by hash; the cache isn't persisted, so clients must handle `NOSCRIPT` by resending the source.
- [Functions](https://redis.io/docs/latest/develop/programmability/functions-intro/) (7.0+) are named libraries loaded once with `FUNCTION LOAD` and called with `FCALL`; they're persisted and replicated like data.
- Pass every key the script touches in `KEYS`, so Cluster can route it and check slots.

## Data structures

### Core types

| Type | Encoding when large | Typical use |
|---|---|---|
| [String](https://redis.io/docs/latest/develop/data-types/strings/) (≤ 512 MB) | raw bytes or integer | cache values, counters (`INCR`), locks |
| [Hash](https://redis.io/docs/latest/develop/data-types/hashes/) | hash table | objects with per-field updates; per-field TTL since 7.4 |
| [List](https://redis.io/docs/latest/develop/data-types/lists/) | quicklist (linked listpacks) | queues, recent items; index access is O(n) |
| [Set](https://redis.io/docs/latest/develop/data-types/sets/) | hash table | membership, tags, intersections |
| [Sorted set](https://redis.io/docs/latest/develop/data-types/sorted-sets/) | [skip list](https://en.wikipedia.org/wiki/Skip_list) + hash table | leaderboards, sliding-window limiters, delay queues |
| [Stream](https://redis.io/docs/latest/develop/data-types/streams/) | radix tree of listpacks | append-only event log with consumer groups |

### Compact encodings

- Small collections use a flat [listpack](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/): hashes up to 512 fields, sets and sorted sets up to 128 members, values ≤ 64 bytes; integer-only sets up to 512 use an intset.
- Crossing a threshold converts the key to a hash table or skip list, which takes several times the memory; [`OBJECT ENCODING`](https://redis.io/docs/latest/commands/object-encoding/) shows the current form.
- Many small hashes beat millions of top-level keys: each key costs tens of bytes of overhead.

### Sorted set details

- [`ZADD`](https://redis.io/docs/latest/commands/zadd/), `ZRANK`, `ZREM` are O(log n); `ZSCORE` is O(1) via the hash; range by rank or score is O(log n + m).
- Scores are 64-bit floats: integers are exact only up to 2^53, so don't pack large IDs into scores.
- Members with equal scores sort lexicographically; `ZRANGE ... BYLEX` works only when every member has the same score.

### Probabilistic and specialized types

- [HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/) counts distinct items in 12 KB with 0.81% standard error; `PFMERGE` unions them.
- [Bitmaps](https://redis.io/docs/latest/develop/data-types/bitmaps/) are bit operations on strings — one bit per user ID for daily actives.
- [Geo](https://redis.io/docs/latest/develop/data-types/geospatial/) commands store geohashes as sorted-set scores and search by radius or box.
- Since 8.0, the former Redis Stack modules ship built in: [JSON](https://redis.io/docs/latest/develop/data-types/json/), time series, Bloom and Cuckoo filters, count-min sketch, top-k, t-digest, vector sets, and the query engine.

## Expiration and eviction

### Key expiration

- A [TTL](https://redis.io/docs/latest/commands/expire/) belongs to the key; [`SET`](https://redis.io/docs/latest/commands/set/) without `KEEPTTL` clears it, while `INCR`, `HSET`, or `LPUSH` keep it.
- Per-field TTLs on hashes ([`HEXPIRE`](https://redis.io/docs/latest/commands/hexpire/)) exist since 7.4; before that, expiry was whole-key only.
- [Expired keys](https://redis.io/docs/latest/commands/expire/#how-redis-expires-keys) are deleted lazily on access plus by a background sampler, so memory lags behind expirations.
- Replicas don't expire keys themselves; they wait for the primary's `DEL`, but reads of a logically expired key already return nothing.

### Eviction policies

- [`maxmemory`](https://redis.io/docs/latest/develop/reference/eviction/#maxmem) is 0 (unlimited) by default on 64-bit, so an unbounded cache grows until the kernel OOM killer steps in.
- [`maxmemory-policy`](https://redis.io/docs/latest/develop/reference/eviction/#eviction-policies) defaults to `noeviction`: at the limit, writes fail with an OOM error while reads continue.
- Caches use `allkeys-lru` or `allkeys-lfu`; `allkeys-lrm`/`volatile-lrm` (8.6+) evict the least recently modified keys.
- `volatile-*` policies evict only keys with a TTL, so without TTLs they behave like `noeviction`.
- Leave headroom: replication and AOF buffers aren't counted against `maxmemory`.

### Approximated LRU and LFU

- [LRU](https://redis.io/docs/latest/develop/reference/eviction/#apx-lru) is approximated: evict the oldest of `maxmemory-samples` (5) random keys, helped by a pool of good candidates; 10 samples is close to true LRU.
- [LFU](https://redis.io/docs/latest/develop/reference/eviction/#lfu-eviction) keeps an 8-bit logarithmic (Morris) counter per key that decays every minute (`lfu-decay-time 1`), so formerly hot keys age out.

## Persistence

### RDB snapshots

- [RDB](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) forks; the child writes a point-in-time snapshot while the parent keeps serving, sharing memory [copy-on-write](https://en.wikipedia.org/wiki/Copy-on-write).
- Under heavy writes the fork can approach 2× memory; set [`vm.overcommit_memory = 1`](https://redis.io/docs/latest/operate/oss_and_stack/management/admin/) and disable transparent huge pages — fork and overcommit in [os.md](os.md).
- Default save points: after 1 hour with ≥ 1 change, 5 min with ≥ 100, 1 min with ≥ 10,000 — everything since the last snapshot is lost on a crash.
- `stop-writes-on-bgsave-error yes` (default) rejects writes after a failed snapshot.

### AOF

- [AOF](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/#append-only-file) logs every write; it's off by default (`appendonly no`) and, when on, takes precedence over RDB at startup.
- `appendfsync`: `always` (slow, safest), `everysec` (default, loses up to ~1 s), `no` (the OS decides, ~30 s on Linux).
- A rewrite (`BGREWRITEAOF`) forks to compact the log; since 7.0 the AOF is [multi-part](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/#log-rewriting) — an RDB-format base file plus incremental files and a manifest.
- A pure cache can run without persistence; even with AOF, async replication still loses writes on failover.

## Replication and high availability

### Replication

- [Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/) is asynchronous: the primary acknowledges writes before replicas have them.
- A reconnecting replica resumes with `PSYNC` (replication ID + offset) if the gap still fits the replication backlog (1 MB default); otherwise it does a full resync — a fork and an RDB transfer.
- [`WAIT`](https://redis.io/docs/latest/commands/wait/) blocks until n replicas acknowledge, and [`WAITAOF`](https://redis.io/docs/latest/commands/waitaof/) (7.2+) until they fsync; both shrink the loss window but don't make Redis strongly consistent.
- `min-replicas-to-write` (off by default) rejects writes when fewer replicas than that acknowledged within `min-replicas-max-lag` seconds, limiting what an isolated primary accepts.
- A primary with persistence off that auto-restarts comes back empty, and its replicas [sync to the empty dataset](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/#safety-of-replication-when-master-has-persistence-turned-off).

### Sentinel

- [Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/) monitors a primary, promotes a replica on failure, and tells clients the new primary; run at least 3 on independent hosts.
- The `quorum` sets how many Sentinels must agree the primary is down; the failover itself still needs a majority of Sentinels.
- Clients must be Sentinel-aware and ask it for the current primary, not cache the address.
- Acknowledged writes not yet replicated are lost on failover, and an old primary on the minority side keeps accepting writes unless `min-replicas-to-write` is set and it loses sight of enough replicas.

## Cluster

### Hash slots

- [Redis Cluster](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) splits keys into 16,384 slots (`CRC16(key) mod 16384`); each primary owns a range.
- [Hash tags](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/#hash-tags) hash only the part in braces, so `{user42}:cart` and `{user42}:orders` share a slot.
- Multi-key commands, transactions, and scripts need all keys in one slot, else `CROSSSLOT`; only database 0 exists.

### Redirections and resharding

- [`MOVED`](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/#moved-redirection): the slot lives elsewhere — the client updates its slot map. [`ASK`](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/#ask-redirection): the slot is mid-migration — retry once on the target after `ASKING`, without updating the map.
- Smart clients cache the slot map ([`CLUSTER SHARDS`](https://redis.io/docs/latest/commands/cluster-shards/)) and refresh it on `MOVED`.
- Since 8.4, [`CLUSTER MIGRATION`](https://redis.io/docs/latest/commands/cluster-migration/) moves whole slots atomically instead of key by key with `ASK` redirects.

### Cluster failure handling

- Nodes gossip over the cluster bus (data port + 10000); a primary unreachable for [`cluster-node-timeout`](https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/#redis-cluster-configuration-parameters) (15 s) is marked failed by a majority of primaries, and one of its replicas is promoted.
- [Not strongly consistent](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/#write-safety): async replication loses acknowledged writes, and a primary on the minority side of a partition accepts writes until the node timeout.
- With `cluster-require-full-coverage yes` (default), the whole cluster stops serving if any slot has no live owner.

## Messaging

### Pub/sub

- [Pub/sub](https://redis.io/docs/latest/develop/pubsub/) is fire-and-forget: a disconnected subscriber misses messages for good.
- A slow subscriber is disconnected once its output buffer exceeds 32 MB, or 8 MB for 60 s.
- In Cluster, `PUBLISH` is broadcast to every node; [sharded pub/sub](https://redis.io/docs/latest/develop/pubsub/#sharded-pubsub) (`SPUBLISH`, 7.0+) keeps a channel on its slot's shard.
- [Keyspace notifications](https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/) are off by default and travel over pub/sub, so they're lossy too.

### Streams

- [`XADD`](https://redis.io/docs/latest/commands/xadd/) appends entries with time-based IDs (`<ms>-<seq>`); [`XREADGROUP`](https://redis.io/docs/latest/commands/xreadgroup/) gives each entry to one consumer in a group.
- Delivered entries sit in the pending entries list until [`XACK`](https://redis.io/docs/latest/commands/xack/) — at-least-once delivery.
- A crashed consumer's entries are taken over with [`XAUTOCLAIM`](https://redis.io/docs/latest/commands/xautoclaim/) (6.2+) or `XREADGROUP ... CLAIM` (8.4+); [`XNACK`](https://redis.io/docs/latest/commands/xnack/) (8.8+) releases them explicitly.
- Streams grow until trimmed: `XADD ... MAXLEN ~ n` trims approximately and cheaply.
- Since 8.6, `XADD ... IDMP` deduplicates producer retries.

### Lists as queues

- `LPUSH` + [`BRPOP`](https://redis.io/docs/latest/commands/brpop/) is the simplest queue, but a worker crash after the pop loses the job.
- Reliable queue: [`BLMOVE`](https://redis.io/docs/latest/commands/blmove/) (6.2+) atomically moves the job to a per-worker processing list; remove it after success, re-queue stale ones.
- Prefer Streams when you need acknowledgments, replay, or several consumer groups; Kafka-style logs in [system.md](system.md).

## Common patterns

### Distributed locks

- Acquire with [`SET lock:k <random token> NX PX 30000`](https://redis.io/docs/latest/commands/set/); the token identifies the owner.
- Release only if the token still matches: compare-and-delete in a Lua script, or [`DELEX key IFEQ token`](https://redis.io/docs/latest/commands/delex/) since 8.4.
- The TTL can expire mid-work (GC pause, slow I/O), giving two holders — protect the resource with fencing tokens; Redlock's safety debate in [distributed.md](distributed.md).
- With async replication, a failover can lose the lock key and let a second client acquire it.

### Caching with Redis

- Strategies (cache-aside, write-through) and stampede fixes are in [system.md](system.md); give every key a TTL with jitter.
- [Client-side caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) (6.0+): with `CLIENT TRACKING`, Redis sends invalidation messages for keys a client has read, so it can keep a local copy.
- Store objects as hashes when you update single fields; as serialized strings when you always read the whole object.

### Counters and rate limiters

- `INCR` then `EXPIRE` as two calls can leave a counter without a TTL if the client dies between them — wrap them in `MULTI` or a Lua script.
- Since 8.8, [`INCREX`](https://redis.io/docs/latest/commands/increx/) increments with bounds and an expiry in one command; with `EX ... ENX` the TTL is set only on creation, giving a fixed-window limiter.
- Sliding-window log: a sorted set of timestamps — `ZREMRANGEBYSCORE` old entries, `ZADD` now, `ZCARD`; algorithm trade-offs in [system.md](system.md).

## Operations

### Memory

- Redis uses [jemalloc](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/); `mem_fragmentation_ratio` (RSS ÷ used) below 1 means swapping; a high value can be fragmentation, but confirm with `allocator_frag_ratio` and absolute bytes before enabling `activedefrag`.
- [`MEMORY USAGE`](https://redis.io/docs/latest/commands/memory-usage/) reports one key's footprint; `INFO memory` the totals.
- Freed memory isn't always returned to the OS right away, so RSS can stay high after deletes.

### Security defaults

- The shipped `redis.conf` binds to `127.0.0.1`, and [protected mode](https://redis.io/docs/latest/operate/oss_and_stack/management/security/#protected-mode) refuses remote clients when no password is set; exposing it without auth invites remote takeover (`CONFIG SET dir` + `SAVE`).
- [ACLs](https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/) (6.0+) give users per-command and per-key-pattern permissions; TLS is built in since 6.0.

### Licensing and Valkey

- Redis 7.4 (2024) moved from BSD to RSALv2/SSPLv1; the Linux Foundation forked 7.2.4 as [Valkey](https://valkey.io/) (BSD), which several clouds now offer as managed Redis.
- [Redis 8.0](https://github.com/redis/redis/releases/tag/8.0.0) added AGPLv3 as a third license option and renamed Community Edition to Redis Open Source.
