"""Environment-based configuration for the Arsenal social posting agent.

All secrets come from environment variables (optionally loaded from a local
`.env` file). Nothing sensitive is ever hard-coded or committed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional; env vars still work without it.
    pass


@dataclass
class Config:
    notion_token: str
    notion_database_id: str
    x_consumer_key: str | None
    x_consumer_secret: str | None
    x_access_token: str | None
    x_access_token_secret: str | None
    max_tweet_len: int = 280


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(
            f"Missing required environment variable: {name}\n"
            "See .env.example and the README for setup."
        )
    return value


def load_config() -> Config:
    return Config(
        notion_token=_require("NOTION_TOKEN"),
        notion_database_id=_require("NOTION_DATABASE_ID"),
        x_consumer_key=os.environ.get("X_CONSUMER_KEY"),
        x_consumer_secret=os.environ.get("X_CONSUMER_SECRET"),
        x_access_token=os.environ.get("X_ACCESS_TOKEN"),
        x_access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET"),
        max_tweet_len=int(os.environ.get("MAX_TWEET_LEN", "280")),
    )
