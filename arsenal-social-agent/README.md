# Arsenal Social Posting Agent

Reads rows from the Notion database **"Arsenal Content — Social Posting Schedule"**,
finds posts that are due, publishes them to the right platform, and flips
`Status` → `Posted` — but **only** after a post genuinely goes live.

A row is picked up when:

- `Status` == `Not Started`, **and**
- `Scheduled Date` is on or before today.

## What works today

| Platform  | Posting |
|-----------|---------|
| X         | ✅ implemented (X API v2, OAuth 1.0a) |
| TikTok    | ⛔ stubbed — row is skipped, Status untouched |
| YouTube   | ⛔ stubbed |
| Pinterest | ⛔ stubbed |
| Instagram | ⛔ stubbed |

Each stub is a drop-in point: add a real poster mirroring `platforms/x_poster.py`
and register it in `agent.build_poster`.

## How a post is assembled

Fields are stacked in this order: **Hook → Body or Caption → CTA → Hashtags**
(blank line between each). For X the result is length-checked against
`MAX_TWEET_LEN` (280 by default). If it's over, the row is **skipped, not
truncated**, so you never publish a mangled tweet.

> Note: X counts a t.co-wrapped URL as 23 chars and some emoji as 2; the
> platform is the final arbiter. The local check is a close, conservative
> approximation.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in the values
```

**Notion:** create an internal integration at
<https://www.notion.so/my-integrations>, copy its token into `NOTION_TOKEN`,
then open the database and share it with that integration (`•••` →
Connections). `NOTION_DATABASE_ID` is the 32-char id in the database URL.

**X:** create an app at <https://developer.x.com> with **Read and Write**
permission, generate the consumer keys and user access tokens, and put all four
into `.env`. If the posting account has X Premium, set `MAX_TWEET_LEN=25000`.

## Usage

Safe by default — without `--live` it composes and prints but never posts or
writes to Notion.

```bash
# Dry-run just the row-1 X post (what we started with)
python agent.py --story 1 --platform X

# Actually publish it
python agent.py --story 1 --platform X --live

# Dry-run everything due today
python agent.py

# Publish everything due, capped at 5 rows
python agent.py --live --limit 5

# Pretend it's a specific day (useful for testing due-date logic)
python agent.py --today 2026-07-18
```

Flags: `--live`, `--platform`, `--story`, `--today`, `--limit`.

## Offline check

`selftest_row1.py` runs the captured row-1 X content through the composer with
no credentials or network — handy for verifying the compose + length guard:

```bash
python selftest_row1.py
```

It shows that row 1's X post is 289 characters, 9 over the 280 limit — so on a
standard (non-Premium) account you'd trim the copy slightly in Notion before it
will post.

## Files

- `agent.py` — CLI entry point and orchestration loop
- `config.py` — environment/secret loading
- `notion_store.py` — query due rows, mark Posted
- `compose.py` — Notion fields → platform text + length guard
- `platforms/` — `x_poster.py` (live) and `stubs.py` (the rest)
- `selftest_row1.py` — offline composer check
