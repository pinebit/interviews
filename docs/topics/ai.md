# AI Engineering Cheatsheet

The 20 most frequently asked AI engineering interview topics, with short answers.

**Architecture & Orchestration**

## 1. How do you design an enterprise AI system and workflow?

Start with the **business outcome** and map inputs, systems, decisions, actions, failure cases, and owners. Put deterministic rules in code, use an LLM for ambiguous language or judgment, and add gates before consequential actions. A typical topology is an API or event trigger → queue → durable workflow → model, retrieval, and connector services → audit log. Keep state outside the model so work can resume after a crash.

A practical flow is intake → classify → retrieve evidence → draft or decide → validate → approve if needed → execute → record the outcome. Define success, escalation, throughput, latency, and cost before choosing an agent framework. Use queues or event streams to decouple slow systems; see [system.md](system.md) for their trade-offs.

## 2. When should you use a workflow, a single agent, or multiple agents?

A **workflow** fixes the steps in code; a **single agent** chooses tools and next steps within a bounded task; a **multi-agent system** delegates distinct work to specialists. Use the least complex design that passes the task's evaluations. Extra agents add handoffs, latency, cost, and more ways to lose context.

Choose multiple agents when roles need different tools or instructions, or independent subtasks can run in parallel. Assign one component responsibility for the final result, define the data each handoff must include, and set budgets and stop conditions.

## 3. How does stateful agent orchestration work?

A **stateful graph** represents steps as nodes, transitions as edges, and task data as explicit state. It can branch, loop, pause for review, and resume from a checkpoint. LangGraph and LlamaIndex Workflows are examples; CrewAI and AutoGen focus on agent collaboration patterns.

For long business processes, persist task IDs, inputs, completed steps, approvals, and external side effects. **Durable execution** with Temporal suits processes that wait and retry for days; Airflow suits scheduled data pipelines; n8n and Make speed up connector-driven automation. None makes an external write exactly once: use idempotency keys or deduplication. See [distributed.md](distributed.md) for retry semantics.

## 4. How do planning, reflection, and self-correction help agents?

**Planning** decomposes an open-ended task into verifiable steps; **reflection** checks an intermediate result against requirements and repairs a concrete error. ReAct alternates tool use with updated decisions, while plan-and-execute separates initial planning from execution. These patterns help when the next action depends on tool results.

Do not add open-ended critique loops by default: they can repeat mistakes and consume budget. Set a maximum number of steps, require evidence such as tests or source records, and escalate when the agent cannot resolve a failure. A model's private reasoning text is not a reliable audit record; store decisions and tool outcomes explicitly.

## 5. How do you redesign a business process around AI?

Map the current **process**, including handoffs, waiting time, exceptions, and reasons for human judgment. Choose a narrow outcome to improve, such as time to resolve a support case, then automate the repetitive steps and preserve human decisions where they add value. Design the exception path before scaling the happy path.

Pilot with real users and measure cycle time, error rate, adoption, cost, and downstream rework. Update roles, training, and operating procedures alongside the software; copying every old manual step into an agent workflow usually preserves the old bottlenecks.

**Data & Knowledge (RAG)**

## 6. How do you build a RAG system for enterprise knowledge?

**Retrieval-augmented generation (RAG)** indexes permitted source material, retrieves relevant passages for a question, and gives those passages to the model with source identifiers. The basic pipeline is ingest → parse → chunk → index → retrieve → rerank → answer with citations. Keep source versions and access metadata so answers can be traced and refreshed.

RAG is useful for private or changing knowledge such as policies, contracts, and support records. It does not guarantee truth: the correct answer may be absent, outdated, or missed by retrieval. For questions about relationships between entities, **GraphRAG** can combine graph traversals (for example, in Neo4j) with source documents. Verify extracted relationships against the records and abstain when evidence is insufficient.

## 7. Why combine lexical and vector search, and when do you rerank?

**Hybrid search** combines lexical search such as BM25, which catches exact names and IDs, with dense vector search, which catches semantic matches. Merge candidate lists with reciprocal rank fusion, then **rerank** a small set with a cross-encoder for precision; compress the final context to passages needed for the answer.

