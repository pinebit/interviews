# AGENTS.md

This repo is a set of concise cheatsheets for technical interview prep. The reader skims them repeatedly to memorize key points.

## Structure

- One plain Markdown file per topic, in the `topics/` folder (e.g. `topics/golang.md`).
- File names are lowercase, single word or kebab-case.
- `README.md` lists every cheatsheet with a link and a one-line summary. Update it when adding or renaming a file.

## Cheatsheet format

- Title: `# <Topic> Cheatsheet`, followed by a one-line intro: "The 20 most frequently asked <topic> interview topics, with short answers."
- Each cheatsheet has **20 entries**. To add a topic, replace the least important one rather than growing the list.
- Each entry is a question as a `##` heading, numbered: `## 1. What are goroutines?`
- Order entries by importance and how often they come up in real interviews, most frequent first. Renumber after reordering.
- Answers are 1–2 short paragraphs; use a third only when the topic needs a deeper explanation (e.g. a design question or a mechanism with several parts). Lead with the direct answer, then the key detail or gotcha interviewers probe for.
- A short bullet list is fine for enumerations (types, levels, patterns, steps) — keep items to one line where possible.
- A code snippet is fine only when it is shorter and clearer than prose (a few lines at most).
- Don't repeat topics across cheatsheets; link to the other file instead (e.g. `see [distributed.md](distributed.md)`).

## Style

- Concise and accurate over exhaustive. Cut anything that doesn't help recall.
- Use **bold** for the one or two terms worth memorizing in each answer.
- No filler, no marketing tone, no emojis.
- Verify facts against current language/tool versions; note the version when behavior changed (e.g. "since Go 1.22").
