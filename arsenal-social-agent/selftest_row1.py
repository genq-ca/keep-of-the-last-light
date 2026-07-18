#!/usr/bin/env python3
"""Offline self-test for the row-1 X post.

Runs the real Notion content for Story #1 / X (captured from the database)
through the composer, with no credentials or network required. Verifies the
compose + length-guard behavior that the live agent depends on.

    python selftest_row1.py
"""
from compose import ComposeError, compose_x
from notion_store import Post

ROW1_X = Post(
    page_id="3a127177-2067-8168-ab22-d5950000cff6",
    story=1,
    title="X — Morgan Rogers £105m Bid",
    platform="X",
    status="Not Started",
    hook="🚨 Arsenal are preparing a CLUB-RECORD bid.",
    body=(
        "~£105m for Morgan Rogers would beat the £100m paid for Declan Rice. "
        "Personal terms are reportedly close — Villa's valuation is the last "
        "obstacle."
    ),
    cta="Would you sanction this fee? Reply below 👇",
    hashtags="#Arsenal #MorganRogers #AFC #ArsenalTransferNews #COYG",
    source_url="https://sports.yahoo.com/articles/report-arsenal-ready-pay-105m-185000839.html",
    scheduled="2026-07-18",
)


def main() -> None:
    print("Row 1 / X — composing at the default 280-char limit:\n")
    try:
        text = compose_x(ROW1_X, max_len=280)
        print(text)
        print(f"\n[{len(text)} chars] — OK, within limit")
    except ComposeError as exc:
        print(f"ComposeError: {exc}\n")

    print("\n" + "-" * 60)
    print("Same row with MAX_TWEET_LEN raised (X Premium, 25000):\n")
    text = compose_x(ROW1_X, max_len=25000)
    print(text)
    print(f"\n[{len(text)} chars] — OK, would post")


if __name__ == "__main__":
    main()
