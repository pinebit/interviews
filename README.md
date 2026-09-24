# Interview Refresher

Topic briefs on what engineers forget before technical interviews:

[Read the briefs online](https://pinebit.github.io/interviews/).

Each topic in `docs/topics/` is a brief grouped by subtopic, covering what an experienced engineer tends to forget before an interview. Skim them to memorize.

## Topics

- [Go](docs/topics/golang.md) — goroutines, channels, interfaces, slices, maps, context, GC, generics, and more
- [Distributed Systems](docs/topics/distributed.md) — CAP, consistency, replication, consensus, transactions, clocks, CRDTs, stream processing, and more
- [Ethereum](docs/topics/ethereum.md) — accounts, gas, EVM, security, PoS, proxies, rollups, MEV, DeFi, bridges, and more
- [System Design](docs/topics/system.md) — interview framework, caching, scaling, databases, queues, classic designs (URL shortener, feed, chat), and more
- [Databases](docs/topics/database.md) — ACID, indexes, isolation levels, joins, locking, MVCC, SQL, replication, partitioning, and more
- [AI Engineering](docs/topics/ai.md) — enterprise agents, workflow orchestration, RAG, system integration, evaluations, security, governance, and more
- [DevOps](docs/topics/devops.md) — deployments, CI/CD, Docker, Kubernetes, AWS, Terraform, GitOps, and more
- [Security](docs/topics/security.md) — web vulnerabilities, access control, authentication, cryptography, TLS, and threat modeling
- [Rust](docs/topics/rust.md) — ownership, borrowing, lifetimes, traits, error handling, concurrency, and Cargo
- [Python](docs/topics/python.md) — GIL, memory management, generators, decorators, async/await, typing, and more
- [TypeScript](docs/topics/typescript.md) — structural typing, generics, unions, narrowing, utility types, and more
- [JavaScript](docs/topics/javascript.md) — event loop, closures, prototypes, `this`, promises, modules, and more
- [Backend](docs/topics/backend.md) — REST/RPC/GraphQL, auth, idempotency, queues, caching, and more
- [Frontend](docs/topics/frontend.md) — rendering strategies, state management, performance, accessibility, and more

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
