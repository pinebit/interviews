# AI Engineering Cheatsheet

The 20 most frequently asked AI engineering interview topics, with short answers.

## 1. How do LLMs work?

An LLM is a **decoder-only transformer** trained to predict the **next token**. Text is split into tokens (subword units, roughly 4 characters of English each). Each token becomes an embedding vector, and stacked layers of **self-attention** plus feed-forward networks turn the sequence into a probability distribution over the next token. Generation is autoregressive: sample one token, append it, and repeat.

Attention lets every token weigh every earlier token, so its cost grows **O(n²)** with context length. Inference has two phases. **Prefill** processes the whole prompt in parallel and is compute-bound. **Decode** produces one token at a time and is memory-bandwidth-bound. The **KV cache** keeps the attention keys and values from previous tokens so they aren't recomputed. This is why output tokens cost more and are slower than input tokens.

## 2. What is RAG?

**Retrieval-Augmented Generation** fetches relevant documents at query time and puts them in the prompt, so the model answers from your data rather than its weights alone. It keeps knowledge fresh without retraining, lets you cite sources, and reduces hallucination.

The pipeline:

- **Indexing:** chunk documents (by structure, a few hundred tokens with overlap), embed the chunks, and store them in a vector index with metadata.
- **Retrieval:** embed the query and find the top-k chunks. **Hybrid search** combines dense vectors with BM25 keyword search, merged by reciprocal rank fusion.
- **Reranking:** a cross-encoder rescores the candidates for precision.
- **Generation:** the prompt includes the chunks and an instruction to answer only from them, with citations.

Most failures come from retrieval, not generation. Common causes are bad chunking, a query that doesn't match the document wording (fix with query rewriting or HyDE), and missing metadata filters. Evaluate retrieval separately (recall@k) from the final answer (faithfulness). **Agentic RAG** exposes search as a tool, so the model can issue several queries, refine them, and decide when it has enough. It replaces the single fixed retrieval step.

## 3. What is an AI agent?

An agent is an LLM that **uses tools in a loop** until the task is done. The model reads the context, decides on an action (a tool call), the harness executes it, the result is appended to the context, and the loop repeats until the model returns a final answer or a limit is hit. This is the **ReAct** pattern (reason + act).

The parts of an agent are:

- **Model:** does the reasoning.
- **Tools:** functions with a name, a description, and a JSON schema.
- **Instructions:** the system prompt.
- **Context/memory management:** controls what the model sees on each step.
- **Harness:** runs the loop and enforces budgets, permissions, and stop conditions.

Agents fit open-ended tasks where you can't hardcode the steps. The costs are latency, token spend, and compounding errors: 95% per-step reliability over 20 steps gives only about 36% end-to-end. Mitigate with good tool design, verification steps (tests, checks), human approval for risky actions, and step and cost limits.

## 4. Workflows vs agents?

A **workflow** runs LLM calls through code paths you define in advance. An **agent** lets the model choose its own path. Workflows are predictable, cheaper, and easier to test. Agents handle open-ended problems. Start with the simplest thing that works, often a single call with good retrieval, and add agency only when it clearly helps.

