# Interview Refresher

Topic briefs on what engineers forget before technical interviews, grouped by subtopic.

## Topics

### Fundamentals

- [Algorithms](topics/algorithms.md) — complexity, arrays and sequences, strings, sorting, data structures, graphs, dynamic programming, greedy and backtracking, NP-hardness
- [Databases](topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, Redis and NoSQL, schema design, scaling
- [Distributed Systems](topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, Kafka and stream processing
- [Networking](topics/networking.md) — TCP, keepalive and congestion control, HTTP/1.1 vs 2 vs 3, QUIC, DNS, IP addressing, NAT, MTU, BGP and anycast
- [Operating Systems](topics/os.md) — processes and signals, scheduling and cgroup throttling, virtual memory, OOM and cgroup limits, NUMA, file descriptors, epoll and io_uring, fsync, synchronization, perf tools
- [System Design](topics/system.md) — interview framework, load balancing, caching and consistency, storage choices, queues, rate limiting, reliability, architecture, probabilistic and geospatial structures, classic designs

### Languages

- [Go](topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, standard library gotchas, modules and GODEBUG, testing, profiling and PGO
- [JavaScript](topics/javascript.md) — event loop, scope and closures, `this` and prototypes, numbers, async, modules, memory, metaprogramming, Node.js runtime, DOM events, recent additions
- [Python](topics/python.md) — runtime and the GIL, memory management, data structures, concurrency, gotchas, object model, functions, recent features, typing, tooling
- [Rust](topics/rust.md) — ownership and borrowing, lifetimes, traits, closures and iterators, smart pointers, error handling, concurrency, async, unsafe, macros and Cargo
- [Solidity](topics/solidity.md) — language semantics, storage layout, calls and ABI, contract security, gas optimization, upgradeability, errors, compiler and Foundry testing, inline assembly
- [TypeScript](topics/typescript.md) — type system semantics, narrowing, type-level programming, compilation and TypeScript 6/7, strictness, declarations, typing patterns

### Web

- [Backend](topics/backend.md) — API design, idempotency and concurrency, service calls and webhooks, async work, data access, lifecycle and health, security, testing
- [Frontend](topics/frontend.md) — rendering strategies, browser pipeline, CSS, performance, caching, React rendering and hooks, state management, accessibility
- [Security](topics/security.md) — server-side and browser-side attacks, auth and sessions, tokens and OAuth, authorization, cryptography, TLS, supply chain, threat modeling

### Infrastructure

- [AWS](topics/aws.md) — IAM and KMS, VPC networking, compute, storage and databases, events, operations
- [DevOps](topics/devops.md) — deployment strategies, containers, Kubernetes workloads/storage/networking/operations, Terraform, CI/CD and GitOps

### Domains

- [AI Engineering](topics/ai.md) — LLM fundamentals, attention and MoE, reasoning models, inference and serving, RAG, fine-tuning, agents, tools and MCP, evaluation, cost, security
- [Ethereum](topics/ethereum.md) — accounts and transactions, gas, EVM, signatures and standards, PoS consensus, scaling, DeFi and MEV

## Quiz

Clone the repository and start Codex or Claude Code from its root:

```sh
git clone https://github.com/pinebit/interviews.git
cd interviews
codex  # or: claude
```

In the agent chat, run `/quiz golang` in Claude Code or `$quiz golang` in Codex. The quiz generates questions from random brief concepts, asks one at a time, and gives you a score at the end. Use `/quiz golang ethereum` to mix topics, or `/quiz all 20` for 20 concepts across all topics.
