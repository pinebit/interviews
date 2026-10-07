#!/usr/bin/env python3
"""Check that external links in topic briefs resolve and their #anchors exist.

Usage: check_links.py [brief.md ...]   (default: every file in docs/topics/)
"""

import concurrent.futures
import html
import http.client
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = ROOT / "docs" / "topics"
LINK = re.compile(r"\]\((https?://[^)\s]+)\)")
# Minified HTML (the WHATWG spec, Hugo sites) leaves attribute values unquoted.
ANCHOR = re.compile(r"""(?<![\w-])(?:id|name)=(?:"([^"]+)"|'([^']+)'|([^\s"'>]+))""")
# Wikipedia rejects requests without a descriptive User-Agent.
USER_AGENT = "interview-briefs-link-checker (+https://github.com/pinebit/interviews)"


def fetch(url):
    """Return (error, set of anchor ids) for a page URL without a fragment."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", "replace")
    except (OSError, http.client.HTTPException) as e:  # URLError and timeouts are OSErrors
        return str(e), set()
    return None, {html.unescape("".join(groups)) for groups in ANCHOR.findall(body)}


def main():
    briefs = [pathlib.Path(p) for p in sys.argv[1:]] or sorted(TOPICS.glob("*.md"))
    links = []  # (brief, line number, url)
    for brief in briefs:
        for lineno, line in enumerate(brief.read_text().split("\n"), 1):
            links += [(brief, lineno, url) for url in LINK.findall(line)]

    pages = {url.partition("#")[0] for _, _, url in links}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(pages, pool.map(fetch, pages)))

    problems = 0
    for brief, lineno, url in links:
        page, _, fragment = url.partition("#")
        error, anchors = results[page]
        if not error and fragment and urllib.parse.unquote(fragment) not in anchors:
            error = f"missing anchor #{fragment}"
        if error:
            problems += 1
            print(f"{brief}:{lineno}: {url}: {error}")
    print(f"{len(links)} links ({len(pages)} pages) checked, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
