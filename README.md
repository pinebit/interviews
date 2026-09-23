# Interview Cheatsheets

Short, memorizable material for software engineering interview prep:

[Read the cheatsheets online](https://pinebit.github.io/interviews/).

Each topic in `docs/topics/` covers its 20 most frequently asked interview questions with brief answers, ordered from most to least common. Skim them to memorize.

## Topics

- [Go](docs/topics/golang.md) — goroutines, channels, interfaces, slices, maps, context, GC, generics, and more
- [Distributed Systems](docs/topics/distributed.md) — CAP, consistency, replication, consensus, transactions, clocks, CRDTs, stream processing, and more
- [Ethereum](docs/topics/ethereum.md) — accounts, gas, EVM, security, PoS, proxies, rollups, MEV, DeFi, bridges, and more
- [System Design](docs/topics/system.md) — interview framework, caching, scaling, databases, queues, classic designs (URL shortener, feed, chat), and more
- [Databases](docs/topics/database.md) — ACID, indexes, isolation levels, joins, locking, MVCC, SQL, replication, partitioning, and more
- [AI Engineering](docs/topics/ai.md) — enterprise agents, workflow orchestration, RAG, system integration, evaluations, security, governance, and more
- [DevOps](docs/topics/devops.md) — deployments, CI/CD, Docker, Kubernetes, AWS, Terraform, GitOps, and more

## Quiz

The `quiz` skill (`.agents/skills/quiz/`, linked into `.claude/skills/` for Claude Code) quizzes you on the cheatsheets one question at a time and reports your score at the end:

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
