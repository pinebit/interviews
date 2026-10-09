---
name: renovate
description: Bring topic briefs in docs/topics/ up to date with the latest released versions of the languages, tools, specs, and services they cover, correcting stale claims and adding interview-relevant changes. Use when the user asks to renovate, refresh, update, or fact-check briefs, e.g. "/renovate golang", "/renovate react nextjs", "/renovate all".
argument-hint: "<all | topic [topic...]>"
---

# Renovate

Check each selected brief against the latest stable releases of what it covers, fix claims that are now wrong, and add changes an interviewer could ask about. Edit the briefs in place; don't commit.

## Arguments

`<all | topic [topic...]>`

- A topic is a brief file name without `.md` (e.g. `golang` → `docs/topics/golang.md`). Several topics can be given, separated by spaces or commas.
- `all` means every file in `docs/topics/`.
- If no topic is given, or a topic has no matching file, list the available topics (`ls docs/topics/`) and ask the user to choose. Confirm a near match (e.g. `go` → `golang`) instead of guessing.

## Running several topics

Each topic is independent research, so give each one its own subagent when the harness supports subagents with web and edit tools (Claude Code: the Agent tool; Codex: a spawned agent). Run as many in parallel as the harness allows and queue the rest. Give each one:

- the brief path and today's date;
- the instruction to read `AGENTS.md` and this file's "Per-topic procedure" and follow it for that brief only;
- the instruction to edit only that brief and return the report described in "Per-topic report".

Without subagents, do the topics one after another. Wait until every topic has reported or failed, then finish with "Wrap-up"; redo or report any topic that failed.

## Per-topic procedure

Your training data is older than the latest releases. Take versions, dates, and behavior from current official sources (release notes, changelogs, spec or EIP pages, the project blog, docs via Context7), not from memory. Every change you make needs a source you have actually read in this session.

1. Read `AGENTS.md` (format rules, what to include and cut, topic ownership) and the whole brief.
2. Inventory what is versioned. List the subjects the brief depends on (e.g. ethereum: protocol forks, EIPs, client defaults; nextjs: Next.js, React; postgresql: PostgreSQL, PgBouncer) and every version-bound claim: `since X`, `X+`, version numbers, dates, "experimental", "deprecated", "default", "planned", "upcoming", and numbers that change between releases (limits, defaults, prices, thresholds). Fundamentals briefs (algorithms, distributed, system) have few of these; check the tools and products they name.
3. Find the latest stable release of each subject and the newest version the brief mentions. Read the release notes for every version in between. Prereleases (beta, RC, nightly, draft EIPs, proposals) don't count as shipped. Mention one only when the brief already does, or when interviewers already ask about it, and label it with its status (e.g. "planned for Fusaka", "TypeScript 7 beta").
4. Check the brief's claims and prose against the sources, starting with the inventory from step 2, and fix what is wrong, stale, or misleading. Keep historical version distinctions that are still useful ("before Go 1.22"). Look in particular for:
   - an experimental or opt-in feature that is now the default or removed;
   - a deprecated API that has been removed, or a "planned" change that shipped (give its version or date);
   - a changed default, limit, or number;
   - a "recommended" approach the project now advises against;
   - a release-note or docs link that now redirects or points to an outdated page.
   Leave a claim unchanged if you can't confirm it either way, and report it.
5. Add new changes that meet the bar in AGENTS.md "What to include": behavior an experienced engineer would be asked about or would get wrong. Skip minor library additions, performance work with no visible change in behavior, and tooling trivia. Put each addition in the concept it belongs to and note the version. Respect the format limits (2–6 bullets per concept, one fact per bullet). When a concept would go over its limit, merge or cut its weakest bullets.
6. If the brief has a `## Timeline`, add rows for new versions in the same style (version linked to its release notes, each change linked to its section), and keep the rows consistent with the body.
7. Respect ownership (AGENTS.md "Topic ownership"): full coverage stays in the owner brief. Fix the short overlaps in your brief that summarize another topic, and keep their link to the owner. Edit only your own brief. If another brief now contradicts your sources (e.g. a React change that nextjs restates), list it in the report with the file, the claim, and the source.
8. Keep the brief's voice: concise, no bold, no filler. Link new terms per the "External links" rule.
9. Verify: run `python3 scripts/lint_briefs.py` and `python3 scripts/check_links.py docs/topics/<brief>.md`, then fix every problem in your brief. Re-read your diff (`git diff docs/topics/<brief>.md`) for accuracy and lost content.

## Per-topic report

Keep it short:

- Versions checked: each subject → latest stable version (source URL).
- Changes: one line each, in the form `section › concept: what changed (source URL)`.
- Unverified: claims you couldn't confirm.
- Other briefs: contradictions found outside this brief.
- Checks: lint and link-check results.

If nothing needed changing, say so and still list the versions checked.

## Wrap-up

1. Apply the fixes listed under "Other briefs", following that brief's ownership and format rules. Check each against its source before editing.
2. If a renovated topic's one-line summary in `README.md` and `docs/index.md` no longer matches its sections, update both.
3. Run `python3 scripts/lint_briefs.py`, `python3 scripts/check_links.py <every brief modified>`, and `zensical build --clean --strict` if it is installed (`.venv/bin/zensical`). Fix the problems, and report any check you skipped.
4. Report to the user: a table of topics with the latest versions checked and the number of changes, then each topic's change lines, the unverified claims, and the check results. Leave committing to the user.
