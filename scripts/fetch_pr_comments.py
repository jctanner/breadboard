#!/usr/bin/env python3
"""Export a GitHub PR's conversation comments, reviews and inline comments.

Usage: .venv/bin/python scripts/fetch_pr_comments.py [PR_URL] --output FILE
The token is read from .env.github, never from a command-line argument.
"""
import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
from dotenv import dotenv_values

DEFAULT_PR = "https://github.com/fullsend-ai/strat-creator/pull/85"


def pages(session, url):
    """Follow every next-page link, including for reviews and inline replies."""
    records = {}
    while url:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        for record in response.json():
            records[record["id"]] = record
        url = response.links.get("next", {}).get("url")
    return list(records.values())


def export(pr_url, env_file, output):
    match = re.fullmatch(r"https://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)/?", pr_url)
    if not match:
        raise ValueError("Expected https://github.com/OWNER/REPO/pull/NUMBER")
    owner, repo, number = match.groups()
    if not env_file.is_file():
        raise ValueError(f"Token file does not exist: {env_file}")
    token = dotenv_values(env_file, interpolate=False).get("GITHUB_TOKEN")
    if not token or not token.strip():
        raise ValueError(f"GITHUB_TOKEN is missing from {env_file}")

    with requests.Session() as session:
        session.headers.update({
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        base = f"https://api.github.com/repos/{owner}/{repo}"
        kinds = {
            "Regular comment": f"{base}/issues/{number}/comments",
            "Review": f"{base}/pulls/{number}/reviews",
            "Inline review comment": f"{base}/pulls/{number}/comments",
        }
        groups = {kind: pages(session, url + "?per_page=100") for kind, url in kinds.items()}
        # Include any pending review comments visible to this token, too.
        inline = {item["id"]: item for item in groups["Inline review comment"]}
        for review in groups["Review"]:
            if review.get("state") == "PENDING":
                for item in pages(session, f"{base}/pulls/{number}/reviews/{review['id']}/comments?per_page=100"):
                    inline[item["id"]] = item
        groups["Inline review comment"] = list(inline.values())

    counts = {kind: len(items) for kind, items in groups.items()}
    lines = [f"Pull request: {pr_url}", f"Fetched (UTC): {datetime.now(UTC).isoformat()}",
             *(f"{kind}: {count}" for kind, count in counts.items()),
             "Dates are GitHub API timestamps in UTC. Reviews without text are retained.", ""]
    entries = [(kind, item) for kind, items in groups.items() for item in items]
    entries.sort(key=lambda entry: (entry[1].get("created_at") or entry[1].get("submitted_at") or "9999",
                                    entry[0], entry[1]["id"]))
    for kind, item in entries:
        lines.extend(["=" * 78, f"Type: {kind}", f"ID: {item['id']}",
                      f"Author: {(item.get('user') or {}).get('login', '[deleted]')}",
                      f"URL: {item.get('html_url', item.get('url', ''))}"])
        date_fields = ("submitted_at",) if kind == "Review" else ("created_at", "updated_at")
        for field in date_fields:
            lines.append(f"{field}: {item.get(field) or '[not supplied / not submitted]'}")
        for field in ("state", "path", "line", "original_line", "side", "commit_id",
                      "pull_request_review_id", "in_reply_to_id"):
            if item.get(field) is not None:
                lines.append(f"{field}: {item[field]}")
        lines.extend(["", item.get("body") or "[No comment text]", ""])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr_url", nargs="?", default=DEFAULT_PR)
    parser.add_argument("--env-file", type=Path, default=Path(".env.github"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        counts = export(args.pr_url, args.env_file, args.output)
    except (ValueError, OSError, requests.RequestException) as error:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1
    print(f"Saved {sum(counts.values())} entries to {args.output}")
    for kind, count in counts.items():
        print(f"  {kind}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
