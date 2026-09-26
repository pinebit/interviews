# AI Engineering

What experienced AI engineers forget before an interview, grouped by subtopic. For retries and idempotency see [distributed.md](distributed.md); for general observability see [system.md](system.md).

## LLM fundamentals

### Tokens and context windows

- Models read **tokens** (subword pieces from BPE-style tokenizers): roughly **4 characters or ¾ of a word** of English per token; code and non-English text use more.
- The context window holds input **and** output tokens; price and latency scale with both, and output tokens cost several times more than input.

### Attention cost

- Self-attention compares every token with every other: prefill compute grows **O(n²)** with sequence length; each decoded token attends to all cached ones.
- **GQA/MQA** share key/value heads across query heads, shrinking the KV cache several-fold.
- **FlashAttention** computes exact attention in tiles held in on-chip memory — same result, far less memory traffic.

### Mixture of experts

- An **MoE** layer routes each token to a few of many expert feed-forward networks, so **active parameters** per token are a fraction of the total.
- Compute follows active parameters, but memory follows **total** parameters (offloading experts to CPU saves GPU memory, at a speed cost); uneven routing complicates serving.

### Reasoning models

- Reasoning models spend **test-time compute**: they generate a chain of thought before answering, trading latency and cost for accuracy on math, code, and planning.
- **Thinking tokens are billed as output** and count against the context window; APIs expose a thinking budget or effort level.
- Prompt them with goals and constraints — "think step by step" is already built in.

### Sampling parameters

- **Temperature** scales logits before softmax: low → focused and repeatable, high → diverse. **Top-p** (nucleus) samples from the smallest set covering probability `p`; top-k from the `k` likeliest tokens.
- Temperature 0 is near-greedy but **not guaranteed deterministic** — batching and floating-point order change results.

### Long-context behavior

- Recall is weakest for facts in the **middle** of a long prompt ("lost in the middle"), and quality degrades as irrelevant context grows.
- Put instructions and the key evidence at the start or end; retrieving less but better beats stuffing the window.

### Structured output

- **Constrained decoding** masks tokens so output matches a JSON schema or grammar — except when cut off by the token limit or replaced by a refusal.
- It guarantees **shape, not correctness** — still validate values in code.

### Tool calling

- The model emits a structured call (name + JSON arguments); **the application executes it** and appends the result, then the model continues — a loop until the model answers.
- The model never runs anything itself, so every side effect is under application control.

## Inference and serving

### Prefill vs decode

- Prefill processes the whole prompt in parallel — compute-bound, drives **time to first token (TTFT)**.
- Decode emits one token at a time — memory-bandwidth-bound, drives **time per output token (TPOT)**; total latency ≈ TTFT + TPOT × output tokens.

### KV cache

- Attention keys and values of past tokens are cached so each new token doesn't recompute them; cache size grows with **sequence length × layers × batch**, which is what limits concurrency on a GPU.
- **Prompt caching** reuses the KV cache of an identical **prefix** — put stable content (system prompt, tool schemas, documents) first.

### Batching and PagedAttention

- **Continuous batching** adds and removes requests at every decode step instead of waiting for a whole batch to finish.
- **PagedAttention** (vLLM) stores the KV cache in fixed-size blocks like virtual-memory pages, cutting fragmentation so more requests fit.

### Speculative decoding

- A small **draft model** proposes several tokens; the large model verifies them in one pass and keeps the accepted prefix.
- Faster decode with the **same output distribution**; the gain depends on how often drafts are accepted.

### Quantization

- Weights in FP16 take **2 bytes per parameter** (a 70B model ≈ 140 GB); INT8 halves that, **4-bit** (GPTQ, AWQ) quarters it, with some quality loss.
- Smaller weights also speed up decode, since decode is memory-bound.

## Retrieval and RAG

### RAG pipeline

- Ingest → parse → **chunk** → embed → index → retrieve → **rerank** → answer with citations.
- Keep source version and access metadata on every chunk, so answers stay traceable and refreshable.
- RAG doesn't guarantee truth — the answer can be missing or stale; **abstain** when evidence is insufficient.

### Embeddings and similarity

- An embedding maps text to a vector; similarity is usually **cosine** — on normalized vectors that's just the dot product.
- Query and documents must share one **embedding space** (same model, or jointly trained query/passage encoders as in DPR); changing models means re-embedding the corpus.

### Vector index types

| Index | How | Trade-off |
|---|---|---|
| Flat | exact scan | perfect recall, O(n) per query |
| **HNSW** | layered proximity graph | high recall and speed, memory-heavy, slow builds |
| **IVF** | cluster, then probe `nprobe` clusters | less memory; recall depends on `nprobe` |
| **PQ** | compress vectors into codes | much smaller, lower recall; often combined as IVF-PQ |

### Chunking

- Chunk along **document structure** (sections, paragraphs); a few hundred tokens with **10–20% overlap** is a common starting point — tune on evals.
- **Parent-document retrieval**: match small chunks, return the surrounding section for context.

### Hybrid search and reranking

