#!/usr/bin/env python3
"""Manage pushed article history to avoid duplicate recommendations."""

import json
import os
import sys
from datetime import datetime, timezone

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "push_history.json")
MAX_HISTORY_DAYS = 14  # Keep 14 days of history, then prune


def load_history():
    """Load push history from file."""
    if not os.path.exists(HISTORY_FILE):
        return {"pushed": []}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save push history to file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_duplicate(url, title, history):
    """Check if an article was already pushed.

    Only matches by URL (exact). Same event with new article/URL is NOT a duplicate —
    follow-up coverage is valuable context for the user.
    """
    pushed_urls = {entry.get("url") for entry in history.get("pushed", [])}
    return url in pushed_urls


def record_push(url, title, source):
    """Record a pushed article to history."""
    history = load_history()
    history["pushed"].append({
        "url": url,
        "title": title,
        "source": source,
        "pushed_at": datetime.now(timezone.utc).isoformat(),
    })
    # Prune old entries
    cutoff = datetime.now(timezone.utc).timestamp() - (MAX_HISTORY_DAYS * 86400)
    history["pushed"] = [
        e for e in history["pushed"]
        if datetime.fromisoformat(e["pushed_at"]).timestamp() > cutoff
    ]
    save_history(history)


def check_duplicates(articles_json):
    """Read articles from stdin JSON, output non-duplicate ones."""
    articles = json.loads(articles_json)
    history = load_history()
    results = []
    for a in articles:
        if is_duplicate(a.get("link", ""), a.get("title", ""), history):
            print(f"[DEDUP] skip: {a['title'][:50]}", file=sys.stderr)
        else:
            results.append(a)
    json.dump(results, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: dedup.py check < articles.json")
        print("       dedup.py record <url> <title> <source>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "check":
        check_duplicates(sys.stdin.read())
    elif cmd == "record":
        record_push(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        print(f"Recorded: {sys.argv[3][:50]}", file=sys.stderr)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
