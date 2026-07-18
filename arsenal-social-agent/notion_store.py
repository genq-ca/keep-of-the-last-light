"""Notion access layer: read due posts and update their status.

Uses the Notion REST API (developer integration token) directly via `requests`.
This is separate from any Notion app/MCP connection — you need an internal
integration token with the target database shared to it. See the README.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import requests

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"


@dataclass
class Post:
    page_id: str
    story: float | None
    title: str
    platform: str | None
    status: str | None
    hook: str
    body: str
    cta: str
    hashtags: str
    source_url: str | None
    scheduled: str | None


class NotionStore:
    def __init__(self, token: str, database_id: str):
        self.database_id = database_id
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )

    # --- reading -----------------------------------------------------------
    @staticmethod
    def _plain(rich: list | None) -> str:
        return "".join(part.get("plain_text", "") for part in (rich or []))

    def get_due_posts(
        self,
        today: str | None = None,
        status: str = "Not Started",
    ) -> list[Post]:
        """Return posts whose Status == `status` and Scheduled Date <= today."""
        today = today or dt.date.today().isoformat()
        payload = {
            "filter": {
                "and": [
                    {"property": "Status", "select": {"equals": status}},
                    {"property": "Scheduled Date", "date": {"on_or_before": today}},
                ]
            },
            "sorts": [{"property": "Story #", "direction": "ascending"}],
        }
        results: list[dict] = []
        cursor: str | None = None
        while True:
            if cursor:
                payload["start_cursor"] = cursor
            resp = self.session.post(
                f"{API}/databases/{self.database_id}/query", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            results.extend(data["results"])
            if data.get("has_more"):
                cursor = data["next_cursor"]
            else:
                break
        return [self._parse(page) for page in results]

    def _parse(self, page: dict) -> Post:
        props = page["properties"]

        def text(name: str) -> str:
            prop = props.get(name, {})
            if prop.get("type") == "title":
                return self._plain(prop.get("title"))
            if prop.get("type") == "rich_text":
                return self._plain(prop.get("rich_text"))
            return ""

        def select(name: str) -> str | None:
            sel = props.get(name, {}).get("select")
            return sel["name"] if sel else None

        def url(name: str) -> str | None:
            return props.get(name, {}).get("url")

        def date(name: str) -> str | None:
            d = props.get(name, {}).get("date")
            return d["start"] if d else None

        def number(name: str) -> float | None:
            return props.get(name, {}).get("number")

        return Post(
            page_id=page["id"],
            story=number("Story #"),
            title=text("Post"),
            platform=select("Platform"),
            status=select("Status"),
            hook=text("Hook"),
            body=text("Body or Caption"),
            cta=text("CTA"),
            hashtags=text("Hashtags or Tags"),
            source_url=url("Source URL"),
            scheduled=date("Scheduled Date"),
        )

    # --- writing -----------------------------------------------------------
    def mark_posted(self, page_id: str) -> None:
        """Set Status -> Posted. Only call this after a confirmed live post."""
        resp = self.session.patch(
            f"{API}/pages/{page_id}",
            json={"properties": {"Status": {"select": {"name": "Posted"}}}},
        )
        resp.raise_for_status()