- **BM25** (lexical) catches exact names and IDs; dense vectors catch paraphrases; merge with **reciprocal rank fusion**.
- A cross-encoder reranker rescores a small candidate set — but can't recover a passage that was never retrieved, so tune **recall@k** first.

### Permission-aware retrieval

- Filter by tenant, ACL, and sensitivity **before** a chunk reaches the model; a prompt saying "ignore forbidden data" is not access control.
- The same filter must apply to caches, follow-up retrieval, and agent memory; fail closed when permission metadata is missing.

### RAG vs prompting vs fine-tuning

| Approach | Use when |
|---|---|
| Prompting + structured output | behavior or format needs to change quickly |
| RAG | facts are private or change often; citations matter |
| Fine-tuning | a stable style, format, or decision gap persists after prompting; poor for keeping facts current |

## Fine-tuning

### SFT, RLHF, DPO

- **SFT**: train on input → ideal-output pairs.
- **RLHF**: train a reward model on human preferences, then optimize the policy against it (PPO).
- **DPO**: learn directly from preferred/rejected pairs, no separate reward model — simpler and more stable.

### LoRA and QLoRA

- **LoRA** freezes the base weights and trains small low-rank adapter matrices — a tiny fraction of parameters, swappable per task.
- **QLoRA** trains LoRA adapters on top of a **4-bit** quantized base, fitting large models on one GPU.

## Agents and orchestration

### Workflow vs agent vs multi-agent

- **Workflow**: steps fixed in code — for well-understood, mostly deterministic processes.
- **Agent**: the model picks tools and next steps in a loop — for tasks whose path varies.
- **Multi-agent**: only when roles need different tools or context, or work can run in parallel — each handoff adds latency, cost, and lost context.
- Start with the simplest design that passes the evals.

### Durable execution and state

- Persist task IDs, inputs, completed steps, approvals, and side effects **outside the model**, so a run can resume from a checkpoint.
- **Durable execution** (Temporal) fits processes that wait or retry for days; none of it makes external writes exactly-once — use idempotency keys.

### Stop conditions

- Cap steps, tokens, and cost per run; require evidence (tests pass, a record exists) before declaring success; escalate on repeated failure.
- Open-ended self-critique loops often repeat the same mistake and burn budget.

### Context management

- Long agent runs overflow the window: **compact** old turns into summaries and keep tool outputs short.
- Store bulky state in files or memory the agent can re-read; **subagents** keep exploratory work out of the main context.

## Tools and integration

### Tool design

- Narrow names and schemas, clear errors, short outputs; a tool call is a **request**, not permission — authorize and validate in code.
- Writes need timeouts and **idempotency keys**; log what was read and changed.

### Model Context Protocol

- **MCP** standardizes how apps discover and call tools, read resources, and fetch prompts — JSON-RPC 2.0 over stdio (local) or **Streamable HTTP** (remote, replaced HTTP+SSE in 2025).
- Authorization is optional; HTTP servers that support it use **OAuth 2.1**. MCP doesn't replace per-action authorization or business validation.

### Browser automation as a fallback

- Use it only without an API — layouts change and clicks have ambiguous effects.
- Isolate its credentials and require **approval** before irreversible submits.

## Evaluation

### Eval sets and metrics

- Build eval cases from real traffic, edge cases, and past incidents, with expected outcomes.
- Measure separately: retrieval (**recall@k**, **MRR**, **nDCG**), answer groundedness and citation accuracy, and end-to-end task success.

### LLM-as-judge

- Scales rubric grading, but has **position**, **verbosity**, and **self-preference** biases — calibrate against human labels and randomize answer order.
- Prefer deterministic checks (schema, state change, test pass) wherever they exist.

### Shadow mode and prompt versioning

- **Shadow mode**: run a candidate on live inputs, log its proposed outputs without executing them, compare before rollout.
- Version prompts like code and record which **prompt + model version** produced each result, so a regression can be traced.

### Tracing

- **One trace per run** across model calls, retrieval, tool calls, approvals, and writes.
- Record latency, tokens, cost, errors, and whether a side effect already happened — so a retry doesn't repeat it.

## Cost and latency

### Model routing and caching

- **Route** easy requests to a small, fast model and hard ones to a strong model.
- **Semantic caching** reuses answers to similar queries; its key must include user permissions, source version, and freshness, or it leaks.
- Measure cost **per completed task**, not per call.

### Batch and streaming

- **Batch APIs** run requests asynchronously (results within ~24 h) at about **half price** — for evals, backfills, and offline labeling.
- **Streaming** doesn't cut total time but shows the first tokens at TTFT, which is what users perceive.

## Security and oversight

### Prompt injection

- Instructions hidden in lower-trust content (web pages, emails, tool results) can hijack the model; no filter reliably stops it.
- Treat that content as **data**, keep tool permissions narrow, and validate actions in code.

### Lethal trifecta

- **Private data access + untrusted content + an exfiltration channel** in one agent enables data theft.
- Removing any one of the three closes most of the risk — e.g. no outbound network from an agent that reads private data.

### Human approval gates

- Require approval before high-impact actions (money, legal, external sends); show the action, evidence, and affected records.
- An approval covers **one specific action**; re-check that data hasn't changed since the proposal, and record who approved what and when.
