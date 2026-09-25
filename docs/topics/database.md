# Databases

What experienced database engineers forget before an interview, grouped by subtopic. For SQL vs NoSQL and the scaling ladder, see [system.md](system.md); for replication theory and sharding, see [distributed.md](distributed.md).

## Indexes

### B+tree indexes

- The default index is a **B+tree**: balanced, sorted, O(log n), serves range scans and `ORDER BY`.
- **Clustered** (InnoDB): rows are stored in primary-key order and secondary indexes point to the PK. **Heap** (PostgreSQL): rows are unordered and indexes point to a physical location (`ctid`).

### Composite indexes

- **Leftmost-prefix rule**: `(a, b, c)` serves `a`, `a,b`, `a,b,c` — not `b` alone.
- Put **equality columns first, range columns last**; the column after a range condition can't be used for seeking.

### Covering indexes

- A **covering index** holds every column the query needs, enabling an **index-only scan** (`INCLUDE` adds payload columns in PostgreSQL).
- PostgreSQL still checks the **visibility map**; recently modified pages force heap visits until VACUUM runs.

### Partial and expression indexes

- **Partial** (`WHERE deleted_at IS NULL`) and **expression** (`ON lower(email)`) indexes cover only what queries use.
- **Sargability**: a function or implicit cast on an indexed column (`WHERE lower(email) = ...`) blocks index use unless a matching expression index exists.

### Specialized index types

| Index | Use for |
|---|---|
| **GIN** | full-text, JSONB, arrays (inverted index) |
| **GiST** | geometry, ranges, nearest neighbor |
| **BRIN** | huge, naturally ordered tables (append-only time series); tiny |
| Hash | equality only |

### Building indexes online

- Plain `CREATE INDEX` blocks writes for the whole build; **`CREATE INDEX CONCURRENTLY`** doesn't, but is slower, can't run in a transaction, and leaves an `INVALID` index if it fails.
- Index every foreign key you join or cascade-delete on — PostgreSQL doesn't create them automatically.

## Transactions and isolation

### Anomalies × isolation levels

| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | possible | possible | possible |
| Read Committed | — | possible | possible |
| Repeatable Read | — | — | possible (per SQL standard) |
| Serializable | — | — | — |

### Lost update and write skew

- **Lost update**: two read-modify-write cycles overwrite each other.
- **Write skew**: two transactions read overlapping data and write different rows, together breaking an invariant (both doctors go off call).

### PostgreSQL isolation

- **Default: Read Committed**; Repeatable Read is **snapshot isolation** — no phantoms, and a concurrent update of the same row **aborts** (no lost update), but write skew is possible.
- **Serializable** is **SSI**: it prevents write skew by aborting with a serialization error, so the app must **retry**.

### MySQL InnoDB isolation

- **Default: Repeatable Read** with **next-key locks** (record + gap) on locking reads, blocking many phantoms.
- Plain `SELECT` reads the snapshot, but `UPDATE` sees the latest committed row — lost updates slip through without `SELECT ... FOR UPDATE`.

## MVCC and locking

### PostgreSQL MVCC

- Readers read a **snapshot** and never block writers, or vice versa; writers still lock rows against each other.
- Old row versions stay in the table, tagged **`xmin`/`xmax`**; **VACUUM** reclaims them, and a long-running transaction blocks it, causing **bloat**.
- **XID wraparound** (32-bit transaction IDs) forces aggressive anti-wraparound vacuuming.
- **HOT updates** skip index maintenance when no indexed column changed and the page has room.

### InnoDB MVCC

- Updates happen in place; older versions are rebuilt from the **undo log**, and a long transaction makes undo history grow.

### Row locks and queue tables

- `SELECT ... FOR UPDATE` locks the rows it returns; **`SKIP LOCKED`** lets workers claim different rows of a queue table without blocking.

### Optimistic locking

- Add a `version` column and `UPDATE ... WHERE id = ? AND version = ?`; zero rows updated means someone else won — reload and retry.
- Best when conflicts are rare; pessimistic locks when they're frequent.

### Deadlocks

- Two transactions each hold a lock the other needs; the database detects the cycle and **aborts one**.
- Prevent with a **consistent lock order** and short transactions.

### DDL locks and the lock queue

- Most `ALTER TABLE` forms take an **`ACCESS EXCLUSIVE`** lock. If it waits behind a long query, **every later query queues behind it** — a brief outage from a "fast" migration.
- Set **`lock_timeout`** (a few seconds) on migrations and retry; rollout patterns in [devops.md](devops.md).

### Advisory locks

- PostgreSQL **advisory locks** are app-defined locks on a number, not a row — for leader election or job dedup without a table to lock.

## Storage engines and durability

### B-tree vs LSM-tree

| | B-tree (PostgreSQL, InnoDB) | LSM-tree (RocksDB, Cassandra) |
|---|---|---|
| Writes | in-place page updates, random I/O | append to **memtable** → flush immutable **SSTables** |
| Reads | one tree walk, predictable | may check several files; **bloom filters** skip most |
| Background work | page splits, vacuum | **compaction** |
| Fits | read-heavy, range scans | write-heavy |

- Compaction strategy trades **read, write, and space amplification** against each other.

### Write-ahead log

- Commits append to the **WAL** and `fsync` it before data pages change; pages are written lazily at **checkpoints**.
- Crash recovery replays the log (ARIES-style redo/undo); **group commit** batches many commits into one fsync.

### Backups and PITR

- **Logical** backups (`pg_dump`): portable, slow to restore at scale. **Physical** (`pg_basebackup`, snapshots): fast restore, same major version.
- **PITR** = physical base backup + WAL replayed to a chosen moment. Replicas are **not backups** — they replicate mistakes too.

## Query execution and tuning

### Logical evaluation order

