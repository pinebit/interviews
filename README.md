# Interview Refresher

Topic briefs on what engineers forget before technical interviews:

[Read the briefs online](https://pinebit.github.io/interviews/).

Each topic in `docs/topics/` is a brief grouped by subtopic, covering what an experienced engineer tends to forget before an interview. Skim them to memorize.

## Topics

- [Go](docs/topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, testing and profiling
- [Algorithms](docs/topics/algorithms.md) — complexity, array patterns, sorting, data structures, graphs, dynamic programming, greedy methods
- [Distributed Systems](docs/topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, stream processing
- [Ethereum](docs/topics/ethereum.md) — accounts and transactions, gas, EVM, security, upgradeability, signatures, PoS consensus, scaling, DeFi and MEV
- [System Design](docs/topics/system.md) — interview framework, traffic and edge, caching, data storage, async processing, rate limiting, reliability, architecture, classic designs
- [Databases](docs/topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, schema design, scaling
- [AI Engineering](docs/topics/ai.md) — architecture choices, agent orchestration, tools and integration, RAG, evaluation, cost, security, governance
- [DevOps](docs/topics/devops.md) — deployment strategies, containers, Kubernetes, Terraform, GitOps
- [AWS](docs/topics/aws.md) — IAM, VPC networking, compute, storage, databases, events, operations
- [Security](docs/topics/security.md) — web vulnerabilities, auth and sessions, tokens, access control, cryptography, TLS, threat modeling
- [Rust](docs/topics/rust.md) — ownership and borrowing, lifetimes, traits, smart pointers, error handling, concurrency, async, unsafe, macros and Cargo
- [Python](docs/topics/python.md) — runtime and the GIL, memory management, concurrency, gotchas, object model, typing, tooling
- [TypeScript](docs/topics/typescript.md) — type system semantics, narrowing, type-level programming, compilation, strictness, declarations, typing patterns
- [JavaScript](docs/topics/javascript.md) — event loop, scope and closures, `this` and prototypes, async, modules, memory, DOM events, recent additions
- [Backend](docs/topics/backend.md) — API design, idempotency, resilience, async work, data access, lifecycle, security, testing
- [Frontend](docs/topics/frontend.md) — rendering strategies, browser pipeline, performance, caching, React internals, state management, accessibility, security

## Quiz

The `quiz` skill (`.agents/skills/quiz/`, linked into `.claude/skills/` for Claude Code) quizzes you on the briefs one question at a time and reports your score at the end:

```
/quiz golang            # 10 random questions from one topic
/quiz golang ethereum   # questions mixed from several topics
/quiz all 20            # 20 questions from every topic
```

## Local site preview

Install the site builder, then serve the site:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-docs.txt
zensical serve
```

To produce the same files as the Pages workflow, run `zensical build --clean --strict`. Zensical reads the Markdown directly from `docs/` and reloads edits while serving. The generated `site/` directory is ignored by Git.

GitHub Pages must be configured to use **GitHub Actions** as its build and deployment source. Once this workflow is on `main`, each push builds and publishes the site.