Common workflow patterns (from Anthropic's "Building effective agents"):

- **Prompt chaining:** fixed sequential steps, with gates between them.
- **Routing:** classify the input and send it to a specialized prompt or model.
- **Parallelization:** split into independent subtasks (sectioning), or run the same task several times and vote.
- **Orchestrator-workers:** a lead LLM breaks the task down on the fly and delegates to workers.
- **Evaluator-optimizer:** one call generates, another critiques, and the loop repeats until it passes.

## 5. Prompt engineering vs context engineering?

**Prompt engineering** is writing good instructions:

- Be clear and specific about the task, audience, and output format.
- Give the model a role and the relevant background.
- Include a few examples (**few-shot**).
- Separate sections with delimiters or XML tags.
- Ask for step-by-step reasoning on hard problems.
- Explain *why* a rule exists, not only what it is.

**Context engineering** is the broader discipline of deciding everything that goes into the context window on each call: system prompt, tool definitions, retrieved documents, conversation history, memory, and tool results. For agents it is the main lever for quality. Too little context and the model guesses. Too much and quality degrades (**context rot**, "lost in the middle"), cost rises, and latency grows. Techniques include just-in-time retrieval through tools, summarizing or compacting old turns, trimming large tool outputs, and handing isolated subtasks to subagents with clean contexts.

## 6. What are embeddings and how does vector search work?

An **embedding** is a dense vector (for example, 768–3072 dimensions) that places semantically similar text close together. Similarity is usually **cosine similarity** or dot product on normalized vectors. Use the same embedding model for indexing and querying. Changing the model means re-embedding everything.

Exact nearest-neighbor search is O(n), so vector stores use **approximate nearest neighbor (ANN)** indexes:

- **HNSW:** a layered proximity graph. Fast with high recall, but memory-heavy. The most common default.
- **IVF:** clusters vectors and searches only the nearest clusters.
- **Product quantization:** compresses vectors to save memory, at some cost to accuracy.

You tune the trade-off between recall and latency (for example, `ef_search` in HNSW). Metadata filtering combined with ANN is a common source of missed results.

## 7. How do you evaluate an LLM application?

Build an **eval set** of realistic inputs with expected outputs or grading criteria, drawn from real usage and known failure cases. Run it on every prompt, model, or pipeline change, as a regression test in CI. Eval-driven development is the LLM counterpart of TDD: without evals, every change is a guess.

Grader types:

- **Code-based:** exact match, regex, JSON schema validity, unit tests passing. Cheap and deterministic, so prefer them.
- **LLM-as-judge:** a model scores output against a rubric. Scales well, but has biases: position, verbosity, and preference for its own outputs. Calibrate it against human labels.
- **Human review:** the ground truth. Slow, so use it to build and calibrate the other graders.

Also measure specific dimensions:

- **RAG:** retrieval recall, answer faithfulness to the sources, and answer relevance (tools like Ragas).
- **Agents:** the final outcome (did the task succeed?) rather than an exact trajectory. Consistency matters: **pass@k** (any of k attempts succeeds) vs **pass^k** (all k succeed).
- **In production:** track user feedback, escalation rates, cost, and latency, and sample traces for review.

## 8. What are hallucinations and how do you reduce them?

A **hallucination** is fluent, confident output that is false or not supported by the sources. It happens because the model generates plausible tokens rather than looking up facts, and training rewards answering over admitting uncertainty.

Mitigations:

- Ground answers with **RAG** and require citations.
- Let the model say "I don't know".
- Ask it to quote the source before answering.
- Lower the temperature for factual tasks.
- Verify claims with a second pass or with tools such as search, code execution, or a database.
- Constrain outputs with schemas.

Measure the hallucination rate with faithfulness evals. You cannot eliminate it, so design the UX and review process around that.

## 9. Prompting vs RAG vs fine-tuning?

- **Prompting:** try it first. It's cheap, fast to iterate, and handles most tasks.
- **RAG:** for when the model lacks **knowledge**: private, fresh, or large corpora, or when you need citations.
- **Fine-tuning:** for **behavior**: a consistent format, style, or domain-specific task, or distilling a large model into a smaller, cheaper one. It is poor at adding facts and hard to update.

**LoRA** freezes the base weights and trains small low-rank adapter matrices, usually well under 1% of the parameters. It is cheap and lets you swap adapters per task. **QLoRA** does the same on a 4-bit quantized base model, so large models fit on a single GPU. Full fine-tuning updates every weight and costs far more. Fine-tuning needs a clean dataset (hundreds to thousands of examples) and evals to prove it beats a well-prompted base model.

## 10. How do tool calling and MCP work?

With **tool calling**, you pass tool definitions (name, description, JSON Schema for the arguments) to the model. The model returns a structured call instead of text, your code executes it, and you send back the result. The model never executes anything itself. Tool quality drives agent quality: use clear names and descriptions, few overlapping tools, helpful error messages, and concise outputs. Tool definitions also consume context on every call.

The **Model Context Protocol (MCP)** is an open standard, introduced by Anthropic in 2024, for connecting AI apps to tools and data. It reduces the N×M integration problem to N+M.

- **Roles:** a **host** (for example, an IDE or chat app) runs **clients** that connect to **servers**, over JSON-RPC 2.0.
- **What servers expose:** **tools** (actions), **resources** (read-only data), and **prompts** (templates).
- **Transports:** stdio for local servers and Streamable HTTP for remote ones, with OAuth for authorization.

**A2A** (Agent2Agent) is a separate protocol for communication between agents rather than between an agent and its tools.

## 11. How are LLMs trained?

1. **Pretraining:** next-token prediction on trillions of tokens of web, code, and book text. This produces a base model with broad knowledge but no instruction-following.
2. **Supervised fine-tuning (SFT):** trains on curated prompt-and-response pairs so the model follows instructions.
3. **Preference tuning:**
   - **RLHF** trains a reward model on human rankings, then optimizes the policy with RL (PPO).
   - **DPO** optimizes directly on preference pairs, with no separate reward model.
   - **RLAIF** and Constitutional AI use AI feedback instead of human labels.

**Reasoning models** add large-scale RL with **verifiable rewards** (RLVR) on math, code, and other checkable tasks, using methods such as GRPO (popularized by DeepSeek-R1). The model learns to produce long chains of thought before answering. Spending more tokens on thinking at inference time improves accuracy: **test-time compute** is a scaling axis alongside model size and data. The trade-off is higher latency and cost, so use reasoning models or thinking budgets for hard problems, not simple lookups.

## 12. What are tokens and context windows?

**Tokens** are the units a model reads and writes, produced by a tokenizer such as BPE. APIs price and limit usage by tokens. Tokenization explains some classic quirks: poor letter counting, weak arithmetic on long numbers, and non-English text using more tokens.

The **context window** is the maximum number of input plus output tokens per call. Current frontier models support hundreds of thousands to over a million tokens. A long window doesn't guarantee good use of it: recall and reasoning degrade as context grows, especially for information in the middle. Put the important instructions at the start or end. In long-running agents, manage context actively through compaction, summaries, and external memory, instead of filling the window.

## 13. What do temperature, top-p, and top-k do?

- **Temperature** scales the logits before softmax. Low values (0–0.3) make output near-deterministic, which suits extraction, classification, and code. Higher values (0.7–1.0) add diversity for creative text and brainstorming.
- **Top-k** samples only from the k most likely tokens.
- **Top-p** (nucleus sampling) samples from the smallest set of tokens whose cumulative probability reaches p.

Usually you tune temperature or top-p, not both. Temperature 0 is still not perfectly deterministic in practice: batching and floating-point non-associativity on GPUs can change results. Some reasoning models fix or ignore these parameters.

## 14. What is prompt injection and how do you defend against it?

**Prompt injection** is when untrusted text (web pages, emails, documents, tool results) contains instructions that the model follows as if they came from the user. Unlike SQL injection, there is no reliable way to separate code from data in a prompt, so filtering helps but cannot fully prevent it. **Jailbreaking** is related: the user tries to get around the model's safety training.

The dangerous combination is the **"lethal trifecta"**: an agent with access to **private data**, exposure to **untrusted content**, and the ability to **communicate externally**. Together they allow data exfiltration. Defend at the architecture level:

- **Least-privilege tools:** give the agent only the tools and data access it needs.
- **Sandboxing:** isolate network and filesystem access.
- **Human approval:** require it for sensitive actions.
- **Separation:** keep the model that reads untrusted content from also holding privileged tools.
- **Guardrails and filters:** apply input and output classifiers, PII filters, and output validation before acting.
- **Logging:** record every tool call for audit.

## 15. How do you reduce LLM cost and latency?

- **Right-size the model:** route easy requests to a small, fast model and hard ones to a frontier model (a model cascade).
- **Prompt caching:** reuse a stable prompt prefix (system prompt, tools, documents). Cached input tokens are billed at a steep discount and processed faster. Put static content first and variable content last.
- **Trim tokens:** use shorter prompts, fewer retrieved chunks, compact tool outputs, and capped output length. Output tokens are the expensive ones.
- **Streaming:** improves perceived latency (time to first token).
- **Batch APIs:** discounted asynchronous processing for offline jobs.
- **Parallelize:** run independent calls concurrently.
- **Semantic caching:** return a stored answer for a near-duplicate query (watch for staleness).

On the serving side, self-hosted stacks use **continuous batching**, PagedAttention (efficient KV-cache memory), quantization (for example, FP8 or 4-bit), and **speculative decoding** (a small draft model proposes tokens that the large model verifies in parallel).

## 16. When should you use multiple agents?

A multi-agent system splits work across agents with separate contexts. The most common and reliable pattern is an **orchestrator with subagents**: a lead agent plans and delegates independent subtasks (research branches, file searches) to workers that run in parallel with clean contexts, and each returns a condensed result.

The benefits are parallelism, specialization, and context isolation: each agent stays focused, and the lead's context isn't flooded. The costs are much higher token use and harder debugging. Coordination also fails when subtasks depend on each other, because agents make conflicting decisions without shared context. Use multiple agents for broad, parallelizable work such as research. Prefer a single agent for tightly coupled tasks like most coding.

## 17. How does agent memory work?

LLMs are stateless, so memory is whatever the harness puts back into context.

- **Short-term:** the conversation or working context, managed by truncation, summarization, or **compaction** when it nears the limit.
- **Long-term:** facts, preferences, and past learnings stored outside the model and retrieved when relevant. Storage can be files (such as `CLAUDE.md` or notes), a database, or a vector store.
- **Types** (borrowed from cognitive science): **episodic** (past events), **semantic** (facts), and **procedural** (how to do things, such as skills or instructions).

The hard parts are deciding what to write (not everything), keeping memories current (update or delete stale ones), and retrieving the right ones without polluting context. Structured notes an agent maintains itself, such as a progress file or a todo list, often work better than raw vector recall for long tasks.

## 18. How do you get reliable structured output?

Ask for JSON that matches a schema, and enforce it. **Constrained decoding** (structured outputs or strict mode) masks invalid tokens during generation, so the output always parses and matches the JSON Schema. Tool calling is another way to get structured arguments. Without enforcement, use a validation library (Pydantic, Zod) and retry with the error message on failure.

A schema guarantees the shape, not the correctness of the values, so still validate the semantics. Forcing strict formats can slightly hurt reasoning quality. Let the model reason first (in a separate field or step), then emit the structured result.

## 19. How do you do agentic engineering with AI coding tools?

**Agentic engineering** means directing coding agents (such as Claude Code, Codex, and Cursor) as a disciplined engineer, in contrast to "vibe coding", where you accept output unread. The engineer owns the design, the context, and the verification. The agent does the typing and the exploring.

The workflow:

1. **Explore → plan → implement → verify.** Have the agent read the relevant code and propose a plan. Review the plan before any code is written.
2. **Give it a feedback loop.** Tests, type checkers, linters, and the ability to run the app let the agent check its own work. This is the biggest quality lever.
3. **Keep tasks small and scoped.** Commit often so any step is easy to revert.
4. **Encode project knowledge** in files the agent reads automatically (`AGENTS.md`, `CLAUDE.md`): build commands, conventions, and pitfalls. Add reusable skills or custom commands for repeated procedures.
5. **Review every diff** as you would a colleague's pull request. You are accountable for what ships.

Advanced setups:

- Run agents in parallel on separate git worktrees.
- Use subagents to keep the main context clean.
- Use hooks to enforce formatting or block dangerous commands.
- Run headless agents in CI to triage issues or fix lint errors.

The risks are subtle bugs, hallucinated APIs, security issues, and bloated code, so verification and human review stay mandatory.

## 20. What tools are common in modern AI pipelines?

- **Agent frameworks and SDKs:**
  - LangGraph: graph-based, stateful workflows.
  - OpenAI Agents SDK, Claude Agent SDK, and Google ADK: vendor SDKs.
  - Pydantic AI: type-safe agents.
  - CrewAI: multi-agent teams.
  - DSPy: optimizes prompts programmatically.
  - LlamaIndex: data connectors and RAG pipelines.
- **Vector stores:** pgvector (Postgres), Qdrant, Pinecone, Weaviate, Milvus, Chroma. Elasticsearch and OpenSearch also offer hybrid search.
- **Observability and evals:** Langfuse, LangSmith, Braintrust, Arize Phoenix. They capture traces of every LLM and tool call and run evals on them. The OpenTelemetry GenAI conventions standardize the trace format.
- **Gateways:** LiteLLM and OpenRouter provide a unified API across providers, with fallbacks, cost tracking, and rate limits.
- **Serving and local inference:** vLLM and SGLang for high-throughput serving, TensorRT-LLM on NVIDIA hardware, Ollama and llama.cpp for local models.
- **Fine-tuning:** Hugging Face TRL and PEFT, Unsloth, Axolotl.
- **Integration standard:** MCP (see #10).

In interviews, show you can justify choices, not just list tools. Frameworks speed up prototypes but add abstraction you may need to debug. Many production teams use thin wrappers over provider SDKs plus a tracing tool.
