# AGENTS.md

This repo is a set of concise cheatsheets for technical interview prep. The reader skims them repeatedly to memorize key points. Some topics also have a lecture script: the same material as continuous prose for reading aloud or listening.

## Structure

- `topics/` — one cheatsheet per topic (e.g. `topics/golang.md`).
- `lectures/` — optional lecture script for a topic, with the same file name as its cheatsheet (e.g. `lectures/ai.md` for `topics/ai.md`). No `-lecture` suffix.
- `.agents/skills/quiz/` — the `quiz` skill, which quizzes the user on cheatsheet entries. `.claude/skills/quiz` is a symlink to it so Claude Code and Codex share one copy.
- File names are lowercase, single word or kebab-case.
- `README.md` lists every cheatsheet and lecture with a link and a one-line summary. Update it when adding or renaming a file.

## Cheatsheet format

- Title: `# <Topic> Cheatsheet`, followed by a one-line intro: "The 20 most frequently asked <topic> interview topics, with short answers."
- Each cheatsheet has **20 entries**. To add a topic, replace the least important one rather than growing the list.
- Each entry is a question as a `##` heading, numbered: `## 1. What are goroutines?`
- Order entries by importance and how often they come up in real interviews, most frequent first. Renumber after reordering.
- Answers are 1–2 short paragraphs; use a third only when the topic needs a deeper explanation (e.g. a design question or a mechanism with several parts). Lead with the direct answer, then the key detail or gotcha interviewers probe for.
- A short bullet list is fine for enumerations (types, levels, patterns, steps) — keep items to one line where possible.
- A code snippet is fine only when it is shorter and clearer than prose (a few lines at most).
- Don't repeat topics across cheatsheets; link to the other file instead (e.g. `see [distributed.md](distributed.md)`).

## Lecture format

- Title: `# <Topic>: A Short Interview Lecture`, followed by a short intro that frames the area.
- A few `##` sections that group related topics into a logical story; the order need not follow the cheatsheet's numbering.
- Plain spoken prose: no bullets, tables, code, or bold. Introduce acronyms by their full name.
- Must cover every entry of the matching cheatsheet, including the key named terms, numbers, and gotchas. When the cheatsheet changes, update the lecture.

## Style

- Concise and accurate over exhaustive. Cut anything that doesn't help recall.
- Use **bold** for the one or two terms worth memorizing in each answer.
- No filler, no marketing tone, no emojis.
- Verify facts against current language/tool versions; note the version when behavior changed (e.g. "since Go 1.22").
