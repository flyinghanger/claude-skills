#!/usr/bin/env python3
"""Fetch RSS feeds in parallel and output structured JSON for LLM filtering."""

import json
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError

FEEDS = {
    # AI related (all 11)
    "AI开发者日报": "https://ainews.liduos.com/rss.xml",
    "Founder Park": "https://wechat2rss.bestblogs.dev/feed/f940695505f2be1399d23cc98182297cadf6f90d.xml",
    "Jina AI": "https://jina.ai/feed.rss",
    "Last Week in AI": "https://lastweekin.ai/feed",
    "Latent Space": "https://www.latent.space/feed",
    "The Batch": "https://rsshub.bestblogs.dev/deeplearning/the-batch",
    "Turing Post": "https://rss.beehiiv.com/feeds/UJIoBuf5BX.xml",
    "宝玉的分享": "https://s.baoyu.io/feed.xml",
    "新智元": "https://wechat2rss.bestblogs.dev/feed/e531a18b21c34cf787b83ab444eef659d7a980de.xml",
    "机器之心": "https://wechat2rss.bestblogs.dev/feed/8d97af31b0de9e48da74558af128a4673d78c9a3.xml",
    "量子位": "https://www.qbitai.com/feed",
    # Other curated (8)
    "Hacker News": "https://news.ycombinator.com/rss",
    "Simon Willison": "https://simonwillison.net/atom/everything/",
    "LangChain Blog": "https://blog.langchain.com/rss/",
    "HuggingFace Blog": "https://huggingface.co/blog/feed.xml",
    "AIGC Weekly": "https://quaily.com/op7418/feed/atom",
    "36kr": "https://36kr.com/feed",
    "TechCrunch": "https://techcrunch.com/feed/",
    "GitHub Trending Weekly": "https://mshibanami.github.io/GitHubTrendingRSS/weekly/all.xml",
}

# Only include articles from the last N days
LOOKBACK_DAYS = 7

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) DailyDigest/1.0"
}


def parse_date(date_str: str) -> Optional[datetime]:
    """Try common RSS/Atom date formats."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 822
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",            # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def fetch_feed(name: str, url: str, cutoff: datetime) -> List[Dict]:
    """Fetch and parse a single RSS/Atom feed, return recent articles."""
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=15) as resp:
            data = resp.read()
    except (URLError, TimeoutError, OSError) as e:
        print(f"[WARN] {name}: fetch failed - {e}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"[WARN] {name}: parse failed - {e}", file=sys.stderr)
        return []

    articles = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # Try RSS 2.0 items
    items = root.findall(".//item")
    if not items:
        # Try Atom entries
        items = root.findall(".//atom:entry", ns)
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    def _find_first(parent, tags):
        """Find first matching element (avoids Element bool pitfall)."""
        for tag in tags:
            el = parent.find(tag) if ":" not in tag or tag.startswith("{") else parent.find(tag, ns)
            if el is not None:
                return el
        return None

    for item in items:
        # Title
        title_el = _find_first(item, [
            "title", "atom:title", "{http://www.w3.org/2005/Atom}title",
        ])
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        # Link
        link = ""
        link_el = item.find("link")
        if link_el is not None:
            link = link_el.text.strip() if link_el.text else link_el.get("href", "")
        if not link:
            link_el = _find_first(item, [
                "atom:link", "{http://www.w3.org/2005/Atom}link",
            ])
            if link_el is not None:
                link = link_el.get("href", "")

        # Date
        date_str = ""
        for tag in ["pubDate", "published", "updated", "dc:date",
                     "{http://www.w3.org/2005/Atom}published",
                     "{http://www.w3.org/2005/Atom}updated",
                     "{http://purl.org/dc/elements/1.1/}date"]:
            el = item.find(tag)
            if el is not None and el.text:
                date_str = el.text
                break

        pub_date = parse_date(date_str) if date_str else None

        # Filter by cutoff (skip if date unknown but keep first 3 per feed)
        if pub_date and pub_date < cutoff:
            continue

        # Description/summary (truncate to save tokens)
        desc = ""
        for tag in ["description", "summary", "content:encoded",
                     "{http://www.w3.org/2005/Atom}summary",
                     "{http://www.w3.org/2005/Atom}content"]:
            el = item.find(tag)
            if el is not None and el.text:
                desc = el.text.strip()[:300]
                break

        if title:
            articles.append({
                "source": name,
                "title": title,
                "link": link,
                "date": pub_date.isoformat() if pub_date else "",
                "summary": desc,
            })

        # Cap per feed to avoid token explosion
        if len(articles) >= 10:
            break

    return articles


def fetch_github_trending() -> List[Dict]:
    """Fetch GitHub daily trending repos by parsing the trending page."""
    import re
    url = "https://github.com/trending?since=daily"
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except (URLError, TimeoutError, OSError) as e:
        print(f"[WARN] GitHub Trending: fetch failed - {e}", file=sys.stderr)
        return []

    repos = []
    # Split by Box-row to get each repo block
    rows = re.split(r'class="Box-row"', html)[1:]

    for row in rows:
        # Repo name
        rm = re.search(r'<h2[^>]*>.*?href="/([^"]+)"', row, re.DOTALL)
        if not rm:
            continue
        repo_path = rm.group(1).strip()
        if "/" not in repo_path:
            continue

        # Description
        desc = ""
        desc_match = re.search(
            r'<p class="col-9[^"]*"[^>]*>\s*(.+?)\s*</p>',
            row, re.DOTALL
        )
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # Language
        lang = ""
        lang_match = re.search(
            r'<span itemprop="programmingLanguage">([^<]+)</span>', row
        )
        if lang_match:
            lang = lang_match.group(1).strip()

        # Total stars: after octicon-star SVG, find next number
        total_stars = ""
        sm = re.search(r'octicon-star.*?</svg>\s*([\d,]+)', row, re.DOTALL)
        if sm:
            total_stars = sm.group(1).strip().replace(",", "")

        # Stars today
        today_stars = ""
        tm = re.search(r'([\d,]+)\s*stars\s*today', row)
        if tm:
            today_stars = tm.group(1).replace(",", "")

        repos.append({
            "repo": repo_path,
            "description": desc[:200],
            "language": lang,
            "total_stars": total_stars,
            "today_stars": today_stars,
        })

        if len(repos) >= 5:
            break

    return repos


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    all_articles = []

    with ThreadPoolExecutor(max_workers=10) as pool:
        # Submit RSS feeds
        futures = {
            pool.submit(fetch_feed, name, url, cutoff): name
            for name, url in FEEDS.items()
        }
        # Submit GitHub trending
        gh_future = pool.submit(fetch_github_trending)

        for future in as_completed(futures):
            name = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
                print(f"[OK] {name}: {len(articles)} articles", file=sys.stderr)
            except Exception as e:
                print(f"[ERR] {name}: {e}", file=sys.stderr)

        # Collect GitHub trending
        try:
            gh_repos = gh_future.result()
            print(f"[OK] GitHub Trending: {len(gh_repos)} repos", file=sys.stderr)
        except Exception as e:
            gh_repos = []
            print(f"[ERR] GitHub Trending: {e}", file=sys.stderr)

    # Sort by date (newest first), undated at the end
    all_articles.sort(key=lambda a: a["date"] or "0000", reverse=True)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "cutoff": cutoff.isoformat(),
        "total": len(all_articles),
        "feeds_count": len(FEEDS),
        "articles": all_articles,
        "github_trending": gh_repos,
    }

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
