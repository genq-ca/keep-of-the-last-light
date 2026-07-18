"""Placeholder posters for platforms not yet wired to a live API.

They never publish; they return a clear error so the agent skips the row and
leaves its Notion Status untouched. Replace with a real Poster (mirroring
XPoster) as each platform's posting path is added.
"""
from __future__ import annotations

from .base import Poster, PostResult


class NotImplementedPoster(Poster):
    def __init__(self, platform: str):
        self.platform = platform

    def post(self, text: str) -> PostResult:
        return PostResult(
            ok=False,
            error=f"{self.platform} posting is not implemented yet — row skipped",
        )
