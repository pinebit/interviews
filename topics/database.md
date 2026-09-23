# Databases Cheatsheet

The 10 most frequently asked database interview topics, with short answers. For SQL vs NoSQL and scaling databases, see [system.md](system.md). For replication and sharding internals, see [distributed.md](distributed.md).

## 1. What does ACID mean?

- **Atomicity** — a transaction is all-or-nothing. On failure, every change is rolled back.
- **Consistency** — a transaction moves the database from one valid state to another, and all constraints (foreign keys, checks, uniqueness) hold.
- **Isolation** — concurrent transactions don't see each other's partial work. How strictly this holds depends on the **isolation level**.
- **Durability** — once committed, data survives crashes. This is usually done with a **write-ahead log** flushed to disk.

Atomicity and durability come from the WAL and rollback, isolation from locking or MVCC. The "C" in ACID is partly the application's job, and it is **not** the "C" in CAP (which means linearizability).

## 2. What are the transaction isolation levels and anomalies?

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

## 3. How do indexes work?

An index is a separate data structure that finds rows without scanning the whole table. It is usually a **B+ tree**: balanced, sorted, O(log n) lookups, and it supports **range queries** and `ORDER BY`. Hash indexes support only equality lookups. Indexes speed up reads but **slow down every write** and use disk and memory, so index for real query patterns only.

Key concepts:
- **Composite index** `(a, b, c)` follows the **leftmost prefix rule**: it helps queries on `a`, `a, b`, and `a, b, c`, but not on `b` alone. Put equality columns first, range columns last.
- **Covering index** — contains every column the query needs, so the table itself is never read ("index-only scan").
- **Clustered index** — the table rows are physically stored in index order (InnoDB's primary key). There can be only one. PostgreSQL tables are unordered heaps.
- **Selectivity** — an index on a column with few distinct values (e.g. a boolean) is rarely used. Functions applied to a column (`WHERE lower(email) = ...`) prevent the index from being used unless you create an index on that expression.

## 4. B-tree vs LSM-tree storage engines?

**B-tree engines** (PostgreSQL, MySQL InnoDB) update pages **in place** on disk. Reads are fast and predictable, each key is in exactly one place, and range scans are efficient. Writes cause random I/O and **write amplification** (a whole page is rewritten for a small change).

**LSM-tree engines** (RocksDB, Cassandra, LevelDB, ScyllaDB) buffer writes in an in-memory **memtable**, flush it to immutable sorted files (**SSTables**), and merge those files in the background (**compaction**). Writes are fast and sequential, which makes LSM trees great for **write-heavy** workloads. Reads may have to check several files; **bloom filters** skip files that can't contain the key. Rule of thumb: **B-tree for read-heavy workloads, LSM for write-heavy ones**.

## 5. What are normalization and denormalization?

**Normalization** organizes tables to **remove redundancy** and update anomalies:
- **1NF** — atomic values, no repeating groups.
- **2NF** — 1NF plus no column depends on only part of a composite key.
- **3NF** — 2NF plus no column depends on another non-key column ("every column depends on the key, the whole key, and nothing but the key").

Each fact is stored once, so writes stay consistent.

**Denormalization** deliberately adds redundancy (duplicated columns, precomputed counts, materialized views) to **avoid expensive joins on reads**. The cost is extra storage and keeping the copies in sync on writes (triggers, application code, or async jobs). Typical approach: normalize by default, and denormalize specific hot read paths once measurements show a need.

## 6. What is MVCC?

**Multi-Version Concurrency Control** keeps **several versions of each row**, so readers see a consistent **snapshot** without taking locks: **readers don't block writers, and writers don't block readers**. Each transaction sees only versions committed before its snapshot started. Writers still take row locks against other writers.

**PostgreSQL** stores old versions in the table itself (hidden columns `xmin`/`xmax` record which transactions created and deleted each version) and needs **VACUUM** to reclaim dead rows. Long-running transactions block that cleanup and cause **bloat**. **MySQL InnoDB** and **Oracle** update rows in place and rebuild older versions from **undo logs**. MVCC is what makes Read Committed and snapshot isolation cheap.

## 7. Pessimistic vs optimistic locking? How do deadlocks happen?

**Pessimistic locking** locks data before using it: `SELECT ... FOR UPDATE` holds row locks until commit. It's safe when there is heavy contention, but it reduces concurrency. **Optimistic locking** doesn't lock. It stores a **version** column and updates with `UPDATE ... SET ..., version = version + 1 WHERE id = ? AND version = ?`. If 0 rows are updated, someone else changed the row, so retry. It's better when conflicts are rare, and common in web apps and ORMs.

A **deadlock** happens when two transactions each hold a lock the other needs (T1 locks A then wants B, T2 locks B then wants A). The database detects the cycle and **aborts one transaction**, which the app must retry. Prevention: **always acquire locks in a consistent order**, keep transactions short, and avoid waiting on user input or network calls while holding locks.

## 8. What JOIN types exist and how are they executed?

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

## 9. What is a write-ahead log (WAL)?

Before a change is applied to the data files, it is **appended to a sequential log** and flushed (`fsync`) at commit. After a crash, the database **replays the log** to redo committed changes and undo uncommitted ones (ARIES-style recovery). Appending sequentially is much faster than writing random pages, and the pages themselves are written to disk lazily at **checkpoints**.

The WAL is also the basis for **replication** (streaming the WAL to replicas), **point-in-time recovery** (base backup + replayed WAL), and **change data capture** (Debezium reads the log to stream changes to Kafka). Trade-off: `synchronous_commit = off` or group commit gives faster commits at the risk of losing the last few milliseconds of transactions in a crash.

## 10. How do you optimize a slow query?

1. **Measure**: run `EXPLAIN ANALYZE` and look for **sequential scans** on large tables, big gaps between estimated and actual row counts (stale statistics: run `ANALYZE`), and expensive sorts or hashes that spill to disk.
2. **Index** the columns used in `WHERE`, `JOIN`, and `ORDER BY`. Consider composite and covering indexes.
3. **Rewrite**: select only the columns you need (not `SELECT *`), avoid functions on indexed columns, and replace correlated subqueries with joins.
4. **Fix the N+1 problem**: one query per item in a list (a common ORM mistake). Batch with `IN (...)` or a join, or use eager loading.
5. **Paginate with a cursor** (`WHERE id > last_id LIMIT n`) instead of a large `OFFSET`, which still reads and throws away all the skipped rows.
6. **Beyond the query**: caching, materialized views, read replicas, partitioning large tables (e.g. by date), and connection pooling.

Use the slow query log or `pg_stat_statements` to find which queries matter: optimize the ones with the highest **total time**, not just the slowest single run.
