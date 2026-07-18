"""Post to X (Twitter) via the v2 API using OAuth 1.0a user context.

Requires an X developer app with Read+Write permission and user access
tokens. tweepy handles the OAuth 1.0a signing needed to create tweets.
"""
from __future__ import annotations

from .base import Poster, PostResult


class XPoster(Poster):
    platform = "X"

    def __init__(self, cfg):
        missing = [
            name
            for name, value in {
                "X_CONSUMER_KEY": cfg.x_consumer_key,
                "X_CONSUMER_SECRET": cfg.x_consumer_secret,
                "X_ACCESS_TOKEN": cfg.x_access_token,
                "X_ACCESS_TOKEN_SECRET": cfg.x_access_token_secret,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"X credentials missing: {', '.join(missing)}")

        import tweepy  # imported lazily so dry-runs don't need the dependency

        self._client = tweepy.Client(
            consumer_key=cfg.x_consumer_key,
            consumer_secret=cfg.x_consumer_secret,
            access_token=cfg.x_access_token,
            access_token_secret=cfg.x_access_token_secret,
        )

    def post(self, text: str) -> PostResult:
        try:
            resp = self._client.create_tweet(text=text)
            tweet_id = resp.data["id"]
            return PostResult(
                ok=True, permalink=f"https://x.com/i/web/status/{tweet_id}"
            )
        except Exception as exc:  # surface the API error; caller leaves row untouched
            return PostResult(ok=False, error=str(exc))
