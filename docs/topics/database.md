# Databases

What experienced database engineers forget before an interview, grouped by subtopic. For SQL vs NoSQL and scaling databases, see [system.md](system.md). For replication theory and sharding, see [distributed.md](distributed.md).

## Indexes

### B+tree and clustering

- Standard index structure is a **B+tree**: balanced, sorted, O(log n), supports range scans and `ORDER BY`.
- **Clustered index**: rows are physically stored in index order — InnoDB's primary key. **Heap**: rows stored unordered, index points to a location — PostgreSQL tables by default.
- **Composite index** `(a, b, c)` follows the **leftmost-prefix rule**: helps `a`, `a,b`, `a,b,c` — not `b` alone. Put equality columns first, range columns last.

### Covering and specialized indexes

- **Covering index** contains every column the query needs, enabling an **index-only scan**; PostgreSQL still checks the **visibility map** to confirm rows are visible without touching the heap.
- **Partial indexes** (`WHERE deleted_at IS NULL`) and **expression indexes** (`ON lower(email)`) index only what's queried.
- **GIN** — full-text, JSONB, arrays. **GiST** — geospatial, nearest-neighbor. **BRIN** — tiny index for naturally-ordered huge tables (append-only time series). **Hash** — equality-only.
- **Sargability**: a function or implicit cast on an indexed column (`WHERE lower(email) = ...`) prevents index use unless there's a matching expression index.

## Transactions and isolation

### Anomalies × isolation levels

| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | possible | possible | possible |
| Read Committed | — | possible | possible |
| Repeatable Read | — | — | possible (per SQL standard) |
| Serializable | — | — | — |

- **Lost update**: two read-modify-write cycles overwrite each other. **Write/read skew**: transactions read overlapping data and write different rows, together breaking an invariant not visible to either alone.
- **PostgreSQL default: Read Committed**; its Repeatable Read is **snapshot isolation** — no phantoms, but write skew is still possible.
- **MySQL InnoDB default: Repeatable Read**, implemented with **next-key locks** (record + gap locks) that also block some phantoms the standard wouldn't require.
- Only **Serializable** (PostgreSQL: **SSI**, Serializable Snapshot Isolation) prevents write skew — the app must retry transactions that fail with a serialization error.

## MVCC and locking

### MVCC mechanics

- Readers see a consistent **snapshot** without locking; readers don't block writers and vice versa. Writers still take row locks against other writers.
- **PostgreSQL**: old row versions live in the table itself, tagged with **`xmin`/`xmax`**; **VACUUM** reclaims dead versions, long-running transactions block it and cause **bloat**; **xid wraparound** forces aggressive vacuuming past a transaction-ID threshold.
- **InnoDB**: updates in place, older versions rebuilt from the **undo log**.
- HOT (heap-only tuple) updates in PostgreSQL skip index maintenance when no indexed column changed.

### Explicit locking

- `SELECT ... FOR UPDATE` takes row locks; `SKIP LOCKED` lets concurrent workers claim different rows from a queue table without blocking each other.
- **Optimistic locking**: a version column, `UPDATE ... WHERE id=? AND version=?`; zero rows updated means retry. Preferred when conflicts are rare.
- **Deadlock**: two transactions each hold a lock the other needs; the database detects the cycle and aborts one. Prevent with a **consistent lock ordering** and short transactions.
- **Advisory locks** (PostgreSQL) are application-defined locks outside any table, useful for cross-session coordination (leader election, job dedup) without a real row to lock.

## Storage engines and durability

### B-tree vs LSM

