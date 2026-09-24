# Interview Refresher

Topic briefs on what engineers forget before technical interviews, grouped by subtopic.

## Topics

- [Go](topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, testing and profiling
- [Distributed Systems](topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, stream processing
- [Ethereum](topics/ethereum.md) — accounts and transactions, gas, EVM, security, upgradeability, signatures, PoS consensus, scaling, DeFi and MEV
- [System Design](topics/system.md) — interview framework, traffic and edge, caching, data storage, async processing, rate limiting, reliability, architecture, classic designs
- [Databases](topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, schema design, scaling
- [AI Engineering](topics/ai.md) — architecture choices, agent orchestration, tools and integration, RAG, evaluation, cost, security, governance
- [DevOps](topics/devops.md) — deployment strategies, containers, Kubernetes, Terraform, GitOps
- [AWS](topics/aws.md) — IAM, VPC networking, compute, storage, databases, events, operations
- [Security](topics/security.md) — web vulnerabilities, auth and sessions, tokens, access control, cryptography, TLS, threat modeling
- [Rust](topics/rust.md) — ownership and borrowing, lifetimes, traits, smart pointers, error handling, concurrency, async, unsafe, macros and Cargo
- [Python](topics/python.md) — runtime and the GIL, memory management, concurrency, gotchas, object model, typing, tooling
- [TypeScript](topics/typescript.md) — type system semantics, narrowing, type-level programming, compilation, strictness, declarations, typing patterns
- [JavaScript](topics/javascript.md) — event loop, scope and closures, `this` and prototypes, async, modules, memory, DOM events, recent additions
- [Backend](topics/backend.md) — API design, idempotency, resilience, async work, data access, lifecycle, security, testing
- [Frontend](topics/frontend.md) — rendering strategies, browser pipeline, performance, caching, React internals, state management, accessibility, security

## Quiz

Clone the repository and start Codex or Claude Code from its root:

```sh
git clone https://github.com/pinebit/interviews.git
cd interviews
codex  # or: claude
```

In the agent chat, run `$quiz golang` in Codex or `/quiz golang` in Claude Code. The quiz asks one question at a time and gives you a score at the end. Use `$quiz all 20` or `/quiz all 20` for 20 questions across all topics.