Choose pgvector when PostgreSQL is already the data platform; Qdrant, Pinecone, and Milvus are dedicated vector-search options. Compare filtering, scale, operations, and cost on real queries. Apply tenant and permission filters before results reach the model, and tune recall at k: reranking cannot recover a passage that was never retrieved.

## 8. How do you ingest PDFs, scans, and other messy enterprise data?

A robust **ingestion pipeline** extracts text, tables, layout, and metadata; runs OCR on scanned pages; normalizes formats; and records the original page or section for citation. Tools such as Unstructured or LlamaParse can help, but check their output against complex tables and scans. Chunk by document structure; parent-document retrieval can return a matching passage plus its surrounding section.

Handle duplicate files, version changes, failed parses, and deleted or revoked documents. Measure extraction quality on representative invoices, contracts, and scanned forms before indexing them; a good retriever cannot fix missing or misread source text.

## 9. How do you enforce document permissions in RAG?

Carry the requester's **identity and entitlements** into retrieval, and filter by tenant, document ACL, and sensitivity before the model sees a passage. Apply the same rule to cached answers, citations, follow-up retrieval, and agent memory. A prompt telling the model to ignore forbidden data is not an access-control mechanism.

Sync permissions and deletions from source systems such as SharePoint, Salesforce, or Jira. Test with users who have different access to similar documents, and fail closed when permission metadata is missing or stale.

## 10. When should you use RAG, prompting, or fine-tuning?

Use **RAG** for private or changing facts and citations. Use prompting and structured-output validation first for instructions or a JSON schema. If repeated evaluations still show a stable behavior gap, **fine-tuning** can teach task-specific style, decisions, or format; it is a poor way to keep facts current.

For open-weights models, LoRA trains small adapter weights and QLoRA does so with a quantized base model to reduce memory use. Fine-tuning requires representative examples and a held-out evaluation set; a schema still needs runtime validation. Choose the method by measured quality, cost, and update frequency.

**Integrations & Tooling**

## 11. How should an agent call tools and enterprise APIs?

**Tool calling** lets a model propose a typed operation; application code validates arguments, authorizes the action, executes it, and returns the result. Give tools narrow names and schemas, meaningful errors, and short outputs. Use REST, GraphQL, gRPC, or webhooks according to the enterprise system's actual interface; see [system.md](system.md) for protocol trade-offs.

Treat a tool call as a request, not permission. Enforce the user's identity and scopes in the integration layer, add timeouts and idempotency keys for writes, and log what was read or changed. **MCP** can standardize how an AI application discovers tools and resources, but it does not replace authorization or business validation.

## 12. How do you integrate AI with CRM, ERP, and other enterprise systems?

Build **connectors** around supported APIs and events, with clear mappings between business objects such as customers, orders, and tickets. SAP, Salesforce, Dynamics, 1C, Jira, and Microsoft 365 differ in schemas and permissions; some legacy systems still require SOAP. Separate reads from writes, validate records, and respect service-specific rate limits. Webhooks or Kafka/RabbitMQ events can start asynchronous work; polling is a fallback.

Keep credentials in a managed secret store and use delegated user access when an action must reflect the user's permissions. Record the external ID and result so a retry does not duplicate a transaction. For a cross-system workflow, define compensation when an earlier write succeeds and a later one fails; see [distributed.md](distributed.md) for sagas.

## 13. When is browser automation appropriate for an AI workflow?

Use **browser automation** for systems without a usable API, especially read-only tasks or supervised updates. Playwright, Puppeteer, or Selenium use page structure; **computer-use APIs** such as Anthropic's can also interpret screenshots and request mouse or keyboard actions. Visual control handles interfaces without useful DOM structure, but is slower and still brittle.

Layouts change, sessions expire, and clicks can have ambiguous effects. Prefer an official API when available, isolate browser credentials, limit reachable sites, and require approval before irreversible submissions or external communications.

**Reliability & LLMOps**

## 14. How do you evaluate RAG and agent workflows?

