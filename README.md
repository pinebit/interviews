# Interview Refresher

Topic briefs on what engineers forget before technical interviews:

[Read the briefs online](https://pinebit.github.io/interviews/).

Each topic in `docs/topics/` is a brief grouped by subtopic, covering what an experienced engineer tends to forget before an interview. Skim them to memorize.

## Topics

- [Go](docs/topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, standard library gotchas, modules, testing and profiling
- [Algorithms](docs/topics/algorithms.md) — complexity, array and string patterns, sorting, data structures, graphs, dynamic programming, greedy methods, NP-hardness
- [Distributed Systems](docs/topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, Kafka and stream processing
- [Ethereum](docs/topics/ethereum.md) — accounts and transactions, gas, EVM, security, upgradeability, signatures, PoS consensus, scaling, DeFi and MEV
- [System Design](docs/topics/system.md) — interview framework, traffic and edge, real-time delivery, caching, data storage, async processing, rate limiting, reliability, architecture, classic designs
- [Databases](docs/topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, Redis and NoSQL, schema design, scaling
- [Networking](docs/topics/networking.md) — TCP, HTTP/1.1 vs 2 vs 3, QUIC, DNS, IP addressing, NAT, MTU, BGP and anycast
- [Operating Systems](docs/topics/os.md) — processes and signals, scheduling and cgroup throttling, virtual memory and OOM, file descriptors, epoll and io_uring, fsync, synchronization, perf tools
- [AI Engineering](docs/topics/ai.md) — LLM fundamentals, inference and serving, RAG, fine-tuning, agents, tools and MCP, evaluation, cost, security
- [DevOps](docs/topics/devops.md) — deployment strategies, containers, Kubernetes workloads/networking/operations, Terraform, GitOps
- [AWS](docs/topics/aws.md) — IAM and KMS, VPC networking, compute, storage and databases, events, operations
- [Security](docs/topics/security.md) — web vulnerabilities, auth and sessions, tokens and OAuth, access control, cryptography, TLS, supply chain, threat modeling
- [Rust](docs/topics/rust.md) — ownership and borrowing, lifetimes, traits, closures and iterators, smart pointers, error handling, concurrency, async, unsafe, macros and Cargo
- [Python](docs/topics/python.md) — runtime and the GIL, memory management, data structures, concurrency, gotchas, object model, typing, tooling
- [TypeScript](docs/topics/typescript.md) — type system semantics, narrowing, type-level programming, compilation, strictness, declarations, typing patterns
- [JavaScript](docs/topics/javascript.md) — event loop, scope and closures, `this` and prototypes, numbers, async, modules, memory, DOM events, recent additions
- [Backend](docs/topics/backend.md) — API design, idempotency and concurrency, service calls and webhooks, async work, data access, lifecycle, security, testing
- [Frontend](docs/topics/frontend.md) — rendering strategies, browser pipeline, performance, caching, React internals and concurrency, state management, accessibility

## Quiz

The `quiz` skill (`.agents/skills/quiz/`, linked into `.claude/skills/` for Claude Code) generates questions from random brief concepts, asks them one at a time, and reports your score at the end. Run it from the repository root with `/quiz` in Claude Code or `$quiz` in Codex:

```
/quiz golang            # 10 random concepts from one topic
/quiz golang ethereum   # concepts mixed from several topics
/quiz all 20            # 20 concepts from every topic
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
