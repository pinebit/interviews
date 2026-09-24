# Interview Refresher

Topic briefs on what engineers forget before technical interviews, grouped by subtopic.

## Topics

- [Go](topics/golang.md) — concurrency, memory management, slices/maps/strings, types and interfaces, errors, testing and profiling
- [Distributed Systems](topics/distributed.md) — theory, consistency models, replication, partitioning, consensus, clocks and IDs, transactions, conflict resolution, failure handling, stream processing
- [Ethereum](topics/ethereum.md) — accounts and transactions, gas, EVM, security, upgradeability, signatures, PoS consensus, scaling, DeFi and MEV
- [System Design](topics/system.md) — interview framework, traffic and edge, caching, data storage, async processing, rate limiting, reliability, architecture, classic designs
- [Databases](topics/database.md) — indexes, isolation, MVCC and locking, storage engines, query tuning, SQL gotchas, schema design, scaling
- [AI Engineering](topics/ai.md) — architecture choices, agent orchestration, tools and integration, RAG, evaluation, cost, security, governance
- [DevOps](topics/devops.md) — deployment strategies, containers, Kubernetes, AWS, Terraform, GitOps
- [Security](topics/security.md) — web vulnerabilities, access control, authentication, cryptography, TLS, and threat modeling
- [Rust](topics/rust.md) — ownership, borrowing, lifetimes, traits, error handling, concurrency, and Cargo
- [Python](topics/python.md) — GIL, memory management, generators, decorators, async/await, typing, and more
- [TypeScript](topics/typescript.md) — structural typing, generics, unions, narrowing, utility types, and more
- [JavaScript](topics/javascript.md) — event loop, closures, prototypes, `this`, promises, modules, and more
- [Backend](topics/backend.md) — REST/RPC/GraphQL, auth, idempotency, queues, caching, and more
- [Frontend](topics/frontend.md) — rendering strategies, state management, performance, accessibility, and more

## Quiz

Clone the repository and start Codex or Claude Code from its root:

```sh
git clone https://github.com/pinebit/interviews.git
cd interviews
codex  # or: claude
```

In the agent chat, run `$quiz golang` in Codex or `/quiz golang` in Claude Code. The quiz asks one question at a time and gives you a score at the end. Use `$quiz all 20` or `/quiz all 20` for 20 questions across all topics.
