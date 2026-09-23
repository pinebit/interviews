# Databases Cheatsheet

The 20 most frequently asked database interview topics, with short answers. For SQL vs NoSQL and scaling databases, see [system.md](system.md). For replication and sharding internals, see [distributed.md](distributed.md).

## 1. What does ACID mean?

- **Atomicity** — a transaction is all-or-nothing. On failure, every change is rolled back.
- **Consistency** — a transaction moves the database from one valid state to another, and all constraints (foreign keys, checks, uniqueness) hold.
- **Isolation** — concurrent transactions don't see each other's partial work. How strictly this holds depends on the **isolation level**.
- **Durability** — once committed, data survives crashes. This is usually done with a **write-ahead log** flushed to disk.

Atomicity and durability come from the WAL and rollback, isolation from locking or MVCC. The "C" in ACID is partly the application's job, and it is **not** the "C" in CAP (which means linearizability).

## 2. How do indexes work?

An index is a separate data structure that finds rows without scanning the whole table. It is usually a **B+ tree**: balanced, sorted, O(log n) lookups, and it supports **range queries** and `ORDER BY`. Hash indexes support only equality lookups. Indexes speed up reads but **slow down every write** and use disk and memory, so index for real query patterns only.

Key concepts:

- **Composite index** `(a, b, c)` follows the **leftmost prefix rule**: it helps queries on `a`, `a, b`, and `a, b, c`, but not on `b` alone. Put equality columns first, range columns last.
- **Covering index** — contains every column the query needs, so the table itself is never read ("index-only scan").
- **Clustered index** — the table rows are physically stored in index order (InnoDB's primary key). There can be only one. PostgreSQL tables are unordered heaps.
- **Selectivity** — an index on a column with few distinct values (e.g. a boolean) is rarely used. Functions applied to a column (`WHERE lower(email) = ...`) prevent the index from being used unless you create an index on that expression.

Other index types worth naming: **partial indexes** (`WHERE deleted_at IS NULL`), **GIN** (full-text, JSONB, arrays in PostgreSQL), and **GiST** (geospatial).

## 3. What are the transaction isolation levels and anomalies?

| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | possible | possible | possible |
| **Read Committed** | — | possible | possible |
| **Repeatable Read** | — | — | possible (per the SQL standard) |
| **Serializable** | — | — | — |

- **Dirty read**: seeing another transaction's uncommitted data.
- **Non-repeatable read**: reading the same row twice and getting different values.
- **Phantom read**: running the same query twice and getting new or missing rows.

Two more anomalies matter in practice: **lost update** (two read-modify-write cycles overwrite each other) and **write skew** (two transactions read the same data, then write different rows, and together they break an invariant, e.g. both on-call doctors go off duty).

Defaults: **PostgreSQL = Read Committed**, **MySQL InnoDB = Repeatable Read**. PostgreSQL's Repeatable Read is actually **snapshot isolation**: no phantoms, but write skew is still possible. Only Serializable (PostgreSQL uses SSI, Serializable Snapshot Isolation) prevents write skew, and the app must **retry transactions that fail with serialization errors**.

## 4. What JOIN types exist and how are they executed?

Types:

- **INNER JOIN** — only rows that match on both sides.
- **LEFT / RIGHT OUTER JOIN** — all rows from one side, with NULLs where the other side has no match.
- **FULL OUTER JOIN** — all rows from both sides.
- **CROSS JOIN** — every combination (Cartesian product).
- **Self join** — a table joined to itself, e.g. employee → manager.

Anti-join pattern: `LEFT JOIN ... WHERE b.id IS NULL` or `NOT EXISTS`. Avoid `NOT IN` when the subquery can contain NULLs — then it returns no rows.

The query planner picks the join algorithm:

- **Nested loop** — for each outer row, look up matches, ideally through an index. Best when one side is small.
- **Hash join** — build a hash table on the smaller side, then probe it with the larger side. Best for large joins on equality with no useful index.
- **Merge join** — both inputs sorted on the join key, then merged. Good when inputs are already sorted (e.g. from an index).

## 5. What are normalization and denormalization?

**Normalization** organizes tables to **remove redundancy** and update anomalies:

- **1NF** — atomic values, no repeating groups.
- **2NF** — 1NF plus no column depends on only part of a composite key.
- **3NF** — 2NF plus no column depends on another non-key column ("every column depends on the key, the whole key, and nothing but the key").

Each fact is stored once, so writes stay consistent.

**Denormalization** deliberately adds redundancy (duplicated columns, precomputed counts, materialized views) to **avoid expensive joins on reads**. The cost is extra storage and keeping the copies in sync on writes (triggers, application code, or async jobs). Typical approach: normalize by default, and denormalize specific hot read paths once measurements show a need.

## 6. How do you optimize a slow query?

1. **Measure**: run `EXPLAIN ANALYZE` and look for **sequential scans** on large tables, big gaps between estimated and actual row counts (stale statistics: run `ANALYZE`), and expensive sorts or hashes that spill to disk.
2. **Index** the columns used in `WHERE`, `JOIN`, and `ORDER BY`. Consider composite and covering indexes.
3. **Rewrite**: select only the columns you need (not `SELECT *`), avoid functions on indexed columns, and replace correlated subqueries with joins.
4. **Fix the N+1 problem**: one query per item in a list (a common ORM mistake). Batch with `IN (...)` or a join, or use eager loading.
5. **Paginate with a cursor** (`WHERE id > last_id LIMIT n`) instead of a large `OFFSET`, which still reads and throws away all the skipped rows.
6. **Beyond the query**: caching, materialized views, read replicas, partitioning large tables (e.g. by date), and connection pooling.

Use the slow query log or `pg_stat_statements` to find which queries matter: optimize the ones with the highest **total time**, not just the slowest single run.

## 7. Pessimistic vs optimistic locking? How do deadlocks happen?

**Pessimistic locking** locks data before using it: `SELECT ... FOR UPDATE` holds row locks until commit. It's safe when there is heavy contention, but it reduces concurrency. **Optimistic locking** doesn't lock. It stores a **version** column and updates with `UPDATE ... SET ..., version = version + 1 WHERE id = ? AND version = ?`. If 0 rows are updated, someone else changed the row, so retry. It's better when conflicts are rare, and common in web apps and ORMs.

A **deadlock** happens when two transactions each hold a lock the other needs (T1 locks A then wants B, T2 locks B then wants A). The database detects the cycle and **aborts one transaction**, which the app must retry. Prevention: **always acquire locks in a consistent order**, keep transactions short, and avoid waiting on user input or network calls while holding locks.

## 8. What is MVCC?

**Multi-Version Concurrency Control** keeps **several versions of each row**, so readers see a consistent **snapshot** without taking locks: **readers don't block writers, and writers don't block readers**. Each transaction sees only versions committed before its snapshot started. Writers still take row locks against other writers.

**PostgreSQL** stores old versions in the table itself (hidden columns `xmin`/`xmax` record which transactions created and deleted each version) and needs **VACUUM** to reclaim dead rows. Long-running transactions block that cleanup and cause **bloat**. **MySQL InnoDB** and **Oracle** update rows in place and rebuild older versions from **undo logs**. MVCC is what makes Read Committed and snapshot isolation cheap.

## 9. What keys and constraints exist? Auto-increment vs UUID?

- **PRIMARY KEY** — unique and not null, one per table, identifies each row.
- **FOREIGN KEY** — enforces that a referenced row exists; `ON DELETE CASCADE / SET NULL / RESTRICT` defines what happens when the parent is deleted. Index FK columns — PostgreSQL doesn't do it automatically, and unindexed FKs make deletes and joins slow.
- **UNIQUE**, **NOT NULL**, **CHECK** (`CHECK (price >= 0)`) — enforce invariants in the database, not only in application code.

**Natural keys** (email, ISBN) carry business meaning but can change; **surrogate keys** (generated IDs) are stable and usually preferred. **Auto-increment** IDs are compact and insert in order, but reveal record counts and need a central generator. **UUIDv4** needs no coordination but is 16 bytes and random, which **scatters inserts across the B-tree** and bloats indexes. **UUIDv7** is time-ordered, which fixes the locality problem — see [distributed.md](distributed.md) for ID generation.

## 10. What is the logical order of a SQL query? WHERE vs HAVING?

A query is written `SELECT ... FROM ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... LIMIT`, but logically evaluated as: **FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT/OFFSET**. That explains common errors: you can't use a `SELECT` alias in `WHERE` (it doesn't exist yet), but you can in `ORDER BY`.