- **`FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`** — why a `SELECT` alias works in `ORDER BY` but not in `WHERE`.

### Reading EXPLAIN ANALYZE

- Look for sequential scans on big tables, **estimated vs actual rows** far apart (stale statistics — run `ANALYZE`), and sorts or hashes spilling to disk.

### Join algorithms

| Join | Best when |
|---|---|
| **Nested loop** | outer side small, inner side index-backed |
| **Hash join** | large equality joins without a useful index; builds on the smaller side |
| **Merge join** | both inputs already sorted (e.g. from indexes) |

### Deep pagination cost

- **OFFSET** still reads and discards every skipped row, so deep pages get slower; **keyset** pagination seeks by index — API side in [backend.md](backend.md).

## SQL gotchas

### NULL and three-valued logic

- Any comparison with NULL — even **`NULL = NULL`** — is UNKNOWN, and `WHERE` drops it; use `IS [NOT] NULL` or `IS [NOT] DISTINCT FROM`.
- **`NOT IN` with a NULL in the list returns no rows** — use `NOT EXISTS`.
- `COUNT(*)` counts rows; `COUNT(col)` and other aggregates skip NULLs.

### Window functions

- `fn() OVER (PARTITION BY ... ORDER BY ...)` computes per row without collapsing rows.
- **`ROW_NUMBER`** 1,2,3; **`RANK`** 1,1,3 (gaps); **`DENSE_RANK`** 1,1,2.
- The default frame with `ORDER BY` is **`RANGE ... CURRENT ROW`**, which includes all peer rows with equal sort keys — use `ROWS` for a true running total.

### CTE materialization

- **Since PostgreSQL 12**, a side-effect-free CTE referenced **once** is inlined into the outer query; one referenced several times is materialized.
- `MATERIALIZED` / `NOT MATERIALIZED` override the default.

### Upsert

- **`INSERT ... ON CONFLICT (...) DO UPDATE`** (PostgreSQL) / `ON DUPLICATE KEY UPDATE` (MySQL) replaces a racy check-then-write.

## Non-relational stores

### Redis

- Commands execute on **one thread**, so each command (and Lua script or `MULTI` block) is atomic; a slow command (`KEYS *`, big `SMEMBERS`) blocks everyone.
- Structures: strings, hashes, lists, sets, **sorted sets** (skip list + hash — leaderboards, rate limiters), streams, HyperLogLog.
- **Redis Cluster** splits keys into **16,384 hash slots**; multi-key operations need the same slot, forced with **hash tags** (`{user42}:cart`).

### Redis persistence and licensing

- **RDB**: periodic fork + snapshot (copy-on-write), loses writes since the last one. **AOF**: logs every write; `appendfsync everysec` (default) loses up to **~1 s**.
- Replication is **asynchronous** — failover can drop acknowledged writes.
- The 2024 license change led to the **Valkey** fork (Linux Foundation); **Redis 8** (2025) added AGPLv3 as an option.

### Wide-column key design (Cassandra, DynamoDB)

- The **partition key** picks the node; the **sort/clustering key** orders rows inside the partition — a query must supply the partition key.
- Model **tables per query** (denormalized), not per entity; unbounded partitions (all events of a popular user) become hot and huge — add a time bucket to the key.
- Deletes write **tombstones**, which slow reads until compaction purges them.

### Search engines and inverted indexes

- An **inverted index** maps each term to the list of documents containing it; scoring is **BM25**.
- Elasticsearch/OpenSearch are **near-real-time** (new docs searchable after a refresh, ~1 s default), and the primary shard count is fixed at index creation — resize by reindexing or split/shrink.
- Treat the search index as a derived store, fed by CDC from the source of truth.

## Schema design

### Normalization

- **1NF** atomic values → **2NF** no partial-key dependency → **3NF/BCNF** no dependency on non-key columns: each fact stored once.
- **Denormalize** measured hot paths only (copied columns, counters, materialized views), accepting harder writes.

### Surrogate keys

- **Auto-increment bigint**: compact and ordered, but reveals counts and needs one sequence.
- **UUIDv4** scatters inserts across the B-tree; **UUIDv7** is time-ordered and native via **`uuidv7()` since PostgreSQL 18** — ID schemes in [distributed.md](distributed.md).

### Constraints and soft deletes

- `FOREIGN KEY`, `CHECK`, and `UNIQUE` are the last line of defense — application checks alone race.
- **Soft deletes** (`deleted_at`) plus a partial unique index keep history and undo.

## Scaling

### Physical vs logical replication

- **Physical (streaming)**: ships WAL bytes, exact copy, same major version.
- **Logical**: row changes per table, works across versions and subsets, feeds CDC.
- PostgreSQL **`synchronous_commit`** picks how far a commit waits (`remote_write`, `on`, `remote_apply`); sync vs async trade-offs are in [distributed.md](distributed.md).

### Table partitioning

- **Range** (most common, by date), **list**, or **hash**; **partition pruning** skips irrelevant partitions.
- Dropping an old partition is instant, unlike a bloating bulk `DELETE`; PostgreSQL unique constraints must include the partition key.

### Connection pooling

- Each PostgreSQL connection is a **process** (a few MB), so thousands of direct connections hurt — pool them.
- PgBouncer **session mode** keeps `SET` and advisory locks; **transaction mode** scales further but loses session state; prepared statements work in it **since PgBouncer 1.21**.

### OLTP vs OLAP

- **OLTP**: row storage, many small transactional reads and writes.
- **OLAP**: **column storage**, compression, vectorized scans of few columns over many rows, star schemas (facts + dimensions).

### Materialized views

- Store a query result for fast reads that are stale until refresh; `REFRESH MATERIALIZED VIEW CONCURRENTLY` avoids blocking reads but needs a unique index.
