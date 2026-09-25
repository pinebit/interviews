# Interview Refresher

Topic briefs on what engineers forget before technical interviews, grouped by subtopic.

## Topics

- [Go](topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, standard library gotchas, modules, testing and profiling
- [Algorithms](topics/algorithms.md) — complexity, array and string patterns, sorting, data structures, graphs, dynamic programming, greedy methods, NP-hardness
- [Distributed Systems](topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, Kafka and stream processing
- [Ethereum](topics/ethereum.md) — accounts and transactions, gas, EVM, security, upgradeability, signatures, PoS consensus, scaling, DeFi and MEV
- [System Design](topics/system.md) — interview framework, traffic and edge, real-time delivery, caching, data storage, async processing, rate limiting, reliability, architecture, classic designs
- [Databases](topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, Redis and NoSQL, schema design, scaling
- [Networking](topics/networking.md) — TCP, HTTP/1.1 vs 2 vs 3, QUIC, DNS, IP addressing, NAT, MTU, BGP and anycast
- [Operating Systems](topics/os.md) — processes and signals, scheduling and cgroup throttling, virtual memory and OOM, file descriptors, epoll and io_uring, fsync, synchronization, perf tools
- [AI Engineering](topics/ai.md) — LLM fundamentals, inference and serving, RAG, fine-tuning, agents, tools and MCP, evaluation, cost, security
- [DevOps](topics/devops.md) — deployment strategies, containers, Kubernetes workloads/networking/operations, Terraform, GitOps
- [AWS](topics/aws.md) — IAM and KMS, VPC networking, compute, storage and databases, events, operations
- [Security](topics/security.md) — web vulnerabilities, auth and sessions, tokens and OAuth, access control, cryptography, TLS, supply chain, threat modeling
- [Rust](topics/rust.md) — ownership and borrowing, lifetimes, traits, closures and iterators, smart pointers, error handling, concurrency, async, unsafe, macros and Cargo
- [Python](topics/python.md) — runtime and the GIL, memory management, data structures, concurrency, gotchas, object model, typing, tooling
- [TypeScript](topics/typescript.md) — type system semantics, narrowing, type-level programming, compilation, strictness, declarations, typing patterns
- [JavaScript](topics/javascript.md) — event loop, scope and closures, `this` and prototypes, numbers, async, modules, memory, DOM events, recent additions
- [Backend](topics/backend.md) — API design, idempotency and concurrency, service calls and webhooks, async work, data access, lifecycle, security, testing
- [Frontend](topics/frontend.md) — rendering strategies, browser pipeline, performance, caching, React internals and concurrency, state management, accessibility

## Quiz

Clone the repository and start Codex or Claude Code from its root:

```sh
git clone https://github.com/pinebit/interviews.git
cd interviews
codex  # or: claude
```

In the agent chat, run `/quiz golang` in Claude Code or `$quiz golang` in Codex. The quiz generates questions from random brief concepts, asks one at a time, and gives you a score at the end. Use `/quiz golang ethereum` to mix topics, or `/quiz all 20` for 20 concepts across all topics.
