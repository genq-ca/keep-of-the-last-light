"""Turn Notion fields into platform-ready post text.

Each row carries Hook / Body or Caption / CTA / Hashtags. We assemble them in
that order. X has a hard character limit, so `compose_x` validates length and
refuses to build an over-limit tweet rather than silently truncating.
"""
from __future__ import annotations

from notion_store import Post


class ComposeError(Exception):
    """Raised when a post cannot be assembled within platform constraints."""


def _stack(post: Post, include_source: bool = False) -> str:
    parts = [post.hook, post.body, post.cta, post.hashtags]
    text = "\n\n".join(p.strip() for p in parts if p and p.strip())
    if include_source and post.source_url:
        text += f"\n\n{post.source_url}"
    return text


def compose_x(post: Post, max_len: int = 280, include_source: bool = False) -> str:
    """Assemble an X post and enforce the character limit.

    Note: X weights t.co-wrapped URLs as 23 chars and some emoji as 2, so the
    platform is the final arbiter. This check uses a plain length as a close,
    conservative approximation. Set MAX_TWEET_LEN=25000 for X Premium.
    """
    text = _stack(post, include_source=include_source)
    if len(text) > max_len:
        raise ComposeError(
            f"assembled X post is {len(text)} chars, over the {max_len} limit "
            "— trim Hook/Body/CTA/Hashtags in Notion, or raise MAX_TWEET_LEN "
            "for X Premium"
        )
    return text


def compose_generic(post: Post) -> str:
    """Fallback assembly for platforms without special constraints."""
    return _stack(post)


def compose_for(post: Post, max_len: int = 280) -> str:
    if post.platform == "X":
        return compose_x(post, max_len=max_len)
    return compose_generic(post)
