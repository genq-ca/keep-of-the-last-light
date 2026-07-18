#!/usr/bin/env python3
"""Arsenal social posting agent.

Picks up Notion rows where Status == "Not Started" and Scheduled Date is due
(on or before today), composes platform-ready text, posts to the right
platform, and flips Status -> Posted **only** on a confirmed successful post.

Safe by default: without --live it runs a dry-run (composes and prints, never
posts, never writes to Notion).

Examples:
    # Dry-run just the row-1 X post
    python agent.py --story 1 --platform X

    # Actually publish it
    python agent.py --story 1 --platform X --live

    # Dry-run everything due today
    python agent.py
"""
from __future__ import annotations

import argparse
import datetime as dt

from compose import ComposeError, compose_for
from config import load_config
from notion_store import NotionStore, Post
from platforms.stubs import NotImplementedPoster
from platforms.x_poster import XPoster


def build_poster(platform: str | None, cfg):
    if platform == "X":
        return XPoster(cfg)
    return NotImplementedPoster(platform or "unknown")


def parse_args():
    ap = argparse.ArgumentParser(description="Arsenal social posting agent")
    ap.add_argument(
        "--live",
        action="store_true",
        help="Actually post and update Notion. Default is a dry-run.",
    )
    ap.add_argument("--platform", help="Only process this platform, e.g. X")
    ap.add_argument("--story", type=int, help="Only process this Story # (e.g. 1)")
    ap.add_argument("--today", help="Override today's date (YYYY-MM-DD) for the due check")
    ap.add_argument("--limit", type=int, help="Process at most this many rows")
    return ap.parse_args()


def select_rows(posts: list[Post], args) -> list[Post]:
    if args.platform:
        posts = [p for p in posts if p.platform == args.platform]
    if args.story is not None:
        posts = [p for p in posts if p.story == args.story]
    if args.limit:
        posts = posts[: args.limit]
    return posts


def main() -> None:
    args = parse_args()
    cfg = load_config()
    store = NotionStore(cfg.notion_token, cfg.notion_database_id)

    today = args.today or dt.date.today().isoformat()
    posts = select_rows(store.get_due_posts(today=today), args)

    mode = "LIVE" if args.live else "DRY-RUN"
    print(f"[{mode}] {len(posts)} due post(s) as of {today}\n")

    posted = failed = skipped = 0
    for p in posts:
        story = int(p.story) if p.story is not None else "?"
        print(f"— Story #{story} · {p.platform} · {p.title}")

        try:
            text = compose_for(p, max_len=cfg.max_tweet_len)
        except ComposeError as exc:
            skipped += 1
            print(f"  SKIP (compose): {exc}\n")
            continue

        print("  " + text.replace("\n", "\n  "))
        print(f"  [{len(text)} chars]")

        if not args.live:
            print("  (dry-run — not posted)\n")
            continue

        result = build_poster(p.platform, cfg).post(text)
        if result.ok:
            store.mark_posted(p.page_id)
            posted += 1
            print(f"  POSTED → {result.permalink}  ·  Notion Status → Posted\n")
        else:
            failed += 1
            print(f"  FAILED: {result.error}  (Notion left as Not Started)\n")

    print(
        f"Done. posted={posted} failed={failed} skipped={skipped} "
        f"(dry-run={not args.live})"
    )


if __name__ == "__main__":
    main()
