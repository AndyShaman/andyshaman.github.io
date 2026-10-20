#!/usr/bin/env python3
"""Refresh GitHub star counts and the "Updated <Month YYYY>" line in index.html."""
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.request

INDEX = pathlib.Path(__file__).resolve().parent.parent / "index.html"
STARS = re.compile(r'(data-repo="([^"]+)"><span class="star">★</span> )([\d,]+)')


def fetch_stars(repo):
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}",
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "andyshaman-update-stars"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)["stargazers_count"]


def main():
    html = INDEX.read_text(encoding="utf-8")
    counts = {}
    for repo in dict.fromkeys(m.group(2) for m in STARS.finditer(html)):
        try:
            counts[repo] = fetch_stars(repo)
        except Exception as exc:  # keep the old number for this repo
            print(f"{repo}: {exc}", file=sys.stderr)
            continue
        print(f"{repo}: {counts[repo]}")
    new = STARS.sub(lambda m: m.group(1) + str(counts.get(m.group(2), m.group(3))), html)
    if new != html:
        month = datetime.date.today().strftime("%B %Y")
        new = re.sub(r"Updated [A-Z][a-z]+ \d{4}", f"Updated {month}", new)
        INDEX.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
