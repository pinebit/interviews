# Interview Cheatsheets

Short, memorizable material for software engineering interview prep:

- **Cheatsheets** (`topics/`) — each covers one area with its 20 most frequently asked interview questions and brief answers, ordered from most to least common. Skim them to memorize.
- **Lecture scripts** (`lectures/`) — the same material as a cheatsheet, retold as continuous prose to read aloud or listen to. The file name matches its cheatsheet.

## Cheatsheets

- [Go](topics/golang.md) — goroutines, channels, interfaces, slices, maps, context, GC, generics, and more
- [Distributed Systems](topics/distributed.md) — CAP, consistency, replication, consensus, transactions, clocks, CRDTs, stream processing, and more
- [Ethereum](topics/ethereum.md) — accounts, gas, EVM, security, PoS, proxies, rollups, MEV, DeFi, bridges, and more
- [System Design](topics/system.md) — interview framework, caching, scaling, databases, queues, classic designs (URL shortener, feed, chat), and more
- [Databases](topics/database.md) — ACID, indexes, isolation levels, joins, locking, MVCC, SQL, replication, partitioning, and more
- [AI Engineering](topics/ai.md) — LLM basics, RAG, agents, workflows, context engineering, evals, fine-tuning, MCP, agentic coding, tooling, and more

## Lecture scripts

- [AI Engineering lecture](lectures/ai.md) — a spoken overview of all 20 AI engineering interview topics

## Quiz

The `quiz` skill (`.agents/skills/quiz/`, linked into `.claude/skills/` for Claude Code) quizzes you on the cheatsheets one question at a time and reports your score at the end:

```
/quiz golang            # 10 random questions from one topic
/quiz golang ethereum   # questions mixed from several topics
/quiz all 20            # 20 questions from every topic
```