Build an **evaluation set** from real business cases, edge cases, and past incidents, with expected outcomes and source records. Measure retrieval separately with recall at k; measure answer **groundedness**, relevance, and citation correctness; measure agents by whether the final business task succeeded without unauthorized actions.

Use deterministic checks for schemas and state changes, human review for high-value cases, and an **LLM judge** for scalable rubric scoring after calibrating it against human labels. Ragas or TruLens can help run RAG evaluations. In **shadow mode**, feed real production inputs to a candidate agent but log proposed outputs and writes without executing them; compare outcomes before a live rollout. Regressions must include failure and abstention cases.

## 15. What should you trace and monitor in production?

Trace each **workflow run** across model calls, retrieval, tool calls, approvals, and external writes, using a correlation ID. Record latency, tokens, cost, errors, retries, retrieved document IDs, and final outcome. LangSmith, Langfuse, and Phoenix are examples of tracing tools. Sample traces for quality review, and redact sensitive content before storage.

Alert on user-facing failures, stuck workflows, permission violations, and cost spikes. A trace should show which step failed and whether a side effect happened, so an operator can resume or compensate safely. See [system.md](system.md) for general metrics, logs, and traces.

## 16. How do you manage and optimize prompts at scale?

Treat **prompts as versioned code**: keep templates, variables, examples, and output contracts in source control, then test changes against a fixed evaluation set. Avoid unreviewed, hand-edited strings scattered across services; trace which prompt version produced each result.

**DSPy** expresses an LLM pipeline as modules and uses examples plus a metric to optimize instructions or demonstrations programmatically. It can reduce manual prompt tuning, but needs a useful metric and held-out tests so optimization does not overfit the training cases.

## 17. How do you route models, use caching, and control AI costs?

Use **model routing** to send simple extraction to a fast model and harder reasoning to a stronger one. Compare hosted and privately served open-weights models on quality, throughput, latency, privacy terms, GPU and operations costs. For private serving, vLLM or TGI targets throughput; Ollama fits local pilots. Set token and step budgets, trim retrieved context, and measure cost per completed workflow.

**Prompt caching** reuses an identical input prefix, such as tool schemas or standard instructions, to reduce repeated processing; OpenAI and Anthropic support it with different controls. Keep stable content first and check cache-hit metrics. **Semantic caching** reuses a prior answer to a similar query, so its key must include user permissions, source version, and freshness requirements.

**Security & Governance**

## 18. How do you defend an agent against prompt injection and data leakage?

**Prompt injection** puts instructions inside lower-trust material such as documents, emails, pages, or tool results. Treat that material as data, keep tool permissions narrow, and validate actions in code. Input/output filters and tools such as NeMo Guardrails or Guardrails AI can flag suspicious content or PII, but cannot guarantee that the model will ignore every malicious instruction.

Prevent leakage with retrieval permissions, separate identities for tools, egress controls, output checks for sensitive fields, and approval for external sends. **Red-team** the agent before release with adversarial documents and tool results that try to reveal private records or trigger unauthorized writes, then keep those cases in regression tests. See [devops.md](devops.md) for infrastructure secret handling.

## 19. Where should human approval enter an automated process?

Use **human-in-the-loop (HITL)** gates before actions with high financial, legal, privacy, or external impact. Present the proposed action, supporting evidence, affected records, and a clear approve or reject choice. Persist the workflow state while waiting, then verify that the approver has authority and that the data has not changed materially.

Approval is a control for a specific action, not a blanket authorization for later agent decisions. Provide timeout, cancellation, and escalation paths; record who approved what and when. Low-risk, reversible actions can usually run automatically under policy.

## 20. What does AI governance require in an enterprise system?

Define **ownership and policy** for each use case: allowed data, permitted actions, retention, audit logs, model and provider inventory, and incident response. Enforce role-based access and tenant isolation across prompts, retrieval, traces, caches, and connectors. Document data flows; verify a vendor's retention, training-use, and deletion terms before claiming a zero-retention design. Review privacy and security requirements such as GDPR and SOC 2 controls with the relevant owners.

Classify risks by use case and test controls before release, then monitor them as models and workflows change. Compliance obligations depend on jurisdiction and contract; involve the organization's legal and security owners when defining them.
