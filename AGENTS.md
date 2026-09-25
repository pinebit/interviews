# AGENTS.md

This repo is a set of concise topic briefs for technical interview prep. The reader skims them repeatedly to memorize key points.

## Structure

- `docs/topics/` — one brief per topic (e.g. `docs/topics/golang.md`).
- `docs/index.md` — the reading site's homepage.
- `scripts/lint_briefs.py` — checks the format rules below; CI runs it with the strict site build on every pull request.
- `.agents/skills/quiz/` — the `quiz` skill, which quizzes the user on brief concepts. `.claude/skills/quiz` is a symlink to it so Claude Code and Codex share one copy.
- File names are lowercase, single word or kebab-case.
- `README.md` and `docs/index.md` list every topic with a link and a one-line summary, and `zensical.toml` lists it in the site nav. Update all three when adding or renaming a file.
- Topics are grouped the same way in all three: **Fundamentals**, **Languages**, **Web**, **Infrastructure**, **Domains** — groups ordered by breadth, topics alphabetical within a group.

## Target format

### File layout

```markdown
# Go

What experienced Go engineers forget before an interview, grouped by subtopic.

## Concurrency

### Scheduler (GMP)

- Goroutines (G) run on OS threads (M) through logical processors (P); **`GOMAXPROCS`** = number of Ps.
- `GOMAXPROCS` respects the container CPU limit **since Go 1.25**; before that it used the host CPU count.
- Blocking syscall → the M is parked and the P moves to another M; network I/O goes through the **netpoller** and doesn't hold a thread.
- Preemption is asynchronous (signal-based) **since Go 1.14**, so tight loops no longer starve the scheduler.

### Channel axioms

| Operation | nil channel | closed channel |
|---|---|---|
| send | blocks forever | **panics** |
| receive | blocks forever | zero value, `ok == false` |
| close | panics | **panics** |
```

### Rules

- **Title**: `# <Topic>` (e.g. `# Go`, `# Distributed Systems`). No "Cheatsheet" suffix.
- **Intro**: one line: "What experienced <topic> engineers forget before an interview, grouped by subtopic." Adjust wording for non-language topics (e.g. "Key system design building blocks and trade-offs, grouped by subtopic.").
- **`##` = subtopic** (Concurrency, Memory management, …). Named, not numbered. Ordered by how often the area comes up in interviews. At least 2 concepts each; fold a lone concept into a related subtopic.
- **`###` = concept** — a noun phrase (`### Scheduler (GMP)`, `### Isolation anomalies`), never a question, no numbers. Each concept should be self-contained (no "as above"): the quiz picks `###` headings at random.
- **Body of a concept**: 2–6 bullets, or one short paragraph, or one compact table. One fact per bullet, one line where possible.
- **Tables** for comparisons and matrices (channel axioms, isolation levels vs anomalies, deployment strategies, promise combinators).
- **Code** only when shorter than prose; ≤ 6 lines.
- **Bold** the term or number worth memorizing — at most 3 per concept, not counting tables.
- **Versions**: note when behavior changed ("since Go 1.22", "Python 3.14+", "Pectra, May 2025").
- **Cross-topic**: the owner file covers a concept in full; another file may overlap briefly from its own angle and links to the owner: `see [security.md](security.md)` (rules in Topic ownership). Link to files, not anchors (the strict build validates anchors; only use one if you've checked the slug).
- Suggested size: 5–10 sections, 3–8 concepts each. Shorter is better if nothing is lost.

### What to include

Keep facts that a working engineer knew once but loses without daily use:

- **Internals and mechanisms**: how the scheduler, GC, MVCC, event loop, consensus actually work.
- **Gotchas and edge cases**: nil interface ≠ nil, `NOT IN` with a NULL, mutable default args, microtask ordering.
- **Exact numbers and thresholds**: `append` growth factor, Web Vitals thresholds, gas costs, Raft majority, TTLs.
- **Trade-off tables**: when to pick A vs B, stated as conditions, not opinions.
- **Version changes**: behavior that differs between versions still seen in production.
- **Named patterns and algorithms** an interviewer expects you to name (outbox, saga, token bucket, CEI, expand/contract).

### What to cut

- Syntax and language basics (`var`/`let`/`const`, `*args`, `make` vs `new`, struct vs enum, destructuring).
- Definitions any mid-level engineer knows (authn vs authz, what a container is, what CI/CD stands for).
- Lists of standard-library functions or utility types unless one has a non-obvious behavior.
- Generic advice ("write tests", "use least privilege") without a concrete mechanism.
- History and trivia that nobody asks about (e.g. "what is a zero-day").

## Topic ownership

Each concept has one owner file that covers it in full. Other files may overlap where the concept matters to them too: a bullet or a short concept stating what matters from their angle (database says the WAL is only durable after `fsync`; os explains `fsync`), with a link to the owner for the rest. Don't copy the owner's concept wholesale — copies drift apart, and the quiz would ask the same question twice.

| Concept | Owner | Referenced from |
|---|---|---|
| Consistency models, replication theory, consensus, clocks, delivery semantics, sagas, CRDTs | distributed | database, system, backend |
| Retries, backoff, circuit breakers, backpressure, tail latency | distributed | backend, system |
| Isolation levels, MVCC, indexes, WAL, DB replication setup, pooling | database | backend, system |
| Caching strategies, rate-limiting algorithms, load balancing, CDN, observability (SLI/SLO) | system | backend, devops |
| REST/gRPC/GraphQL, pagination, idempotency keys, outbox, graceful shutdown, N+1 | backend | system, database |
| AuthN, sessions, OAuth/OIDC, JWT, XSS, CSRF, CORS, clickjacking, crypto, TLS | security | backend, frontend |
| Containers, Kubernetes, cloud, IaC, deployment strategies, zero-downtime migrations | devops | backend, database |
| Browser event loop, JS language semantics | javascript | frontend, typescript |
| Rendering strategies, browser pipeline, Web Vitals, HTTP caching in the browser, React | frontend | javascript |
| asyncio event loop | python | — |
| TCP/UDP, HTTP versions, QUIC, DNS, IP addressing, NAT, MTU, BGP/anycast | networking | backend, system, devops |
| Processes, signals, scheduling, virtual memory, OOM, file descriptors, epoll/io_uring, fsync, locks | os | devops, database, golang |
| Container internals (namespaces, cgroups), Kubernetes graceful shutdown | devops | os, backend |
| Solidity language, storage layout, calls and ABI, contract security, gas optimization, upgradeability | solidity | ethereum |
| EVM execution, gas and fee market, transaction types, signatures and token standards, DeFi (flash loans, oracle manipulation) and MEV | ethereum | solidity |

## Style

- Concise and accurate over exhaustive. Cut anything that doesn't help recall.
- Use **bold** for the one or two terms worth memorizing in each answer.
- No filler, no marketing tone, no emojis.
- Verify facts against current language/tool versions; note the version when behavior changed (e.g. "since Go 1.22").
