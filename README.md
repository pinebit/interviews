# Interview Refresher

Topic briefs on what engineers forget before technical interviews:

[Read the briefs online](https://pinebit.github.io/interviews/).

Each topic in `docs/topics/` is a brief grouped by subtopic, covering what an experienced engineer tends to forget before an interview. Skim them to memorize.

## Topics

### Fundamentals

- [Algorithms](docs/topics/algorithms.md) — complexity, arrays and sequences, strings, sorting, data structures, graphs, dynamic programming, greedy and backtracking, NP-hardness
- [Databases](docs/topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, Redis and NoSQL, schema design, scaling
- [Distributed Systems](docs/topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, Kafka and stream processing
- [Networking](docs/topics/networking.md) — TCP, keepalive and congestion control, HTTP/1.1 vs 2 vs 3, QUIC, DNS, IP addressing, NAT, MTU, BGP and anycast
- [Operating Systems](docs/topics/os.md) — processes and signals, scheduling and cgroup throttling, virtual memory, OOM and cgroup limits, NUMA, file descriptors, epoll and io_uring, fsync, synchronization, perf tools
- [System Design](docs/topics/system.md) — interview framework, load balancing, caching and consistency, storage choices, queues, rate limiting, reliability, architecture, probabilistic and geospatial structures, classic designs

### Languages

- [Go](docs/topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, standard library gotchas, modules and GODEBUG, testing, profiling and PGO
- [JavaScript](docs/topics/javascript.md) — event loop, scope and closures, `this` and prototypes, numbers, async, modules, memory, metaprogramming, Node.js runtime, DOM events, recent additions
- [Python](docs/topics/python.md) — runtime and the GIL, memory management, data structures, concurrency, gotchas, object model, functions, recent features, typing, tooling
- [Rust](docs/topics/rust.md) — ownership and borrowing, lifetimes, traits, closures and iterators, smart pointers, error handling, concurrency, async, unsafe, macros and Cargo
- [Solidity](docs/topics/solidity.md) — language semantics, storage layout, calls and ABI, contract security, gas optimization, upgradeability, errors, compiler and Foundry testing, inline assembly
- [TypeScript](docs/topics/typescript.md) — type system semantics, narrowing, type-level programming, compilation and TypeScript 6/7, strictness, declarations, typing patterns

### Web

- [Backend](docs/topics/backend.md) — API design, idempotency and concurrency, service calls and webhooks, async work, data access, lifecycle and health, security, testing
- [Frontend](docs/topics/frontend.md) — rendering strategies, browser pipeline, CSS, performance, caching, React rendering and hooks, state management, accessibility
- [Security](docs/topics/security.md) — server-side and browser-side attacks, auth and sessions, tokens and OAuth, authorization, cryptography, TLS, supply chain, threat modeling

### Infrastructure

- [AWS](docs/topics/aws.md) — IAM and KMS, VPC networking, compute, storage and databases, events, operations
- [DevOps](docs/topics/devops.md) — deployment strategies, containers, Kubernetes workloads/storage/networking/operations, Terraform, CI/CD and GitOps

### Domains

- [AI Engineering](docs/topics/ai.md) — LLM fundamentals, attention and MoE, reasoning models, inference and serving, RAG, fine-tuning, agents, tools and MCP, evaluation, cost, security
- [Ethereum](docs/topics/ethereum.md) — accounts and transactions, gas, EVM, signatures and standards, PoS consensus, scaling, DeFi and MEV

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
