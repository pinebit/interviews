---
name: quiz
description: Run an interactive interview quiz from the cheatsheets in docs/topics/. Use when the user asks to be quizzed or tested on a topic, e.g. "/quiz golang", "/quiz ethereum database", "/quiz all 20".
argument-hint: "<all | topic [topic...]> [count]"
---

# Quiz

Quiz the user on one or more cheatsheets in `docs/topics/`, one question at a time, and report the score at the end.

## Arguments

`<all | topic [topic...]> [count]`

- A topic is a cheatsheet file name without `.md` (e.g. `golang` → `docs/topics/golang.md`). Several topics can be given, separated by spaces or commas.
- `all` means every file in `docs/topics/`.
- `count` is the number of questions; default **10**. If it exceeds the number of available entries, use all of them.
- If no topic is given, or a topic has no matching file, list the available topics (`ls docs/topics/`) and ask the user to choose. Don't guess a close match silently; if a name clearly maps to a file (e.g. `blockchain` → `ethereum`), confirm it with the user first.

## Setup

1. Pick the entries at random with a shell command, not by choosing yourself:

   ```sh
   grep -H '^## [0-9]' docs/topics/golang.md docs/topics/ethereum.md | sort -R | head -n 10
   ```

   Use `docs/topics/*.md` for `all`. Each output line is one entry (`file:## N. Question`). When several topics are selected, questions come from the combined pool.
2. Read the selected topic files so you know each entry's full answer. Grade only against these entries, never outside knowledge that contradicts them.
3. Tell the user the topics and the number of questions, then start. Don't show the list of questions.

## Each question

1. Ask one question, prefixed with its progress and source: `**Q3/10** (golang)`. Base it on the entry: use the heading question, or a narrower question about the key point, term, number, or gotcha in its answer. Don't include hints or the answer.
2. Stop and wait for the user's answer. Never ask the next question in the same message.
3. Grade the answer against the entry:
   - **Correct** — covers the entry's core point (usually the bold terms). Wording and minor omissions don't matter.
   - **Incorrect** — wrong, missing the core point, "skip", or "I don't know".
   State the verdict, then give the entry's key points in 1–3 sentences, naming anything the user missed or got wrong.
4. Ask the next question in the same message as the verdict, so the user only has to type answers.

If the user asks to stop early, report the score for the questions answered so far.

## Final score

After the last question, show:

- The score as `correct/total`, e.g. `**Score: 7/10**`.
- The questions answered incorrectly, each with its file and heading (e.g. `docs/topics/golang.md — 5. How do maps work?`), so the user knows what to review.
