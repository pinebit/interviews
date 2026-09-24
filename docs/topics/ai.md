# AI Engineering

What experienced AI engineers forget before an interview, grouped by subtopic. This topic is design-heavy — bullets are conditions and trade-offs, not definitions.

## Architecture choices

### Workflow vs agent vs multi-agent

- **Workflow** — steps fixed in code; use when the process is well understood and mostly deterministic.
- **Single agent** — chooses tools and next steps within a bounded task; use when the path varies but one component can own the result.
- **Multi-agent** — delegates distinct work to specialists; justified only when roles need different tools/instructions or subtasks can run in parallel — extra agents add handoffs, latency, cost, and ways to lose context.
- Default to the least complex design that passes the task's evaluations; add complexity only when a measured failure mode demands it.

### Redesigning a process around AI

- Map the current process first — handoffs, waiting time, exceptions, and *why* a human judgment step exists — before automating anything.
- Design the exception path before scaling the happy path; copying every manual step into an agent workflow usually just preserves the old bottlenecks.
- Pilot with real users and measure cycle time, error rate, adoption, cost, and downstream rework, not just model accuracy.

## Agent orchestration

### State machines and durable execution

- A **stateful graph** (nodes = steps, edges = transitions, explicit state) can branch, loop, pause for review, and resume from a checkpoint.
- **Durable execution** (e.g. Temporal) suits processes that wait/retry over days; a scheduler (Airflow) suits batch pipelines; none of these makes an external write exactly-once — use idempotency keys or dedup (see [distributed.md](distributed.md)).
- Persist task IDs, inputs, completed steps, approvals, and external side effects, not just the conversation — resumability depends on this state being outside the model.

### Planning, reflection, and stop conditions

- **Planning** decomposes an open-ended task into verifiable steps; **reflection** checks an intermediate result against requirements and repairs a concrete error — both earn their cost only when the next action depends on tool results.
- Don't add open-ended critique loops by default — they can repeat mistakes and burn budget. Cap steps, require evidence (tests, source records), and escalate on unresolved failure.
- A model's private reasoning text is not a reliable audit record — persist decisions and tool outcomes explicitly, not the chain-of-thought.

## Tools and integration

### Tool design

- Give tools narrow names/schemas, meaningful errors, and short outputs; treat a tool call as a **request**, not permission — authorize and validate in application code, not the prompt.
- Add timeouts and idempotency keys for writes; log what was read or changed.
- **MCP** standardizes how an application discovers tools/resources — it does not replace authorization or business validation.

### Enterprise integration and browser fallback

- Build connectors around each system's actual interface (REST/GraphQL/gRPC/webhooks/SOAP), separating reads from writes and respecting per-service rate limits; keep credentials in a managed secret store, using delegated user access when an action must reflect the user's own permissions.
- Record the external ID and result of a write so a retry never duplicates a transaction; define a compensating action for cross-system workflows where an earlier write succeeds and a later one fails (see [distributed.md](distributed.md) for sagas).
- Reach for **browser automation** only when there's no usable API — layouts change, sessions expire, and clicks have ambiguous effects; prefer an official API, isolate browser credentials, and require approval before irreversible submissions.

## RAG

### Pipeline and hybrid retrieval

- Pipeline: ingest → parse → chunk → index → retrieve → rerank → answer with citations; keep source versions and access metadata so answers stay traceable and refreshable.
- RAG doesn't guarantee truth — the right answer can be absent, outdated, or missed by retrieval; abstain when evidence is insufficient.
- **Hybrid search**: lexical (BM25, catches exact names/IDs) + dense vector (semantic matches), merged with **reciprocal rank fusion**, then a **cross-encoder reranks** a small candidate set. Reranking cannot recover a passage that was never retrieved — tune recall@k first.
- **GraphRAG** combines graph traversal with source documents for relationship questions; verify extracted relationships against the underlying records.

### Ingestion and permissions