**`WHERE` filters rows before grouping** and can't use aggregates. **`HAVING` filters groups after aggregation** (`HAVING COUNT(*) > 5`). Filter in `WHERE` whenever possible — fewer rows to group. Other quick ones: `COUNT(*)` counts rows, `COUNT(col)` skips NULLs; `UNION` removes duplicates, `UNION ALL` doesn't (and is faster); `DELETE` removes rows one by one (logged, can have `WHERE`, fires triggers), `TRUNCATE` empties the whole table fast, `DROP` removes the table itself.

## 11. What are window functions?

A window function computes a value **over a set of related rows without collapsing them** into one row, unlike `GROUP BY`. Syntax: `fn() OVER (PARTITION BY dept ORDER BY salary DESC)`. `PARTITION BY` defines the groups, `ORDER BY` the order inside each group, and an optional frame (`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`) limits which rows are included.

Common functions: **`ROW_NUMBER`** (1, 2, 3), **`RANK`** (1, 1, 3 — gaps after ties), **`DENSE_RANK`** (1, 1, 2 — no gaps), **`LAG`/`LEAD`** (previous/next row's value), running `SUM`/`AVG`, `NTILE`. Classic interview tasks: **top-N per group**, the **Nth highest salary** (`DENSE_RANK`), running totals, month-over-month change, and deduplication (`ROW_NUMBER() ... = 1`). Window functions are evaluated after `WHERE`, so filter on them in an outer query or CTE.

## 12. B-tree vs LSM-tree storage engines?

**B-tree engines** (PostgreSQL, MySQL InnoDB) update pages **in place** on disk. Reads are fast and predictable, each key is in exactly one place, and range scans are efficient. Writes cause random I/O and **write amplification** (a whole page is rewritten for a small change).

**LSM-tree engines** (RocksDB, Cassandra, LevelDB, ScyllaDB) buffer writes in an in-memory **memtable**, flush it to immutable sorted files (**SSTables**), and merge those files in the background (**compaction**). Writes are fast and sequential, which makes LSM trees great for **write-heavy** workloads. Reads may have to check several files; **bloom filters** skip files that can't contain the key. Rule of thumb: **B-tree for read-heavy workloads, LSM for write-heavy ones**.

## 13. What is a write-ahead log (WAL)?

Before a change is applied to the data files, it is **appended to a sequential log** and flushed (`fsync`) at commit. After a crash, the database **replays the log** to redo committed changes and undo uncommitted ones (ARIES-style recovery). Appending sequentially is much faster than writing random pages, and the pages themselves are written to disk lazily at **checkpoints**.

The WAL is also the basis for **replication** (streaming the WAL to replicas), **point-in-time recovery** (base backup + replayed WAL), and **change data capture** (Debezium reads the log to stream changes to Kafka). Trade-off: `synchronous_commit = off` or group commit gives faster commits at the risk of losing the last few milliseconds of transactions in a crash.

## 14. How does database replication work?

**Physical replication** streams the WAL (byte-level page changes) to replicas: an exact copy of the whole server, read-only replicas, same major version required. **Logical replication** sends row-level changes (insert/update/delete) per table: works across versions, can replicate a subset of tables, and can feed other systems (PostgreSQL publications/subscriptions, MySQL row-based binlog).

**Asynchronous** replication is fast but can lose the latest commits on failover; **synchronous** waits for a replica to confirm each commit (no data loss, higher latency); **semi-synchronous** (MySQL) waits for at least one replica to receive the change. **Failover** promotes a replica to primary — automated by Patroni, Orchestrator, or managed services (RDS Multi-AZ). Risks to mention: data loss with async, **split brain** if the old primary keeps accepting writes, and **replication lag** causing stale reads.

## 15. What is table partitioning?

**Partitioning** splits one large table into smaller physical pieces **on the same server**, while queries still see one table. Strategies: **range** (by date — the most common), **list** (by region or tenant), **hash** (spread evenly). Different from **sharding**, which spreads data across servers.

Benefits: **partition pruning** (a query with `WHERE created_at >= '2026-09-01'` only scans matching partitions), smaller per-partition indexes, and cheap data retention — **dropping an old partition** is instant, while `DELETE`-ing millions of rows is slow and bloats the table. Costs: queries without the partition key must scan all partitions, and in PostgreSQL unique constraints must include the partition key.

## 16. OLTP vs OLAP? Row vs column storage?

**OLTP** (online transaction processing) serves the application: many small, concurrent reads and writes of individual rows, low latency, normalized schemas — **row-oriented** databases (PostgreSQL, MySQL) store each row together, ideal for "fetch or update this order". **OLAP** (online analytical processing) serves analytics: few large queries that scan millions of rows but only a few columns (`SUM(revenue) GROUP BY month`).

**Column-oriented** stores (ClickHouse, Snowflake, BigQuery, Redshift, DuckDB) store each column separately, so queries **read only the columns they need**, similar values **compress** extremely well, and execution is **vectorized** (processing batches of values at once). Analytics data is typically loaded via ETL/ELT or CDC into a warehouse, modeled as a **star schema**: a central fact table (events, sales) with dimension tables (users, products, dates).

## 17. Views vs materialized views?

A **view** is a saved query: it stores no data and runs the underlying query every time you select from it. It's always up to date and useful for simplifying complex queries, hiding columns, or giving a stable interface over changing tables — but it's **no faster** than the query itself.

A **materialized view** **stores the query result** on disk, so reads are fast, but the data is **stale until refreshed** (`REFRESH MATERIALIZED VIEW` in PostgreSQL; `CONCURRENTLY` avoids blocking reads and requires a unique index). Use it for expensive aggregations like dashboards and reports, refreshed on a schedule. Some databases can maintain them incrementally (Oracle, SQL Server indexed views, streaming databases).

## 18. Why do you need connection pooling?

Opening a database connection is expensive (TCP + TLS handshake, authentication, and in PostgreSQL a whole **new process** using several MB of memory). Databases also have a **hard connection limit**, and performance drops long before it — hundreds of active connections fight over CPU and locks. A **connection pool** keeps a set of open connections and lends them out per request.

Pools live **in the application** (HikariCP, Go's `database/sql`) or as an **external proxy** (PgBouncer, RDS Proxy) — needed when many app instances or serverless functions would each open their own connections. PgBouncer's **transaction mode** (a connection is only held for one transaction) scales best but breaks session-level features like `SET` and advisory locks. Keep pools **small** — around 2× CPU cores of the DB server is a common starting point — and always return connections (leaks exhaust the pool).

## 19. How does NULL behave in SQL?

`NULL` means **unknown**, and SQL uses **three-valued logic**: TRUE, FALSE, UNKNOWN. Any comparison with NULL yields UNKNOWN — even **`NULL = NULL`** — so use **`IS NULL`** / `IS NOT NULL` (or `IS DISTINCT FROM` for NULL-safe comparison). `WHERE` keeps only rows where the condition is TRUE, so UNKNOWN rows silently disappear.

Other gotchas: arithmetic and string concatenation with NULL give NULL (use **`COALESCE`**); aggregates ignore NULLs except `COUNT(*)`, so `AVG(col)` averages only non-null values; **`NOT IN` with a NULL in the list returns no rows**; `UNIQUE` columns can contain multiple NULLs in most databases; sort position of NULLs differs by database (use `NULLS FIRST/LAST` explicitly).

## 20. How do backups and recovery work?

**Logical backups** (`pg_dump`, `mysqldump`) export SQL or data: portable across versions and good for single tables, but slow to create and restore for large databases. **Physical backups** (`pg_basebackup`, Percona XtraBackup, storage snapshots) copy the data files: fast to restore, same major version required.

**Point-in-time recovery (PITR)** = a physical base backup + the archived **WAL**, replayed up to any chosen moment — for example, one second before an accidental `DELETE`. Define **RPO** (how much data you can afford to lose) and **RTO** (how long recovery may take). **Replicas are not backups**: they faithfully replicate your mistakes. Follow the **3-2-1 rule** (3 copies, 2 media, 1 off-site) and **test restores regularly** — a backup you've never restored is only a hope.
