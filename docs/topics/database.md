# Databases

What experienced database engineers forget before an interview, grouped by subtopic. For SQL vs NoSQL and the scaling ladder, see [system.md](system.md); for replication theory and sharding, see [distributed.md](distributed.md).

## Indexes

### B+tree indexes

- The default index is a [B+tree](https://en.wikipedia.org/wiki/B%2B_tree): balanced, sorted, O(log n), serves range scans and `ORDER BY`.
- [Clustered](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) (InnoDB): rows are stored in primary-key order and secondary indexes point to the PK. [Heap](https://www.postgresql.org/docs/current/storage-page-layout.html) (PostgreSQL): rows are unordered and indexes point to a physical location ([`ctid`](https://www.postgresql.org/docs/current/ddl-system-columns.html#DDL-SYSTEM-COLUMNS-CTID)).

### Composite indexes

- [Leftmost-prefix rule](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html): `(a, b, c)` seeks efficiently on `a`, `a,b`, `a,b,c` — not on `b` alone.
- [Skip scan](https://dev.mysql.com/doc/refman/8.4/en/range-optimization.html#range-access-skip-scan) (MySQL 8.0.13+, [PostgreSQL 18+](https://www.postgresql.org/docs/current/indexes-multicolumn.html)) serves `b` alone by probing each distinct `a`; cheap only when `a` has few values.
- Put equality columns first, range columns last; columns after a range condition only filter inside the scanned range (unless skip scan applies).

### Covering indexes

- A [covering index](https://www.postgresql.org/docs/current/indexes-index-only-scans.html) holds every column the query needs, enabling an index-only scan ([`INCLUDE`](https://www.postgresql.org/docs/current/sql-createindex.html) adds payload columns in PostgreSQL).
- PostgreSQL still checks the [visibility map](https://www.postgresql.org/docs/current/storage-vm.html); recently modified pages force heap visits until [VACUUM](https://www.postgresql.org/docs/current/routine-vacuuming.html) runs.

### Partial and expression indexes

- [Partial](https://www.postgresql.org/docs/current/indexes-partial.html) (`WHERE deleted_at IS NULL`) and [expression](https://www.postgresql.org/docs/current/indexes-expressional.html) (`ON lower(email)`) indexes cover only what queries use.
- [Sargability](https://en.wikipedia.org/wiki/Sargable): a function or implicit cast on an indexed column (`WHERE lower(email) = ...`) blocks index use unless a matching expression index exists.

### Specialized index types

| Index | Use for |
|---|---|
| [GIN](https://www.postgresql.org/docs/current/gin.html) | full-text, JSONB, arrays ([inverted index](https://en.wikipedia.org/wiki/Inverted_index)) |
| [GiST](https://www.postgresql.org/docs/current/gist.html) | geometry, ranges, nearest neighbor |
| [BRIN](https://www.postgresql.org/docs/current/brin.html) | huge, naturally ordered tables (append-only time series); tiny |
| [Hash](https://www.postgresql.org/docs/current/hash-index.html) | equality only |

### Building indexes online

- Plain `CREATE INDEX` blocks writes for the whole build; [`CREATE INDEX CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY) doesn't, but is slower, can't run in a transaction, and leaves an `INVALID` index if it fails.
- Index every [foreign key](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK) you join or cascade-delete on — PostgreSQL doesn't create them automatically.

## Transactions and isolation

### Anomalies × isolation levels

| Level | [Dirty read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Dirty_reads) | [Non-repeatable read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Non-repeatable_reads) | [Phantom read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Phantom_reads) |
|---|---|---|---|
| [Read Uncommitted](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Read_uncommitted) | possible | possible | possible |
| [Read Committed](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Read_committed) | — | possible | possible |
| [Repeatable Read](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Repeatable_reads) | — | — | possible (per SQL standard) |
| [Serializable](https://en.wikipedia.org/wiki/Isolation_%28database_systems%29#Serializable) | — | — | — |

### Lost update and write skew

- Lost update: two read-modify-write cycles overwrite each other.
- [Write skew](https://en.wikipedia.org/wiki/Snapshot_isolation): two transactions read overlapping data and write different rows, together breaking an invariant (both doctors go off call).

### PostgreSQL isolation

- Default: [Read Committed](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-READ-COMMITTED); [Repeatable Read](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ) is [snapshot isolation](https://en.wikipedia.org/wiki/Snapshot_isolation) — no phantoms, and a concurrent update of the same row aborts (no lost update), but write skew is possible.
- Serializable is [SSI](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE): it prevents write skew by aborting with a serialization error, so the app must retry.

### InnoDB isolation and MVCC

- Default: [Repeatable Read](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html#isolevel_repeatable-read) with [next-key locks](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html#innodb-next-key-locks) (record + gap) on locking reads, blocking many phantoms.
- Plain `SELECT` reads the [snapshot](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html), but `UPDATE` sees the latest committed row — lost updates slip through without [`SELECT ... FOR UPDATE`](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html).
- Updates happen in place; older versions are rebuilt from the [undo log](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html), and a long transaction makes undo history grow.

## MVCC and locking

### PostgreSQL MVCC

- Plain `SELECT`s read a [snapshot](https://www.postgresql.org/docs/current/mvcc-intro.html) and neither block nor wait for row writes; writers (and `FOR UPDATE`) still lock rows against each other.
- Old row versions stay in the table, tagged [`xmin`/`xmax`](https://www.postgresql.org/docs/current/ddl-system-columns.html#DDL-SYSTEM-COLUMNS-XMIN); [VACUUM](https://www.postgresql.org/docs/current/routine-vacuuming.html) reclaims them, and a long-running transaction blocks it, causing bloat.
- [XID wraparound](https://www.postgresql.org/docs/current/routine-vacuuming.html#VACUUM-FOR-WRAPAROUND) (32-bit transaction IDs) forces aggressive anti-wraparound vacuuming.
- [HOT updates](https://www.postgresql.org/docs/current/storage-hot.html) skip index maintenance when no indexed column changed and the page has room.

### Row locks, queue tables, advisory locks

- [`SELECT ... FOR UPDATE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS) locks the rows it returns; [`SKIP LOCKED`](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE) lets workers claim different rows of a queue table without blocking.
- PostgreSQL [advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS) are app-defined locks on a number, not a row — for leader election or job dedup without a table to lock.

### Optimistic locking

- Add a [`version` column](https://en.wikipedia.org/wiki/Optimistic_concurrency_control): `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?`; zero rows updated means someone else won — reload and retry.
- Best when conflicts are rare; pessimistic locks when they're frequent.

### Deadlocks

- Two transactions each hold a lock the other needs; the database [detects the cycle](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS) and aborts one.
- Prevent with a consistent lock order and short transactions.

### DDL locks and the lock queue

- Most `ALTER TABLE` forms take an [`ACCESS EXCLUSIVE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-TABLES) lock. If it waits behind a long query, every later query queues behind it — a brief outage from a "fast" migration.
- Set [`lock_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-LOCK-TIMEOUT) (a few seconds) on migrations and retry; rollout patterns in [devops.md](devops.md).

## Storage engines and durability

### B-tree vs LSM-tree

| | [B-tree](https://en.wikipedia.org/wiki/B-tree) (PostgreSQL, InnoDB) | [LSM-tree](https://en.wikipedia.org/wiki/Log-structured_merge-tree) ([RocksDB](https://rocksdb.org/), [Cassandra](https://cassandra.apache.org/doc/latest/cassandra/architecture/storage-engine.html)) |
|---|---|---|
| Writes | in-place page updates, random I/O | append to [memtable](https://cassandra.apache.org/doc/latest/cassandra/architecture/storage-engine.html#memtables) → flush immutable [SSTables](https://cassandra.apache.org/doc/latest/cassandra/architecture/storage-engine.html#sstables) |
| Reads | one tree walk, predictable | may check several files; [bloom filters](https://en.wikipedia.org/wiki/Bloom_filter) skip most |
| Background work | page splits, [vacuum](https://www.postgresql.org/docs/current/routine-vacuuming.html) | [compaction](https://github.com/facebook/rocksdb/wiki/Compaction) |
| Fits | read-heavy, range scans | write-heavy |

- Compaction strategy trades [read, write, and space amplification](https://smalldatum.blogspot.com/2015/11/read-write-space-amplification-pick-2_23.html) against each other.

### Write-ahead log

- A commit is durable once its [WAL](https://www.postgresql.org/docs/current/wal-intro.html) record is [fsynced](os.md); dirty data pages are flushed later ([checkpoints](https://www.postgresql.org/docs/current/wal-configuration.html), background writer), never before their WAL.
- Crash recovery replays WAL from the last checkpoint: PostgreSQL only redoes (uncommitted rows stay invisible by commit status); InnoDB redoes, then rolls back with [undo](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html).
- [Group commit](https://www.postgresql.org/docs/current/wal-configuration.html) batches many commits into one fsync.

### Backups and PITR

- Logical backups ([`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html)): portable, slow to restore at scale. Physical ([`pg_basebackup`](https://www.postgresql.org/docs/current/app-pgbasebackup.html), snapshots): fast restore, same major version.
- [PITR](https://www.postgresql.org/docs/current/continuous-archiving.html) = physical base backup + [WAL](https://www.postgresql.org/docs/current/wal-intro.html) replayed to a chosen moment. Replicas are not backups — they replicate mistakes too.

## Query execution and tuning

### Logical evaluation order

`FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT` — why a `SELECT` alias works in `ORDER BY` but not in `WHERE`.

### Why an index isn't used

- Low selectivity: when a filter matches a large share of rows, the planner prefers a [sequential scan](https://www.postgresql.org/docs/current/using-explain.html), since one sequential pass beats many random heap reads.
- `LIKE 'x%'` uses a B-tree only with C collation or [`text_pattern_ops`](https://www.postgresql.org/docs/current/indexes-opclass.html); `LIKE '%x'` needs a trigram GIN or GiST index ([`pg_trgm`](https://www.postgresql.org/docs/current/pgtrgm.html)).
- A function or implicit cast on the column, and `OR` across columns without an index on each, also defeat it.
- Stale statistics show up in [`EXPLAIN ANALYZE`](https://www.postgresql.org/docs/current/using-explain.html#USING-EXPLAIN-ANALYZE) as estimated vs actual rows far apart — run [`ANALYZE`](https://www.postgresql.org/docs/current/sql-analyze.html); also watch for sorts or hashes spilling to disk.
- Scan types: Seq Scan, Index Scan, Index Only Scan, and [Bitmap Heap Scan](https://www.postgresql.org/docs/current/indexes-bitmap-scans.html) (collects matches from one or more indexes, then reads pages in physical order).
- `OFFSET` still reads and discards every skipped row, so deep pages get slower; [keyset pagination](https://use-the-index-luke.com/no-offset) seeks by index — API side in [backend.md](backend.md).

### Join algorithms

| Join | Best when |
|---|---|
| [Nested loop](https://en.wikipedia.org/wiki/Nested_loop_join) | outer side small, inner side index-backed |
| [Hash join](https://en.wikipedia.org/wiki/Hash_join) | large equality joins without a useful index; builds on the smaller side |
| [Merge join](https://en.wikipedia.org/wiki/Sort-merge_join) | both inputs already sorted (e.g. from indexes) |

## SQL gotchas

### NULL and three-valued logic

- Any comparison with NULL — even `NULL = NULL` — is [UNKNOWN](https://en.wikipedia.org/wiki/Null_%28SQL%29#Comparisons_with_NULL_and_the_three-valued_logic_%283VL%29), and `WHERE` drops it; use `IS [NOT] NULL` or [`IS [NOT] DISTINCT FROM`](https://www.postgresql.org/docs/current/functions-comparison.html).
- [`NOT IN`](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-NOTIN) with a NULL in the list returns no rows — use [`NOT EXISTS`](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-EXISTS).
- [`COUNT(*)`](https://www.postgresql.org/docs/current/functions-aggregate.html) counts rows; `COUNT(col)`, `SUM`, `AVG`, `MIN`/`MAX` skip NULLs, but `array_agg`/`json_agg` keep them.

### Window functions

- [`fn() OVER (PARTITION BY ... ORDER BY ...)`](https://www.postgresql.org/docs/current/tutorial-window.html) computes per row without collapsing rows.
- [`ROW_NUMBER`](https://www.postgresql.org/docs/current/functions-window.html) 1,2,3; `RANK` 1,1,3 (gaps); `DENSE_RANK` 1,1,2.
- The [default frame](https://www.postgresql.org/docs/current/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS) with `ORDER BY` is `RANGE ... CURRENT ROW`, which includes all peer rows with equal sort keys — use `ROWS` for a true running total.

### CTE materialization

- Since PostgreSQL 12, a non-recursive, side-effect-free CTE referenced once is [inlined](https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION) into the outer query; one referenced several times is materialized.
- `MATERIALIZED` / `NOT MATERIALIZED` override the default.

### Join pitfalls

- A condition on the right table in `WHERE` (other than `IS NULL`) discards the NULL-extended rows and turns a [`LEFT JOIN`](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-JOIN) into an inner join; put it in `ON`.
- Joining a parent to two one-to-many children multiplies rows (fan-out) and inflates `SUM`/`COUNT`; aggregate each child in a subquery first.
- [`EXISTS`](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-EXISTS) / `NOT EXISTS` are [semi-](https://en.wikipedia.org/wiki/Join_%28relational_algebra%29#Semijoin) and [anti-joins](https://en.wikipedia.org/wiki/Join_%28relational_algebra%29#Antijoin): they never duplicate rows, unlike `JOIN` + `DISTINCT`.

### Upsert

[`INSERT ... ON CONFLICT (...) DO UPDATE`](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT) (PostgreSQL) / [`ON DUPLICATE KEY UPDATE`](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html) (MySQL) replaces a racy check-then-write.

## Non-relational stores

### Redis

- Commands execute on one thread, so each command (and [Lua script](https://redis.io/docs/latest/develop/programmability/eval-intro/) or [`MULTI` block](https://redis.io/docs/latest/develop/using-commands/transactions/)) is atomic; a slow command ([`KEYS *`](https://redis.io/docs/latest/commands/keys/), big `SMEMBERS`) blocks everyone.
- Structures: strings, hashes, lists, sets, [sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/) ([skip list](https://en.wikipedia.org/wiki/Skip_list) + hash — leaderboards, rate limiters), [streams](https://redis.io/docs/latest/develop/data-types/streams/), [HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/).
- Redis Cluster splits keys into [16,384 hash slots](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/); multi-key operations need the same slot, forced with [hash tags](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/#hash-tags) (`{user42}:cart`).

### Redis persistence and replication

- [RDB](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/): periodic fork + snapshot ([copy-on-write](https://en.wikipedia.org/wiki/Copy-on-write)), loses writes since the last one. [AOF](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/#append-only-file): logs every write; `appendfsync everysec` (default) loses up to ~1 s.
- Replication is [asynchronous](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/) — failover can drop acknowledged writes.

### Redis eviction, expiry, and messaging

- [`maxmemory-policy`](https://redis.io/docs/latest/develop/reference/eviction/#eviction-policies) defaults to `noeviction`: at the memory limit, writes fail with an OOM error.
- Caches use `allkeys-lru` or `allkeys-lfu`; `volatile-*` policies evict only keys with a TTL, so without TTLs they behave like `noeviction`.
- Expired keys are removed [lazily](https://redis.io/docs/latest/commands/expire/) on access plus by background sampling, so memory lags behind expirations.
- [Pub/sub](https://redis.io/docs/latest/develop/pubsub/) is fire-and-forget (offline subscribers miss messages); [Streams](https://redis.io/docs/latest/develop/data-types/streams/) persist entries, with consumer groups, acknowledgments, and redelivery of pending entries.

### Document stores (MongoDB)

- [Embed](https://www.mongodb.com/docs/manual/data-modeling/embedding/) data that is read together (one read, atomic update); reference unbounded or shared data — a document is capped at [16 MB](https://www.mongodb.com/docs/manual/reference/limits/#bson-documents).
- Single-document writes are atomic; [multi-document transactions](https://www.mongodb.com/docs/manual/core/transactions/) (replica sets since 4.0, sharded clusters since 4.2) cost more, so design for single-document atomicity.
- [Write concern](https://www.mongodb.com/docs/manual/reference/write-concern/) `w: "majority"` is the default since 5.0 (except some arbiter setups); `w: 1` acknowledges before replication, so a failover can roll back acknowledged writes.
- A query without a matching index scans the collection ([`COLLSCAN`](https://www.mongodb.com/docs/manual/reference/explain-results/#collection-scan)); order compound index keys by the [ESR rule](https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/): Equality, Sort, Range.

### Wide-column key design (Cassandra, DynamoDB)

- The [partition key](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) picks the node; the sort/clustering key orders rows inside the partition — an efficient query must supply the partition key; otherwise it's a full scan (DynamoDB [`Scan`](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Scan.html), Cassandra [`ALLOW FILTERING`](https://cassandra.apache.org/doc/latest/cassandra/developing/cql/dml.html#allow-filtering)) or a secondary index.
- Model [tables per query](https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/index.html) (denormalized), not per entity; unbounded partitions (all events of a popular user) become hot and huge — add a time bucket to the key.
- Deletes write [tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html), which slow reads until [compaction](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/index.html) purges them.

### Search engines and inverted indexes

- An [inverted index](https://en.wikipedia.org/wiki/Inverted_index) maps each term to the list of documents containing it; scoring is [BM25](https://en.wikipedia.org/wiki/Okapi_BM25).
- Elasticsearch/OpenSearch are [near-real-time](https://www.elastic.co/docs/manage-data/data-store/near-real-time-search) (new docs searchable after a refresh, ~1 s default), and the primary shard count is fixed at index creation — resize by reindexing or [split](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-indices-split)/shrink.
- Treat the search index as a derived store, fed by [CDC](distributed.md) from the source of truth.

## Schema design

### Normalization

- [1NF](https://en.wikipedia.org/wiki/First_normal_form) atomic values → [2NF](https://en.wikipedia.org/wiki/Second_normal_form) no partial-key dependency → [3NF](https://en.wikipedia.org/wiki/Third_normal_form) no transitive dependency through non-key columns: each fact stored once.
- [BCNF](https://en.wikipedia.org/wiki/Boyce%E2%80%93Codd_normal_form) is stricter: every nontrivial dependency's determinant is a superkey; 3NF still allows it when the dependent column is part of a candidate key.
- [Denormalize](https://en.wikipedia.org/wiki/Denormalization) measured hot paths only (copied columns, counters, [materialized views](https://www.postgresql.org/docs/current/rules-materializedviews.html)), accepting harder writes.

### Surrogate keys

- Auto-increment bigint: compact and ordered, but reveals counts and needs one sequence.
- [UUIDv4](https://www.rfc-editor.org/rfc/rfc9562#section-5.4) scatters inserts across the B-tree; [UUIDv7](https://www.rfc-editor.org/rfc/rfc9562#section-5.7) is time-ordered and native via [`uuidv7()`](https://www.postgresql.org/docs/current/functions-uuid.html) since PostgreSQL 18 — ID schemes in [distributed.md](distributed.md).

### Constraints and soft deletes

- [`FOREIGN KEY`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK), [`CHECK`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-CHECK-CONSTRAINTS), and [`UNIQUE`](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS) are the last line of defense — application checks alone race.
- Soft deletes (`deleted_at`) keep deleted rows for undo and audit; a [partial unique index](https://www.postgresql.org/docs/current/indexes-partial.html) (`WHERE deleted_at IS NULL`) frees the value for reuse, so an undelete can then conflict.

## Scaling

### Physical vs logical replication

- Physical ([streaming](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION)): ships [WAL](https://www.postgresql.org/docs/current/wal-intro.html) bytes, exact copy, same major version.
- [Logical](https://www.postgresql.org/docs/current/logical-replication.html): row changes per table, works across versions and subsets, feeds [CDC](distributed.md).
- PostgreSQL [`synchronous_commit`](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-SYNCHRONOUS-COMMIT) picks how far a commit waits (`remote_write`, `on`, `remote_apply`); sync vs async trade-offs are in [distributed.md](distributed.md).

### Table partitioning

- [Range](https://www.postgresql.org/docs/current/ddl-partitioning.html) (most common, by date), list, or hash; [partition pruning](https://www.postgresql.org/docs/current/ddl-partitioning.html#DDL-PARTITION-PRUNING) skips irrelevant partitions.
- Dropping an old partition is a cheap metadata change, unlike a bloating bulk `DELETE`, but takes an [`ACCESS EXCLUSIVE`](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-TABLES) lock on the parent — [`DETACH PARTITION CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-altertable.html#SQL-ALTERTABLE-DETACH-PARTITION) (PostgreSQL 14+) first avoids that.
- PostgreSQL [unique constraints must include the partition key](https://www.postgresql.org/docs/current/ddl-partitioning.html#DDL-PARTITIONING-DECLARATIVE-LIMITATIONS).

### Connection pooling

- Each PostgreSQL connection is a [process](https://www.postgresql.org/docs/current/connect-estab.html) (a few MB), so thousands of direct connections hurt — pool them.
- [PgBouncer](https://www.pgbouncer.org/features.html) session mode keeps `SET` and [advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS); transaction mode scales further but loses session state; protocol-level prepared statements work in it since PgBouncer 1.21 when [`max_prepared_statements`](https://www.pgbouncer.org/config.html#max_prepared_statements) > 0 (default 0 before 1.24, now 200); SQL [`PREPARE`](https://www.postgresql.org/docs/current/sql-prepare.html) still doesn't.

### OLTP vs OLAP

- [OLAP](https://en.wikipedia.org/wiki/Online_analytical_processing): [column storage](https://en.wikipedia.org/wiki/Column-oriented_DBMS), compression, vectorized scans of few columns over many rows, [star schemas](https://en.wikipedia.org/wiki/Star_schema) (facts + dimensions).
- [Materialized views](https://www.postgresql.org/docs/current/rules-materializedviews.html) store a query result for fast reads that stay stale until refresh; [`REFRESH MATERIALIZED VIEW CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html) avoids blocking reads but needs a unique index.
