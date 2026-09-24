---
name: quiz
description: Run an interactive interview quiz from the topic briefs in docs/topics/. Use when the user asks to be quizzed or tested on a topic, e.g. "/quiz golang", "/quiz ethereum database", "/quiz all 20".
argument-hint: "<all | topic [topic...]> [count]"
---

# Quiz

Quiz the user on one or more topic briefs in `docs/topics/`, one question at a time, and report the score at the end.

## Arguments

`<all | topic [topic...]> [count]`

- A topic is a brief file name without `.md` (e.g. `golang` → `docs/topics/golang.md`). Several topics can be given, separated by spaces or commas.
- `all` means every file in `docs/topics/`.
- `count` is the number of questions; default **10**. If it exceeds the number of available concepts, use all of them.
- If no topic is given, or a topic has no matching file, list the available topics (`ls docs/topics/`) and ask the user to choose. Don't guess a close match silently; if a name clearly maps to a file (e.g. `blockchain` → `ethereum`), confirm it with the user first.

## Setup

1. Pick the concepts at random with a shell command, not by choosing yourself:

   ```sh
   grep -H '^### ' docs/topics/golang.md docs/topics/ethereum.md | sort -R | head -n 10
   ```

   Use `docs/topics/*.md` for `all`. Each output line is one concept (`file:### Concept name`). When several topics are selected, questions come from the combined pool.
2. Read the selected topic files so you know each concept's full section (its `##` subtopic and body). Grade only against these sections, never outside knowledge that contradicts them.
3. Tell the user the topics and the number of questions, then start. Don't show the list of questions.

## Each question

1. Ask one question, prefixed with its progress and source: `**Q3/10** (golang — Concurrency)`. Base it on the concept: ask about its key fact, number, or gotcha — not "explain <heading>". Don't include hints or the answer.
2. Stop and wait for the user's answer. Never ask the next question in the same message.
3. Grade the answer against the concept's bullets:
   - **Correct** — covers the concept's core point (usually the bold terms). Wording and minor omissions don't matter.
   - **Incorrect** — wrong, missing the core point, "skip", or "I don't know".
   State the verdict, then give the concept's key points in 1–3 sentences, naming anything the user missed or got wrong.
4. Ask the next question in the same message as the verdict, so the user only has to type answers.

If the user asks to stop early, report the score for the questions answered so far.

## Final score

After the last question, show:

- The score as `correct/total`, e.g. `**Score: 7/10**`.
- The concepts answered incorrectly, each with its file, subtopic, and concept name (e.g. `docs/topics/golang.md — Concurrency › Scheduler (GMP)`), so the user knows what to review.
