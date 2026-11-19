"""Import attributed excerpts from Horizon's official Chinese Atom feed."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

import feedparser
import httpx
from selectolax.parser import HTMLParser

FEED_URL = "https://thysrael.github.io/Horizon/feed-zh.xml"
SITE_URL = "https://thysrael.github.io/Horizon/"
MAX_RESPONSE_BYTES = 3_000_000


def safe_url(value: str | None, base: str = SITE_URL) -> str:
    if not value:
        return ""
    url = urljoin(base, value.strip())
    parsed = urlsplit(url)
    return url if parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username else ""


def parse_feed(content: bytes) -> dict:
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        raise ValueError("Horizon returned an invalid feed")
    issues, items, seen = [], [], set()
    for entry in feed.entries[:7]:
        issue_url = safe_url(str(entry.get("link") or ""))
        match = re.search(r"\d{4}-\d{2}-\d{2}", str(entry.get("title") or ""))
        if not issue_url or not match:
            continue
        issue_date = match.group()
        datetime.strptime(issue_date, "%Y-%m-%d")
        parts = entry.get("content") or []
        body = parts[0].get("value", "") if parts else entry.get("summary", "")
        tree = HTMLParser(str(body))
        for node in tree.css("script, style, iframe, form"):
            node.decompose()
        category = "精选资讯"
        issue_items = []
        for heading in tree.root.traverse():
            if heading.tag not in {"h2", "h3"}:
                continue
            if heading.tag == "h2":
                category = heading.text(strip=True)[:60] or category
                continue
            anchor = heading.css_first("a[href]")
            if not anchor:
                continue
            original_url = safe_url(anchor.attributes.get("href", ""), issue_url)
            if not original_url or original_url == issue_url or (anchor.attributes.get("href") or "").startswith("#"):
                continue
            title = " ".join(anchor.text().split())[:240]
            if not title:
                continue
            # Keep occurrences in separate issues distinct, but avoid repeated
            # links inside one digest and don't mistake the TOC for articles.
            key = (issue_date, original_url)
            if key in seen:
                continue
            seen.add(key)
            score_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", heading.text())
            score = float(score_match.group(1)) if score_match else None
            if score is not None and not 0 <= score <= 10:
                score = None
            summary, tags, discussion_url = "", [], ""
            node = heading.next
            while node and node.tag not in {"h2", "h3", "hr"}:
                text = " ".join(node.text().split())
                if node.tag == "p":
                    if not summary and text:
                        summary = text[:500]
                    if text.startswith("标签"):
                        tags = [c.text(strip=True).lstrip("#")[:60] for c in node.css("code")][:8]
                    for link in node.css("a[href]"):
                        if "社区讨论" in link.text():
                            discussion_url = safe_url(link.attributes.get("href", ""), issue_url)
                node = node.next
            fragment = heading.attributes.get("id", "")
            detail_url = issue_url + ("#" + quote(fragment, safe="-_") if fragment else "")
            issue_items.append({
                "id": f"{issue_date}:{original_url}", "title": title,
                "url": original_url, "digest_url": detail_url,
                "issue_date": issue_date, "category": category,
                "score": score, "summary": summary, "tags": tags,
                "discussion_url": discussion_url,
            })
        if issue_items:
            issues.append({"date": issue_date, "url": issue_url, "item_count": len(issue_items)})
            items.extend(issue_items)
    if not items:
        raise ValueError("Horizon feed contained no recognized articles; previous snapshot preserved")
    issues.sort(key=lambda issue: issue["date"], reverse=True)
    items.sort(key=lambda item: (item["issue_date"], item["score"] or 0), reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "horizon", "source_url": SITE_URL,
        "attribution": "Horizon · Thysrael", "latest_issue": issues[0]["date"],
        "status": {"source": "horizon", "status": "ok", "item_count": len(items)},
        "issues": issues, "items": items,
    }


def refresh(output: Path, *, client: httpx.Client | None = None) -> dict:
    owned = client is None
    session = client or httpx.Client(timeout=40, follow_redirects=True)
    try:
        # A bounded stream prevents an upstream error page or oversized feed
        # from consuming unbounded memory on the small production host.
        with session.stream("GET", FEED_URL, headers={
            "User-Agent": "HotGap/1.0 Horizon-feed-reader",
            "Accept": "application/atom+xml,application/xml",
        }) as response:
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise ValueError("Horizon feed exceeded size limit")
                chunks.append(chunk)
        payload = parse_feed(b"".join(chunks))
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
            temporary.chmod(0o644)
            temporary.replace(output)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        return payload
    finally:
        if owned:
            session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(
        os.getenv("SITE_DATA_DIR", "public/data")
    ) / "server-horizon.json")
    args = parser.parse_args()
    try:
        payload = refresh(args.output)
    except Exception as exc:
        logging.error("Horizon import failed (%s); previous snapshot preserved", type(exc).__name__)
        return 1
    print(json.dumps({"event": "horizon_captured", "item_count": len(payload["items"]),
                      "latest_issue": payload["latest_issue"], "issues": len(payload["issues"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
