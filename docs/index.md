# Interview Cheatsheets

Short, memorizable material for software engineering interview prep. Each topic has 20 frequently asked questions with brief answers.

## Topics

- [Go](topics/golang.md) — goroutines, channels, interfaces, slices, maps, context, GC, generics, and more
- [Distributed Systems](topics/distributed.md) — CAP, consistency, replication, consensus, transactions, clocks, CRDTs, stream processing, and more
- [Ethereum](topics/ethereum.md) — accounts, gas, EVM, security, PoS, proxies, rollups, MEV, DeFi, bridges, and more
- [System Design](topics/system.md) — interview framework, caching, scaling, databases, queues, classic designs, and more
- [Databases](topics/database.md) — ACID, indexes, isolation levels, joins, locking, MVCC, SQL, replication, partitioning, and more
- [AI Engineering](topics/ai.md) — enterprise agents, workflow orchestration, RAG, system integration, evaluations, security, governance, and more
- [DevOps](topics/devops.md) — deployments, CI/CD, Docker, Kubernetes, AWS, Terraform, GitOps, and more
- [Security](topics/security.md) — web vulnerabilities, access control, authentication, cryptography, TLS, and threat modeling
- [Rust](topics/rust.md) — ownership, borrowing, lifetimes, traits, error handling, concurrency, and Cargo

## Quiz

Clone the repository and start Codex or Claude Code from its root:

```sh
git clone https://github.com/pinebit/interviews.git
cd interviews
codex  # or: claude
```

In the agent chat, run `$quiz golang` in Codex or `/quiz golang` in Claude Code. The quiz asks one question at a time and gives you a score at the end. Use `$quiz all 20` or `/quiz all 20` for 20 questions across all topics.