- A robust ingestion pipeline extracts text/tables/layout/metadata, runs OCR on scans, and records the original page/section for citation; chunk by document structure, and consider parent-document retrieval to return a passage plus its surrounding section.
- Carry the requester's identity and entitlements into retrieval and filter by tenant/ACL/sensitivity **before** a passage reaches the model — the same filter must apply to cached answers, follow-up retrieval, and agent memory. A prompt instruction to "ignore forbidden data" is not an access-control mechanism; fail closed when permission metadata is stale or missing.

### RAG vs prompting vs fine-tuning

| Approach | Use when |
|---|---|
| Prompting + structured-output validation | Instructions or a JSON schema need to change |
| RAG | Facts are private or change often, citations matter |
| Fine-tuning (LoRA/QLoRA for open weights) | Repeated evals show a stable style/format/decision gap prompting can't close — poor for keeping facts current |

## Evaluation and observability

### Evaluation

- Build the eval set from real business cases, edge cases, and past incidents with expected outcomes and sources; measure retrieval (recall@k), answer groundedness/relevance/citation correctness, and agent success on the final business task, separately.
- Use deterministic checks for schemas/state changes, human review for high-value cases, and an **LLM-as-judge** for scalable rubric scoring only after calibrating it against human labels.
- **Shadow mode**: feed real production inputs to a candidate agent but only log proposed outputs/writes without executing them, to compare before a live rollout.

### Tracing

- Trace each workflow run across model calls, retrieval, tool calls, approvals, and external writes under one correlation ID; record latency, tokens, cost, errors, retries, and the final outcome.
- Alert on user-facing failures, stuck workflows, permission violations, and cost spikes — a trace must show which step failed and whether a side effect already happened, so an operator can resume or compensate safely. See [system.md](system.md) for general logs/metrics/traces.

### Prompt management

- Treat prompts as **versioned code**: templates, variables, examples, and output contracts live in source control and are tested against a fixed evaluation set before merging — not hand-edited strings scattered across services.
- Trace which prompt **version** produced each result, so a regression can be tied back to the change that caused it instead of just "the model got worse."

## Cost and latency

### Routing and caching

- **Model routing**: simple extraction to a fast/cheap model, hard reasoning to a stronger one; compare hosted vs privately served open-weights models on quality, throughput, latency, privacy terms, and GPU/ops cost.
- **Prompt caching** reuses an identical input prefix (tool schemas, standard instructions) to cut repeated processing cost — keep stable content first in the prompt.
- **Semantic caching** reuses a prior answer to a similar query; its cache key must include user permissions, source version, and freshness requirements, or it leaks stale/unauthorized answers.
- Set token and step budgets, trim retrieved context, and measure cost **per completed workflow**, not per call.

## Security

### Prompt injection and data leakage

- **Prompt injection** hides instructions inside lower-trust content (documents, emails, tool results) — treat that content as data, keep tool permissions narrow, and validate actions in code, never in the prompt alone.
- The **"lethal trifecta"**: private data access + untrusted content exposure + an exfiltration channel, all in one agent — removing any one of the three closes most of the risk.
- Input/output filters can flag suspicious content or PII but cannot guarantee the model ignores every malicious instruction; prevent leakage structurally with retrieval permissions, separate tool identities, egress controls, and approval gates for external sends.
- **Red-team** before release with adversarial documents/tool results designed to reveal private records or trigger unauthorized writes, and keep those cases in regression tests.

## Governance and human oversight

### Approval and audit

- Gate **human-in-the-loop** approval before actions with high financial, legal, privacy, or external impact; present the proposed action, evidence, and affected records, and verify the approver's authority and that the data hasn't changed materially since the proposal.
- Approval authorizes one specific action, not later agent decisions — provide timeout, cancellation, and escalation paths, and record who approved what and when.
- Define ownership/policy per use case (allowed data, permitted actions, retention, model/provider inventory, incident response); verify a vendor's retention and training-use terms before claiming zero-retention, and enforce role-based access and tenant isolation across prompts, retrieval, traces, caches, and connectors.
