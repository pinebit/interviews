#!/usr/bin/env python3
"""Check topic briefs against the format rules in AGENTS.md."""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = ROOT / "docs" / "topics"
MAX_BULLETS = 6
BOLD = re.compile(r"\*\*|__")  # either marker, outside code and link targets
NOT_PROSE = re.compile(r"(`+).+?\1|\]\([^)]*\)")
BACKREF = re.compile(r"\b(as|see) (above|below)\b", re.IGNORECASE)


def lint_brief(path):
    errors = []
    lines = path.read_text().split("\n")
    rel = path.relative_to(ROOT)

    def err(lineno, msg):
        errors.append(f"{rel}:{lineno}: {msg}")

    if not lines[0].startswith("# "):
        err(1, "first line must be the '# Title'")
    if len(lines) < 3 or not lines[2] or lines[2].startswith("#"):
        err(3, "missing one-line intro after the title")

    section = None  # (name, lineno, concept count)
    concept = None  # (name, lineno, bullets)
    seen = set()
    in_fence = False

    def close_concept():
        if concept is None:
            return
        name, lineno, bullets = concept
        if bullets > MAX_BULLETS:
            err(lineno, f"'{name}' has {bullets} bullets (max {MAX_BULLETS})")

    def close_section():
        if section is not None and section[2] < 2:
            err(section[1], f"section '{section[0]}' has {section[2]} concept(s) (min 2)")

    for i, line in enumerate(lines, 1):
        if i > 1 and not line and not lines[i - 2]:
            err(i, "consecutive blank lines")
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and BOLD.search(NOT_PROSE.sub("", line)):
            err(i, "no bold in briefs; let the wording carry emphasis")
        if BACKREF.search(line):
            err(i, "concepts must be self-contained; avoid 'as/see above/below'")
        if line.startswith("## "):
            close_concept()
            close_section()
            concept = None
            section = [line[3:], i, 0]
        elif line.startswith("### "):
            close_concept()
            name = line[4:]
            if name.endswith("?"):
                err(i, "concept heading must be a noun phrase, not a question")
            if name in seen:
                err(i, f"duplicate concept '{name}'")
            seen.add(name)
            if section is None:
                err(i, "concept outside a section")
            else:
                section[2] += 1
            concept = [name, i, 0]
        elif concept is not None and line.startswith("- "):
            concept[2] += 1
    close_concept()
    close_section()
    return errors


def lint_listings(briefs):
    errors = []
    listings = {
        "README.md": "docs/topics/{}",
        "docs/index.md": "topics/{}",
        "zensical.toml": "topics/{}",
    }
    for listing, pattern in listings.items():
        text = (ROOT / listing).read_text()
        for brief in briefs:
            if pattern.format(brief.name) not in text:
                errors.append(f"{listing}: missing {brief.name}")
    return errors


def main():
    briefs = sorted(TOPICS.glob("*.md"))
    errors = lint_listings(briefs)
    for brief in briefs:
        errors += lint_brief(brief)
    for e in errors:
        print(e)
    print(f"{len(briefs)} briefs checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
