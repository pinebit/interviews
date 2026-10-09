# PostgreSQL

What experienced PostgreSQL engineers forget before an interview, grouped by subtopic. For SQL vs NoSQL, storage engines, and the scaling ladder, see [system.md](system.md); for replication theory and consistency models, see [distributed.md](distributed.md).

## Indexes

### B-tree indexes

- The default index is a [B+tree](https://en.wikipedia.org/wiki/B%2B_tree): balanced, sorted, O(log n), serves equality, range scans, and `ORDER BY`.
- Tables are [heaps](https://www.postgresql.org/docs/current/storage-page-layout.html): rows are unordered and every index entry points to a physical location ([`ctid`](https://www.postgresql.org/docs/current/ddl-system-columns.html#DDL-SYSTEM-COLUMNS-CTID)), which changes when the row is updated.
- [Deduplication](https://www.postgresql.org/docs/current/btree.html#BTREE-DEDUPLICATION) (PostgreSQL 13+) stores repeated keys once, shrinking indexes on low-cardinality columns.

### Composite indexes

- [Leftmost-prefix rule](https://www.postgresql.org/docs/current/indexes-multicolumn.html): `(a, b, c)` seeks efficiently on `a`, `a,b`, `a,b,c` — not on `b` alone.
- [Skip scan](https://www.postgresql.org/docs/current/indexes-multicolumn.html) (PostgreSQL 18+) serves `b` alone by probing each distinct `a`; cheap only when `a` has few values.
- Put equality columns first, range columns last; columns after a range condition only filter inside the scanned range (unless skip scan applies).

### Covering indexes

- A [covering index](https://www.postgresql.org/docs/current/indexes-index-only-scans.html) holds every column the query needs, enabling an index-only scan; [`INCLUDE`](https://www.postgresql.org/docs/current/sql-createindex.html) (PostgreSQL 11+) adds non-key payload columns.
- An index-only scan still checks the [visibility map](https://www.postgresql.org/docs/current/storage-vm.html); recently modified pages force heap visits until [VACUUM](https://www.postgresql.org/docs/current/routine-vacuuming.html) runs.

### Partial and expression indexes

- [Partial](https://www.postgresql.org/docs/current/indexes-partial.html) (`WHERE deleted_at IS NULL`) and [expression](https://www.postgresql.org/docs/current/indexes-expressional.html) (`ON lower(email)`) indexes cover only what queries use.
- [Sargability](https://en.wikipedia.org/wiki/Sargable): a function or implicit cast on an indexed column (`WHERE lower(email) = ...`) blocks index use unless a matching expression index exists.
- The planner uses a partial index only when it can prove the query's `WHERE` implies the index predicate; a generic prepared-statement plan, which sees `$1` instead of the value, can't prove it.

### Specialized index types

| Index | Use for |
|---|---|
| [GIN](https://www.postgresql.org/docs/current/gin.html) | full-text, JSONB, arrays ([inverted index](https://en.wikipedia.org/wiki/Inverted_index)); slower writes |
| [GiST](https://www.postgresql.org/docs/current/gist.html) | geometry, ranges, nearest neighbor, exclusion constraints |
| [BRIN](https://www.postgresql.org/docs/current/brin.html) | huge, naturally ordered tables (append-only time series); tiny |
| [Hash](https://www.postgresql.org/docs/current/hash-index.html) | equality only |

### Building indexes online

- Plain [`CREATE INDEX`](https://www.postgresql.org/docs/current/sql-createindex.html) takes a `SHARE` lock: reads continue, writes block for the whole build.
- [`CREATE INDEX CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY) doesn't block writes, but scans the table twice, can't run in a transaction, and leaves an `INVALID` index if it fails — drop it and retry.
- [`REINDEX CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-reindex.html) (PostgreSQL 12+) rebuilds a bloated index without blocking writes.
- Index every [foreign key](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK) you join or cascade-delete on — PostgreSQL doesn't create them automatically.

## Transactions and isolation

### Isolation levels

| Level | [Dirty read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Dirty_reads) | [Non-repeatable read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Non-repeatable_reads) | [Phantom read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Phantom_reads) | Serialization anomaly |
|---|---|---|---|---|
| Read Uncommitted | not in PostgreSQL (runs as Read Committed) | possible | possible | possible |
| [Read Committed](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-READ-COMMITTED) (default) | — | possible | possible | possible |
| [Repeatable Read](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ) | — | — | not in PostgreSQL (the SQL standard allows it) | possible |
| [Serializable](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE) | — | — | — | — |

### Lost update and write skew

- Lost update: two read-modify-write cycles overwrite each other; Read Committed allows it — use an atomic `UPDATE ... SET n = n + 1`, [`SELECT ... FOR UPDATE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS), or a version check.
- [Write skew](https://en.wikipedia.org/wiki/Snapshot_isolation): two transactions read overlapping data and write different rows, together breaking an invariant (both doctors go off call); only Serializable or explicit locks prevent it.

### Read Committed re-check

- Each statement in [Read Committed](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-READ-COMMITTED) takes a new snapshot, so two `SELECT`s in one transaction can disagree.
- An `UPDATE` that waits on a row locked by a concurrent writer re-evaluates its `WHERE` against the newest committed version, then updates or skips it — it never sees rows that newly started matching.

### Repeatable Read and Serializable

- [Repeatable Read](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ) is [snapshot isolation](https://en.wikipedia.org/wiki/Snapshot_isolation): one snapshot from the first statement; updating a row a concurrent transaction changed fails with "could not serialize access", so no lost updates — but write skew is possible.
- Serializable is [SSI](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE): predicate (`SIReadLock`) tracking detects dangerous read-write cycles and aborts one transaction.
- Both abort with SQLSTATE [`40001`](https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html); the app must retry the whole transaction, not just the failed statement.

### Optimistic locking

- Add a [`version` column](https://en.wikipedia.org/wiki/Optimistic_concurrency_control): `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?`; zero rows updated means someone else won — reload and retry.
- Best when conflicts are rare; pessimistic locks when they're frequent.

### Errors inside a transaction

- After any error, the [transaction is aborted](https://www.postgresql.org/docs/current/tutorial-transactions.html): every later statement fails with "current transaction is aborted" until `ROLLBACK`.
- [`SAVEPOINT`](https://www.postgresql.org/docs/current/sql-savepoint.html) + `ROLLBACK TO SAVEPOINT` recovers part of the work; psql `ON_ERROR_ROLLBACK` and pgJDBC `autosave` wrap each statement in one, costing an extra round trip.

### Timeouts

- [`statement_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-STATEMENT-TIMEOUT) caps one statement; [`lock_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-LOCK-TIMEOUT) caps the wait for a lock.
- [`idle_in_transaction_session_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-IDLE-IN-TRANSACTION-SESSION-TIMEOUT) kills sessions left in an open transaction, which otherwise hold locks and block VACUUM cleanup.
- [`transaction_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-TRANSACTION-TIMEOUT) (PostgreSQL 17+) caps a whole transaction.
- All default to off; set them per role or per session rather than server-wide.

## MVCC and VACUUM

### Row versions

- An `UPDATE` writes a new row version and marks the old one dead; versions carry [`xmin`/`xmax`](https://www.postgresql.org/docs/current/ddl-system-columns.html#DDL-SYSTEM-COLUMNS-XMIN), and each [snapshot](https://www.postgresql.org/docs/current/mvcc-intro.html) sees only the versions committed before it.
- Plain `SELECT`s never block or wait for row writers; writers (and `FOR UPDATE`) still lock rows against each other, and DDL's `ACCESS EXCLUSIVE` lock blocks even `SELECT`.
- The new version needs a new entry in every index unless the update is [HOT](https://www.postgresql.org/docs/current/storage-hot.html), so wide-indexed, update-heavy tables pay heavy write amplification.

### HOT updates

- A [HOT update](https://www.postgresql.org/docs/current/storage-hot.html) skips index maintenance when no indexed column changed and the new version fits on the same page.
- A lower [`fillfactor`](https://www.postgresql.org/docs/current/sql-createtable.html#RELOPTION-FILLFACTOR) (e.g. 90) leaves free space per page to make HOT more likely on update-heavy tables.
- Indexing a frequently updated column (`updated_at`) disables HOT for every update that touches it; since PostgreSQL 16, columns covered only by BRIN indexes don't.

### VACUUM and autovacuum

- [VACUUM](https://www.postgresql.org/docs/current/routine-vacuuming.html) makes dead versions' space reusable but rarely shrinks the file; [`VACUUM FULL`](https://www.postgresql.org/docs/current/sql-vacuum.html) rewrites the table under an `ACCESS EXCLUSIVE` lock ([pg_repack](https://reorg.github.io/pg_repack/) does it online).
- [Autovacuum](https://www.postgresql.org/docs/current/routine-vacuuming.html#AUTOVACUUM) runs when dead rows exceed 50 + 20% of the table; since PostgreSQL 18 [`autovacuum_vacuum_max_threshold`](https://www.postgresql.org/docs/current/runtime-config-vacuum.html#GUC-AUTOVACUUM-VACUUM-MAX-THRESHOLD) caps that at 100 million rows. Large tables still need a lower per-table scale factor.
- Anything holding an old snapshot stops cleanup everywhere: long transactions, idle-in-transaction sessions, abandoned replication slots, and replicas with `hot_standby_feedback` — the result is bloat.

### Transaction ID wraparound

- [Transaction IDs](https://www.postgresql.org/docs/current/routine-vacuuming.html#VACUUM-FOR-WRAPAROUND) are 32-bit, so only ~2 billion are "in the past"; VACUUM freezes old rows so they stay visible.
- When a table's oldest unfrozen XID passes [`autovacuum_freeze_max_age`](https://www.postgresql.org/docs/current/runtime-config-vacuum.html#GUC-AUTOVACUUM-FREEZE-MAX-AGE) (200 million), an anti-wraparound vacuum runs even if autovacuum is off.
- With fewer than 3 million XIDs left, the server refuses new write transactions until a manual VACUUM catches up — an outage, usually caused by something blocking vacuum for weeks.

## Locking

### Table lock levels

| Statement | [Lock](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-TABLES) | Blocks |
|---|---|---|
| `SELECT` | `ACCESS SHARE` | only `ACCESS EXCLUSIVE` |
| `INSERT`, `UPDATE`, `DELETE` | `ROW EXCLUSIVE` | `SHARE` and stronger (plain `CREATE INDEX`) |
| `VACUUM`, `CREATE INDEX CONCURRENTLY`, `VALIDATE CONSTRAINT` | `SHARE UPDATE EXCLUSIVE` | itself and DDL, not reads or writes |
| `CREATE INDEX` | `SHARE` | writes |
| most `ALTER TABLE`, `DROP`, `TRUNCATE`, `VACUUM FULL` | `ACCESS EXCLUSIVE` | everything, including `SELECT` |

### DDL locks and the lock queue

- Most `ALTER TABLE` forms take an [`ACCESS EXCLUSIVE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-TABLES) lock. If it waits behind a long query, every later query queues behind it — a brief outage from a "fast" migration.
- Set [`lock_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-LOCK-TIMEOUT) (a few seconds) on migrations and retry; rollout patterns in [devops.md](devops.md).

### Safe schema changes

- [`ADD COLUMN`](https://www.postgresql.org/docs/current/sql-altertable.html#SQL-ALTERTABLE-NOTES) with a constant default is metadata-only since PostgreSQL 11; a volatile default (`clock_timestamp()`) rewrites the table.
- Changing a column's type usually rewrites the table and its indexes; widening `varchar(n)` or switching to `text` doesn't.
- Add foreign keys and `CHECK`s as [`NOT VALID`](https://www.postgresql.org/docs/current/sql-altertable.html#SQL-ALTERTABLE-DESC-ADD-TABLE-CONSTRAINT), then `VALIDATE CONSTRAINT`, which scans under `SHARE UPDATE EXCLUSIVE` without blocking writes.
- `SET NOT NULL` scans the table under `ACCESS EXCLUSIVE`, skipped if a validated `CHECK (col IS NOT NULL)` already proves it; since PostgreSQL 18, `NOT NULL` itself can be added `NOT VALID`.

### Row locks and queue tables

- [`SELECT ... FOR UPDATE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS) locks the rows it returns; `FOR NO KEY UPDATE` is weaker and doesn't block inserts of rows referencing them by foreign key.
- [`SKIP LOCKED`](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE) lets workers claim different rows of a queue table without blocking; `NOWAIT` errors instead of waiting.
- Row locks live in the row header on disk, not in memory: there's no limit on rows locked and no lock escalation, but locking writes to the page.

### Advisory locks

- [Advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS) are app-defined locks on a number, not a row — for leader election or job dedup without a table to lock.
- Session-level locks (`pg_advisory_lock`) persist until unlock or disconnect; transaction-level ones (`pg_advisory_xact_lock`) release at commit.
- Session-level locks break behind a transaction-mode pooler: the next transaction may run on a different server connection.

### Deadlocks

- Two transactions each hold a lock the other needs; after [`deadlock_timeout`](https://www.postgresql.org/docs/current/runtime-config-locks.html#GUC-DEADLOCK-TIMEOUT) (1 s) PostgreSQL [detects the cycle](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS) and aborts one.
- Prevent with a consistent lock order (e.g. update rows sorted by ID) and short transactions.

## Query planning and tuning

### Reading EXPLAIN

- [`EXPLAIN ANALYZE`](https://www.postgresql.org/docs/current/using-explain.html#USING-EXPLAIN-ANALYZE) executes the query (wrap writes in a rolled-back transaction); since PostgreSQL 18 it includes `BUFFERS` by default.
- Estimated vs actual rows far apart means stale or insufficient statistics — run [`ANALYZE`](https://www.postgresql.org/docs/current/sql-analyze.html) or add [extended statistics](https://www.postgresql.org/docs/current/planner-stats.html#PLANNER-STATS-EXTENDED) for correlated columns.
- Scan types: Seq Scan, Index Scan, Index Only Scan, and [Bitmap Heap Scan](https://www.postgresql.org/docs/current/indexes-bitmap-scans.html) (collects matches from one or more indexes, then reads pages in physical order).
- [`pg_stat_statements`](https://www.postgresql.org/docs/current/pgstatstatements.html) ranks normalized queries by total time — start tuning there.

### Why an index isn't used

- Low selectivity: when a filter matches a large share of rows, the planner prefers a [sequential scan](https://www.postgresql.org/docs/current/using-explain.html), since one sequential pass beats many random heap reads.
- `LIKE 'x%'` uses a B-tree only with C collation or [`text_pattern_ops`](https://www.postgresql.org/docs/current/indexes-opclass.html); `LIKE '%x'` needs a trigram GIN or GiST index ([`pg_trgm`](https://www.postgresql.org/docs/current/pgtrgm.html)).
- A function or implicit cast on the column, and `OR` across columns without an index on each, also defeat it.
- Small tables: a seq scan of a few pages is cheaper than any index.

### Join algorithms

| Join | Best when |
|---|---|
| [Nested loop](https://en.wikipedia.org/wiki/Nested_loop_join) | outer side small, inner side index-backed |
| [Hash join](https://en.wikipedia.org/wiki/Hash_join) | large equality joins without a useful index; builds on the smaller side |
| [Merge join](https://en.wikipedia.org/wiki/Sort-merge_join) | both inputs already sorted (e.g. from indexes) |

### Memory per query

- [`work_mem`](https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-WORK-MEM) (4 MB) applies per sort or hash node, per parallel worker; hashes get `work_mem × hash_mem_multiplier` (2.0) — one query can use several multiples, times every connection.
- A sort or hash that exceeds it spills to disk (`external merge` in `EXPLAIN ANALYZE`); raise it per session for reporting queries, not globally.

### Prepared statements and generic plans

- A [prepared statement](https://www.postgresql.org/docs/current/sql-prepare.html) runs its first five executions with custom plans, then switches to a cached generic plan if its estimated cost isn't much higher.
- On skewed data a generic plan can be badly wrong for rare values; [`plan_cache_mode = force_custom_plan`](https://www.postgresql.org/docs/current/runtime-config-query.html#GUC-PLAN-CACHE-MODE) forces replanning.
- Drivers may prepare implicitly: [pgJDBC](https://jdbc.postgresql.org/documentation/server-prepare/) after 5 executions of a statement, [pgx](https://pkg.go.dev/github.com/jackc/pgx/v5#hdr-Prepared_Statements) by default.

### Pagination and counting

- `OFFSET` still reads and discards every skipped row, so deep pages get slower; [keyset pagination](https://use-the-index-luke.com/no-offset) seeks by index — API side in [backend.md](backend.md).
- `count(*)` scans the table or an index (MVCC means no stored row count); for a rough number, read [`pg_class.reltuples`](https://www.postgresql.org/docs/current/catalog-pg-class.html).

## SQL gotchas

### Logical evaluation order

`FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT` — why a `SELECT` alias works in `ORDER BY` but not in `WHERE`.

### NULL and three-valued logic

- Any comparison with NULL — even `NULL = NULL` — is [UNKNOWN](https://en.wikipedia.org/wiki/Null_%28SQL%29#Comparisons_with_NULL_and_the_three-valued_logic_%283VL%29), and `WHERE` drops it; use `IS [NOT] NULL` or [`IS [NOT] DISTINCT FROM`](https://www.postgresql.org/docs/current/functions-comparison.html).
- [`NOT IN`](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-NOTIN) with a NULL in the list returns no rows — use [`NOT EXISTS`](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-EXISTS).
- [`COUNT(*)`](https://www.postgresql.org/docs/current/functions-aggregate.html) counts rows; `COUNT(col)`, `SUM`, `AVG`, `MIN`/`MAX` skip NULLs, but `array_agg`/`json_agg` keep them.
- A [`UNIQUE`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS) column accepts many NULLs; `UNIQUE NULLS NOT DISTINCT` (PostgreSQL 15+) allows only one.

### Window functions

- [`fn() OVER (PARTITION BY ... ORDER BY ...)`](https://www.postgresql.org/docs/current/tutorial-window.html) computes per row without collapsing rows.
- [`ROW_NUMBER`](https://www.postgresql.org/docs/current/functions-window.html) 1,2,3; `RANK` 1,1,3 (gaps); `DENSE_RANK` 1,1,2.
- The [default frame](https://www.postgresql.org/docs/current/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS) with `ORDER BY` is `RANGE ... CURRENT ROW`, which includes all peer rows with equal sort keys — use `ROWS` for a true running total.

### CTE materialization

- Since PostgreSQL 12, a non-recursive, side-effect-free CTE referenced once is [inlined](https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION) into the outer query; one referenced several times is materialized.
- `MATERIALIZED` / `NOT MATERIALIZED` override the default.

### Join pitfalls

- A null-rejecting condition on the right table in `WHERE` (`r.x = 1`, unlike `IS NULL` or `COALESCE`) discards the NULL-extended rows and turns a [`LEFT JOIN`](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-JOIN) into an inner join; put it in `ON`.
- Joining a parent to two one-to-many children multiplies rows (fan-out) and inflates `SUM`/`COUNT`; aggregate each child in a subquery first.
- [`EXISTS`](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-EXISTS) / `NOT EXISTS` are [semi-](https://en.wikipedia.org/wiki/Join_%28relational_algebra%29#Semijoin) and [anti-joins](https://en.wikipedia.org/wiki/Join_%28relational_algebra%29#Antijoin): they never duplicate rows, unlike `JOIN` + `DISTINCT`.

### Upsert and MERGE

- [`INSERT ... ON CONFLICT (...) DO UPDATE`](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT) replaces a racy check-then-write; it needs a unique index matching the conflict target, and `EXCLUDED.col` holds the proposed row.
- `ON CONFLICT DO NOTHING ... RETURNING` returns nothing for conflicting rows, so "get or create" needs a follow-up `SELECT`.
- [`MERGE`](https://www.postgresql.org/docs/current/sql-merge.html) (PostgreSQL 15+) doesn't handle concurrent inserts like `ON CONFLICT` does — it can fail with a unique violation.
- `MERGE ... RETURNING` exists since PostgreSQL 17; [`OLD`/`NEW` in `RETURNING`](https://www.postgresql.org/docs/current/dml-returning.html) (any DML) since 18.

## WAL and durability

### Write-ahead log

- A commit is durable once its [WAL](https://www.postgresql.org/docs/current/wal-intro.html) record is [fsynced](os.md); dirty data pages are flushed later ([checkpoints](https://www.postgresql.org/docs/current/wal-configuration.html), background writer), never before their WAL.
- Crash recovery only redoes WAL from the last checkpoint; uncommitted rows stay invisible by their commit status, so there's no undo phase.
- [Group commit](https://www.postgresql.org/docs/current/wal-configuration.html) batches many commits into one fsync.

### Checkpoints

- A checkpoint runs every [`checkpoint_timeout`](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-CHECKPOINT-TIMEOUT) (5 min) or when WAL reaches [`max_wal_size`](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-MAX-WAL-SIZE) (1 GB), whichever comes first.
- The first change to a page after a checkpoint logs the whole page ([`full_page_writes`](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-FULL-PAGE-WRITES)) to survive torn writes, so frequent checkpoints inflate WAL volume.
- Longer intervals mean less WAL and I/O but slower crash recovery.

### Commit durability levels

- [`synchronous_commit`](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-SYNCHRONOUS-COMMIT) picks how far a commit waits: `off` (doesn't wait for the local flush), `local`, `remote_write`, `on` (standby fsync), `remote_apply` (visible on standby); without `synchronous_standby_names`, every mode except `off` just waits for the local flush.
- `off` ([asynchronous commit](https://www.postgresql.org/docs/current/wal-async-commit.html)) can lose up to 3 × `wal_writer_delay` (600 ms by default) of commits on a crash, but never corrupts data — settable per transaction for low-value writes.
- `fsync = off` is different: a crash can corrupt the cluster.

### Backups and PITR

- Logical backups ([`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html)): portable across versions, slow to restore at scale. Physical ([`pg_basebackup`](https://www.postgresql.org/docs/current/app-pgbasebackup.html), snapshots): fast restore, same major version.
- [PITR](https://www.postgresql.org/docs/current/continuous-archiving.html) = physical base backup + archived [WAL](https://www.postgresql.org/docs/current/wal-intro.html) replayed to a chosen moment. Replicas are not backups — they replicate mistakes too.
- [Incremental backups](https://www.postgresql.org/docs/current/continuous-archiving.html#BACKUP-INCREMENTAL-BACKUP) (`pg_basebackup --incremental`, PostgreSQL 17+) copy only changed blocks; [`pg_combinebackup`](https://www.postgresql.org/docs/current/app-pgcombinebackup.html) reconstructs a full one.

## Replication and high availability

### Physical vs logical replication

- Physical ([streaming](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION)): ships [WAL](https://www.postgresql.org/docs/current/wal-intro.html) bytes; an exact, read-only copy of the whole cluster on the same major version, except `UNLOGGED` tables, which are empty on standbys.
- [Logical](https://www.postgresql.org/docs/current/logical-replication.html): row changes per table, works across major versions and subsets — used for zero-downtime upgrades and [CDC](distributed.md).
- Logical replication [doesn't copy](https://www.postgresql.org/docs/current/logical-replication-restrictions.html) DDL or sequence values, and `UPDATE`/`DELETE` need a [replica identity](https://www.postgresql.org/docs/current/sql-altertable.html#SQL-ALTERTABLE-REPLICA-IDENTITY) (usually the primary key).

### Synchronous replication

- [`synchronous_standby_names`](https://www.postgresql.org/docs/current/runtime-config-replication.html#GUC-SYNCHRONOUS-STANDBY-NAMES) lists standbys a commit waits for: `FIRST n (...)` by priority or `ANY n (...)` as a quorum.
- If the required standbys are down, commits hang rather than fail — list more candidates than `n`.
- Sync vs async trade-offs in [distributed.md](distributed.md).

### Replication slots

- A [replication slot](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION-SLOTS) keeps WAL (and, for logical slots, old catalog rows) until its consumer confirms it — a dead consumer fills the disk.
- Cap it with [`max_slot_wal_keep_size`](https://www.postgresql.org/docs/current/runtime-config-replication.html#GUC-MAX-SLOT-WAL-KEEP-SIZE) (PostgreSQL 13+, unlimited by default) or [`idle_replication_slot_timeout`](https://www.postgresql.org/docs/current/runtime-config-replication.html#GUC-IDLE-REPLICATION-SLOT-TIMEOUT) (PostgreSQL 18+, off by default); either invalidates the slot.
- Logical slots can be [synced to a standby](https://www.postgresql.org/docs/current/logicaldecoding-explanation.html#LOGICALDECODING-REPLICATION-SLOTS-SYNCHRONIZATION) (PostgreSQL 17+), so CDC survives a failover.

### Read replicas

- Async [hot standbys](https://www.postgresql.org/docs/current/hot-standby.html) lag, so a read after a write may miss it — route read-your-writes to the primary.
- Replaying a VACUUM that removes rows a standby query still needs cancels that query once replay has been held back for [`max_standby_streaming_delay`](https://www.postgresql.org/docs/current/runtime-config-replication.html#GUC-MAX-STANDBY-STREAMING-DELAY) (30 s) — a budget for the replay lag, not a per-query grace period.
- [`hot_standby_feedback`](https://www.postgresql.org/docs/current/runtime-config-replication.html#GUC-HOT-STANDBY-FEEDBACK) avoids those cancellations but holds back vacuum on the primary, causing bloat.

### Failover

- PostgreSQL has no built-in automatic failover; [Patroni](https://patroni.readthedocs.io/) and similar tools elect a leader through a consensus store (etcd) and fence the old primary.
- A demoted primary may have WAL the new one never got; [`pg_rewind`](https://www.postgresql.org/docs/current/app-pgrewind.html) discards it so the old primary can rejoin as a standby.
- With async replication, commits acknowledged but not yet shipped are lost on failover.

## Architecture and scaling

### Process model and memory

- Each connection is a separate backend [process](https://www.postgresql.org/docs/current/connect-estab.html) (several MB), so thousands of direct connections hurt — pool them.
- [`shared_buffers`](https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-SHARED-BUFFERS) (~25% of RAM is a common start) caches pages, and the OS page cache holds them again; [`effective_cache_size`](https://www.postgresql.org/docs/current/runtime-config-query.html#GUC-EFFECTIVE-CACHE-SIZE) is only a planner hint.
- Since PostgreSQL 18, sequential scans, bitmap heap scans, and vacuum read through [asynchronous I/O](https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-IO-METHOD) (`io_method = worker` by default; `io_uring` on Linux).

### Connection pooling

- [PgBouncer](https://www.pgbouncer.org/features.html) session mode keeps `SET` and session [advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS); transaction mode scales further but loses session state.
- Protocol-level prepared statements work in transaction mode since PgBouncer 1.21 when [`max_prepared_statements`](https://www.pgbouncer.org/config.html#max_prepared_statements) > 0 (default 0 before 1.24, now 200); SQL [`PREPARE`](https://www.postgresql.org/docs/current/sql-prepare.html) still doesn't.
- App-side pool sizing in [backend.md](backend.md).

### Table partitioning

- [Range](https://www.postgresql.org/docs/current/ddl-partitioning.html) (most common, by date), list, or hash; [partition pruning](https://www.postgresql.org/docs/current/ddl-partitioning.html#DDL-PARTITION-PRUNING) skips irrelevant partitions only when the query filters on the partition key.
- Dropping an old partition is a cheap metadata change, unlike a bloating bulk `DELETE`, but takes an [`ACCESS EXCLUSIVE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-TABLES) lock on the parent — [`DETACH PARTITION CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-altertable.html#SQL-ALTERTABLE-DETACH-PARTITION) (PostgreSQL 14+) first avoids that.
- [Unique constraints must include the partition key](https://www.postgresql.org/docs/current/ddl-partitioning.html#DDL-PARTITIONING-DECLARATIVE-LIMITATIONS), so a global unique ID across partitions isn't enforced.

### Materialized views

- A [materialized view](https://www.postgresql.org/docs/current/rules-materializedviews.html) stores a query result for fast reads that stays stale until refreshed — no incremental refresh built in.
- [`REFRESH MATERIALIZED VIEW CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html) doesn't block reads but needs a unique index and is slower.

## Schema design

### Normalization

- [1NF](https://en.wikipedia.org/wiki/First_normal_form) atomic values → [2NF](https://en.wikipedia.org/wiki/Second_normal_form) no partial-key dependency → [3NF](https://en.wikipedia.org/wiki/Third_normal_form) no transitive dependency through non-key columns: each fact stored once.
- [BCNF](https://en.wikipedia.org/wiki/Boyce%E2%80%93Codd_normal_form) is stricter: every nontrivial dependency's determinant is a superkey; 3NF still allows it when the dependent column is part of a candidate key.
- [Denormalize](https://en.wikipedia.org/wiki/Denormalization) measured hot paths only (copied columns, counters, materialized views), accepting harder writes.

### Keys and sequences

- Prefer [`GENERATED ALWAYS AS IDENTITY`](https://www.postgresql.org/docs/current/ddl-identity-columns.html) (PostgreSQL 10+) over `serial`; use `bigint`, since `int` runs out at ~2.1 billion.
- [Sequences](https://www.postgresql.org/docs/current/functions-sequence.html) are non-transactional: `nextval` is never rolled back, so IDs have gaps.
- [UUIDv4](https://www.rfc-editor.org/rfc/rfc9562#section-5.4) scatters inserts across the B-tree; [UUIDv7](https://www.rfc-editor.org/rfc/rfc9562#section-5.7) is time-ordered and native via [`uuidv7()`](https://www.postgresql.org/docs/current/functions-uuid.html) since PostgreSQL 18 — ID schemes in [distributed.md](distributed.md).

### Constraints and soft deletes

- [`FOREIGN KEY`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK), [`CHECK`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-CHECK-CONSTRAINTS), and [`UNIQUE`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS) are the last line of defense — application checks alone race.
- [Exclusion constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION) (`EXCLUDE USING gist (room WITH =, during WITH &&)`) forbid overlapping bookings; since PostgreSQL 18 a primary key or unique constraint can say `WITHOUT OVERLAPS`.
- Soft deletes (`deleted_at`) keep rows for undo and audit; a [partial unique index](https://www.postgresql.org/docs/current/indexes-partial.html) (`WHERE deleted_at IS NULL`) frees the value for reuse, so an undelete can then conflict.

### JSONB

- [`jsonb`](https://www.postgresql.org/docs/current/datatype-json.html) is parsed binary: faster to query and indexable, but drops duplicate keys (last wins), key order, and whitespace; `json` keeps the text as is.
- A [GIN index](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING) with the default `jsonb_ops` supports key-existence and containment; `jsonb_path_ops` is smaller and faster but supports only containment and path queries.
- Updating one key rewrites the whole value; columns you filter or join on belong in real columns.

### Row size and TOAST

- Pages are 8 KB; values that push a row past ~2 KB are compressed or moved out of line by [TOAST](https://www.postgresql.org/docs/current/storage-toast.html), up to 1 GB per field.
- `SELECT *` fetches and decompresses every toasted column; select only what you need.
- [Generated columns](https://www.postgresql.org/docs/current/ddl-generated-columns.html) are virtual (computed on read) by default since PostgreSQL 18; `STORED` computes on write and takes space.

### Common type choices

- [`timestamptz`](https://www.postgresql.org/docs/current/datatype-datetime.html) stores an instant in UTC and stores no time zone; `timestamp` ignores zones entirely — time handling in [backend.md](backend.md).
- [`text`](https://www.postgresql.org/docs/current/datatype-character.html) and `varchar(n)` perform the same; `char(n)` pads with spaces.
- [`numeric`](https://www.postgresql.org/docs/current/datatype-numeric.html#DATATYPE-NUMERIC-DECIMAL) is exact for money; `float8` rounds, and the `money` type depends on `lc_monetary`.