- **B-tree** (PostgreSQL, InnoDB): in-place page updates, predictable reads, efficient range scans; random I/O and **write amplification** on writes.
- **LSM-tree** (RocksDB, Cassandra, ScyllaDB): buffer writes in a **memtable**, flush to immutable **SSTables**, merge via background **compaction**. Fast sequential writes; reads may check several files (**bloom filters** skip files that can't contain the key). Trade-off is **read/write/space amplification** in different proportions depending on compaction strategy.
- Rule of thumb: B-tree for read-heavy, LSM for write-heavy.

### WAL and backups

- Changes are appended to a sequential **write-ahead log** and `fsync`'d at commit before data pages are touched; crash recovery replays it (ARIES-style redo/undo). Pages are written lazily at **checkpoints**. **Group commit** batches concurrent fsyncs for throughput.
- **Logical backups** (`pg_dump`) — portable, slow to restore at scale. **Physical backups** (`pg_basebackup`, snapshots) — fast restore, same major version required.
- **PITR** = physical base backup + replayed WAL up to a chosen moment. Define **RPO**/**RTO**; replicas are not backups — they replicate mistakes too.

## Query execution and tuning

### Logical order and plans

- Logical evaluation order: **`FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`** — explains why a `SELECT` alias can't be used in `WHERE` but can in `ORDER BY`.
- Read `EXPLAIN ANALYZE`: sequential scans on large tables, large gaps between estimated and actual row counts (stale statistics — run `ANALYZE`), sorts/hashes spilling to disk.
- Join algorithms: **nested loop** (best when one side is small, ideally index-backed), **hash join** (build on the smaller side, probe with the larger — best for large equality joins without a useful index), **merge join** (both inputs pre-sorted, e.g. from an index).
- **Keyset pagination** (`WHERE id > last_id LIMIT n`) stays fast at any depth; **OFFSET** pagination still reads and discards every skipped row, getting slower with depth.

## SQL gotchas

### NULL and three-valued logic

- `NULL` means unknown; any comparison including **`NULL = NULL`** yields UNKNOWN, so `WHERE` silently drops those rows. Use `IS [NOT] NULL` or `IS [NOT] DISTINCT FROM`.
- **`NOT IN` with a NULL in the list returns zero rows** — use `NOT EXISTS` instead.
- `COUNT(*)` counts rows; `COUNT(col)` skips NULLs; aggregates generally ignore NULLs.

### Window functions and upsert

- `fn() OVER (PARTITION BY ... ORDER BY ...)` computes per-row without collapsing rows, unlike `GROUP BY`.
- **`ROW_NUMBER`** (1,2,3 no ties), **`RANK`** (1,1,3 — gaps after ties), **`DENSE_RANK`** (1,1,2 — no gaps).
- Default frame is **`RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`** — surprises people expecting `ROWS`, since `RANGE` groups peer rows with equal `ORDER BY` values together.
- CTEs are **inlined** (not materialized as an optimization fence) **since PostgreSQL 12**, unless marked `MATERIALIZED`.
- **`INSERT ... ON CONFLICT (...) DO UPDATE`** (upsert) avoids a separate check-then-write round trip.

## Schema design

### Normalization and keys

- **1NF** (atomic values) → **2NF** (no partial-key dependency) → **3NF**/**BCNF** (no dependency on a non-key column) — each fact stored once.
- **Denormalization** trades write complexity for read speed (duplicated columns, precomputed counts, materialized views); normalize by default, denormalize measured hot paths.
- Surrogate keys: **auto-increment bigint** is compact and insertion-ordered but reveals record counts and needs a central sequence. **UUIDv4** scatters inserts across the B-tree and bloats indexes; **UUIDv7** — time-ordered, fixes locality, generated natively with **`uuidv7()`** built into PostgreSQL **since version 18** — see [distributed.md](distributed.md) for the general ID-generation trade-offs.
- Prefer soft deletes (`deleted_at`) with a partial index over hard deletes when audit history or undo matters; constraints (`FOREIGN KEY`, `CHECK`, `UNIQUE`) are the last line of defense — don't rely on application code alone.

## Scaling

### Replication setups

- **Physical (streaming) replication**: byte-level WAL shipping, exact copy, same major version required. **Logical replication**: row-level changes per table, cross-version, can replicate a subset or feed other systems (CDC).
- **Sync** replicas confirm each commit (no loss, higher latency); **async** is fast but can lose the latest commits on failover; watch **replication lag**.

### Partitioning and pooling

- **Declarative partitioning**: **range** (most common, e.g. by date), **list**, **hash**. **Partition pruning** lets a query touch only matching partitions; dropping an old partition is instant vs. a slow, bloating `DELETE`. PostgreSQL requires unique constraints to include the partition key.
- **Connection pooling**: PgBouncer **session mode** preserves `SET`/advisory locks per connection; **transaction mode** scales further (connection freed after each transaction) but breaks those session-level features — **prepared statements became usable in transaction mode since PgBouncer 1.21**.
- **OLTP** (row storage, many small transactional reads/writes) vs **OLAP** (column storage, few large scans over few columns, vectorized execution, star schema fact/dimension tables) — see [system.md](system.md) for the broader SQL/NoSQL choice.
- **Materialized views** store a query's result on disk for fast, stale-until-refreshed reads; `REFRESH MATERIALIZED VIEW CONCURRENTLY` avoids blocking reads but needs a unique index.
