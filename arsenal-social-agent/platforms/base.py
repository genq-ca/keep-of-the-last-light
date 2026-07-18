"""Poster interface shared by every platform implementation."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PostResult:
    ok: bool
    permalink: str | None = None
    error: str | None = None


class Poster:
    platform: str | None = None

    def post(self, text: str) -> PostResult:  # pragma: no cover - interface
        raise NotImplementedError
