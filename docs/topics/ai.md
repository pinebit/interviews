# AI Engineering

What experienced AI engineers forget before an interview, grouped by subtopic. For retries and idempotency see [distributed.md](distributed.md); for general observability see [system.md](system.md).

## LLM fundamentals

### Tokens and context windows

- Models read tokens (subword pieces from [BPE](https://en.wikipedia.org/wiki/Byte-pair_encoding)-style tokenizers): roughly 4 characters or ¾ of a word of English per token; code and non-English text use more.
- The [context window](https://platform.claude.com/docs/en/build-with-claude/context-windows) holds input and output tokens; price and latency scale with both, and output tokens cost several times more than input.

### Attention cost

- [Self-attention](https://arxiv.org/abs/1706.03762) compares every token with every other: prefill compute grows O(n²) with sequence length; each decoded token attends to all cached ones.
- [GQA](https://arxiv.org/abs/2305.13245)/[MQA](https://arxiv.org/abs/1911.02150) share key/value heads across query heads, shrinking the KV cache several-fold.
- [FlashAttention](https://arxiv.org/abs/2205.14135) computes exact attention in tiles held in on-chip memory — same result, far less memory traffic.

### Mixture of experts

- An [MoE](https://arxiv.org/abs/1701.06538) layer routes each token to a few of many expert feed-forward networks, so active parameters per token are a fraction of the total.
- Compute follows active parameters, but memory follows total parameters (offloading experts to CPU saves GPU memory, at a speed cost); uneven routing complicates serving.

### Reasoning models

- Reasoning models spend [test-time compute](https://arxiv.org/abs/2408.03314): they generate a [chain of thought](https://arxiv.org/abs/2201.11903) before answering, trading latency and cost for accuracy on math, code, and planning.
- [Thinking tokens are billed as output](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) and count against the context window; APIs expose a thinking budget or [effort level](https://platform.claude.com/docs/en/build-with-claude/effort).
- Prompt them with goals and constraints — "think step by step" is already built in.

### Sampling parameters

- [Temperature](https://en.wikipedia.org/wiki/Softmax_function) scales logits before softmax: low → focused and repeatable, high → diverse. [Top-p](https://arxiv.org/abs/1904.09751) (nucleus) samples from the smallest set covering probability `p`; top-k from the `k` likeliest tokens.
- Temperature 0 is near-greedy but [not guaranteed deterministic](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) — batching and floating-point order change results.

### Long-context behavior

- Recall is weakest for facts in the middle of a long prompt (["lost in the middle"](https://arxiv.org/abs/2307.03172)), and quality degrades as irrelevant context grows.
- Put instructions and the key evidence [at the start or end](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#long-context-prompting); retrieving less but better beats stuffing the window.

### Structured output

- [Constrained decoding](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) masks tokens so output matches a [JSON schema](https://json-schema.org/) or grammar — except when cut off by the token limit or replaced by a refusal.
- It guarantees shape, not correctness — still validate values in code.

### Tool calling

- The model emits a [structured call](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) (name + JSON arguments); the application executes it and appends the result, then the model continues — a loop until the model answers.
- The model never runs anything itself, so every side effect is under application control.

## Inference and serving

### Prefill vs decode

- Prefill processes the whole prompt in parallel — compute-bound, drives [time to first token (TTFT)](https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html).
- Decode emits one token at a time — memory-bandwidth-bound, drives time per output token (TPOT); total latency ≈ TTFT + TPOT × output tokens.

### KV cache

- Attention keys and values of past tokens are [cached](https://huggingface.co/docs/transformers/en/kv_cache) so each new token doesn't recompute them; cache size grows with sequence length × layers × batch, which is what limits concurrency on a GPU.
- [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) reuses the KV cache of an identical prefix — put stable content (system prompt, tool schemas, documents) first.

### Batching and PagedAttention

- [Continuous batching](https://www.usenix.org/conference/osdi22/presentation/yu) adds and removes requests at every decode step instead of waiting for a whole batch to finish.
- [PagedAttention](https://arxiv.org/abs/2309.06180) ([vLLM](https://docs.vllm.ai/en/latest/)) stores the KV cache in fixed-size blocks like virtual-memory pages, cutting fragmentation so more requests fit.

### Speculative decoding

- A small draft model proposes several tokens; the large model [verifies them in one pass](https://arxiv.org/abs/2211.17192) and keeps the accepted prefix.
- Faster decode with the same output distribution; the gain depends on how often drafts are accepted.

### Model parallelism and GPU memory

- Serving memory ≈ weights + KV cache + activations; a model too large for one GPU must be split.
- [Tensor parallelism](https://arxiv.org/abs/1909.08053) splits each layer's matrices across GPUs; it needs a fast interconnect ([NVLink](https://www.nvidia.com/en-us/data-center/nvlink/)), so it is usually kept within a node.
- [Pipeline parallelism](https://arxiv.org/abs/1811.06965) puts consecutive layers on different GPUs or nodes: less communication, but pipeline bubbles leave stages idle.
- Data parallelism replicates the whole model for throughput; [disaggregated serving](https://arxiv.org/abs/2401.09670) runs prefill and decode on separate GPU pools, each tuned for its bottleneck.

### Quantization

- Weights in FP16 take 2 bytes per parameter (a 70B model ≈ 140 GB); INT8 halves that, 4-bit ([GPTQ](https://arxiv.org/abs/2210.17323), [AWQ](https://arxiv.org/abs/2306.00978)) quarters it, with some quality loss.
- Smaller weights also speed up decode, since decode is memory-bound.

## Retrieval and RAG

### RAG pipeline

- Ingest → parse → chunk → embed → index → retrieve → rerank → answer with citations ([RAG](https://arxiv.org/abs/2005.11401)).
- Keep source version and access metadata on every chunk, so answers stay traceable and refreshable.
- RAG doesn't guarantee truth — the answer can be missing or stale; abstain when evidence is insufficient.

### Embeddings and similarity

- An embedding maps text to a vector; similarity is usually [cosine](https://en.wikipedia.org/wiki/Cosine_similarity) — on normalized vectors that's just the dot product.
- Query and documents must share one embedding space (same model, or jointly trained query/passage encoders as in [DPR](https://arxiv.org/abs/2004.04906)); changing models means re-embedding the corpus.

### Vector index types

| Index | How | Trade-off |
|---|---|---|
| Flat | exact scan | perfect recall, O(n) per query |
| [HNSW](https://arxiv.org/abs/1603.09320) | layered proximity graph | high recall and speed, memory-heavy, slow builds |
| [IVF](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) | cluster, then probe `nprobe` clusters | less memory; recall depends on `nprobe` |
| [PQ](https://ieeexplore.ieee.org/document/5432202) | compress vectors into codes | much smaller, lower recall; often combined as IVF-PQ |

- [Filtered search](https://qdrant.tech/documentation/search-patterns/vector-search-filtering/): post-filtering the top-k returns too few hits when the filter is selective, and pre-filtering breaks HNSW graph connectivity — use a filter-aware engine or partition the index (per tenant).

### Chunking

- Chunk along document structure (sections, paragraphs); a few hundred tokens with 10–20% overlap is a common starting point — tune on evals.
- Parent-document retrieval: match small chunks, return the surrounding section for context.

### Hybrid search and reranking

- [BM25](https://en.wikipedia.org/wiki/Okapi_BM25) (lexical) catches exact names and IDs; dense vectors catch paraphrases; merge with [reciprocal rank fusion](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf).
- A [cross-encoder](https://sbert.net/examples/cross_encoder/applications/README.html) reranker rescores a small candidate set — but can't recover a passage that was never retrieved, so tune [recall@k](https://en.wikipedia.org/wiki/Evaluation_measures_%28information_retrieval%29) first.

### Permission-aware retrieval

- Filter by tenant, ACL, and sensitivity before a chunk reaches the model; a prompt saying "ignore forbidden data" is not [access control](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/).
- The same filter must apply to caches, follow-up retrieval, and agent memory; fail closed when permission metadata is missing.

### RAG vs prompting vs fine-tuning

| Approach | Use when |
|---|---|
| Prompting + structured output | behavior or format needs to change quickly |
| RAG | facts are private or change often; citations matter |
| Fine-tuning | a stable style, format, or decision gap persists after prompting; poor for keeping facts current |

## Training and fine-tuning

### Training pipeline

- Pretraining: next-token prediction on trillions of tokens; [Chinchilla](https://arxiv.org/abs/2203.15556)-optimal is ≈ 20 tokens per parameter, but modern models train far past it so a smaller model is cheaper to serve.
- Post-training: SFT on demonstrations, then preference tuning ([RLHF](https://arxiv.org/abs/2203.02155), [DPO](https://arxiv.org/abs/2305.18290)) for helpfulness and safety.
- [RL with verifiable rewards](https://arxiv.org/abs/2411.15124) (math and code graded automatically, e.g. [GRPO](https://arxiv.org/abs/2402.03300)) is how reasoning models learn long chains of thought.

### SFT, RLHF, DPO

- SFT: train on input → ideal-output pairs.
- [RLHF](https://arxiv.org/abs/2203.02155): train a reward model on human preferences, then optimize the policy against it ([PPO](https://arxiv.org/abs/1707.06347)).
- [DPO](https://arxiv.org/abs/2305.18290): learn directly from preferred/rejected pairs, no separate reward model — simpler and more stable.

### LoRA and QLoRA

- [LoRA](https://arxiv.org/abs/2106.09685) freezes the base weights and trains small low-rank adapter matrices — a tiny fraction of parameters, swappable per task.
- [QLoRA](https://arxiv.org/abs/2305.14314) trains LoRA adapters on top of a 4-bit quantized base, fitting large models on one GPU.

## Agents and orchestration

### Workflow vs agent vs multi-agent

- [Workflow](https://www.anthropic.com/engineering/building-effective-agents): steps fixed in code — for well-understood, mostly deterministic processes.
- Agent: the model picks tools and next steps in a loop — for tasks whose path varies.
- [Multi-agent](https://www.anthropic.com/engineering/multi-agent-research-system): only when roles need different tools or context, or work can run in parallel — each handoff adds latency, cost, and lost context.
- Start with the simplest design that passes the evals.

### Durable execution and state

- Persist task IDs, inputs, completed steps, approvals, and side effects outside the model, so a run can resume from a checkpoint.
- Durable execution ([Temporal](https://docs.temporal.io/evaluate/understanding-temporal)) fits processes that wait or retry for days; none of it makes external writes exactly-once — use idempotency keys.

### Stop conditions

- Cap steps, tokens, and cost per run; escalate to a human on repeated failure.
- Require evidence (tests pass, a record exists) before declaring success.

### Context management

- Long agent runs overflow the window: [compact](https://platform.claude.com/docs/en/build-with-claude/compaction) old turns into summaries and keep tool outputs short.
- Store bulky state in files or memory the agent can re-read; [subagents](https://code.claude.com/docs/en/sub-agents) keep exploratory work out of the main context.

## Tools and integration

### Tool design

- [Narrow names and schemas](https://www.anthropic.com/engineering/writing-tools-for-agents), clear errors, short outputs; a tool call is a request, not permission — authorize and validate in code.
- Writes need timeouts and idempotency keys; log what was read and changed.

### Model Context Protocol

- [MCP](https://modelcontextprotocol.io/specification/2026-07-28) standardizes how apps discover and call tools, read resources, and fetch prompts — [JSON-RPC 2.0](https://www.jsonrpc.org/specification) over stdio (local) or [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) (remote, replaced HTTP+SSE in 2025).
- Stateless since the 2026-07-28 revision: no `initialize` handshake or `Mcp-Session-Id`; each request carries its protocol version and capabilities in `_meta`, and servers advertise theirs via `server/discover`.
- [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) is optional; HTTP servers that support it use [OAuth 2.1](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/). MCP doesn't replace per-action authorization or business validation.

## Evaluation

### Eval sets and metrics

- Build eval cases from real traffic, edge cases, and past incidents, with expected outcomes.
- Measure separately: retrieval ([recall@k](https://en.wikipedia.org/wiki/Evaluation_measures_%28information_retrieval%29), [MRR](https://en.wikipedia.org/wiki/Mean_reciprocal_rank), [nDCG](https://en.wikipedia.org/wiki/Discounted_cumulative_gain)), answer groundedness and citation accuracy, and end-to-end task success.

### LLM-as-judge

- Scales rubric grading, but has position, verbosity, and [self-preference biases](https://arxiv.org/abs/2306.05685) — calibrate against human labels and randomize answer order.
- Prefer deterministic checks (schema, state change, test pass) wherever they exist.

### Shadow mode and prompt versioning

- Shadow mode: run a candidate on live inputs, log its proposed outputs without executing them, compare before rollout.
- Version prompts like code and record which prompt + model version produced each result, so a regression can be traced.

### Tracing

- One trace per run across model calls, retrieval, tool calls, approvals, and writes ([OpenTelemetry GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)).
- Record latency, tokens, cost, errors, and whether a side effect already happened — so a retry doesn't repeat it.

## Cost and latency

### Model routing and caching

- [Route](https://arxiv.org/abs/2406.18665) easy requests to a small, fast model and hard ones to a strong model.
- Semantic caching reuses answers to similar queries; its key must include user permissions, source version, and freshness, or it leaks.

### Batch and streaming

- [Batch APIs](https://platform.claude.com/docs/en/build-with-claude/batch-processing) run requests asynchronously (results within ~24 h) at about half price — for evals, backfills, and offline labeling.
- [Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) doesn't cut total time but shows the first tokens at TTFT, which is what users perceive.

## Security and oversight

### Prompt injection

- Instructions hidden in lower-trust content (web pages, emails, tool results) can [hijack the model](https://genai.owasp.org/llmrisk/llm01-prompt-injection/); no filter reliably stops it.
- Treat that content as data, keep tool permissions narrow, and validate actions in code.

### Lethal trifecta

- [Private data access + untrusted content + an exfiltration channel](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) in one agent enables data theft.
- Removing any one of the three closes most of the risk — e.g. no outbound network from an agent that reads private data.

### Human approval gates

- Require approval before [high-impact actions](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) (money, legal, external sends, irreversible form submits by a browser agent); show the action, evidence, and affected records.
- An approval covers one specific action; re-check that data hasn't changed since the proposal, and record who approved what and when.
