from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dt_parser

from eco_damage_monitor.collectors.base import BaseCollector


class ExampleGovCollector(BaseCollector):
    def collect(self) -> Iterable:
        for seed_url in self.source.seed_urls:
            html = self.fetch(seed_url)
            soup = BeautifulSoup(html, "lxml")
            for link in soup.select(self.source.list_selector or "a"):
                href = link.get("href")
                if not href:
                    continue
                detail_url = urljoin(seed_url, href)
                detail_html = self.fetch(detail_url)
                detail = BeautifulSoup(detail_html, "lxml")
                title_node = detail.select_one(self.source.title_selector or "h1")
                body_node = detail.select_one(self.source.content_selector or "body")
                time_node = detail.select_one(self.source.publish_time_selector or "time")
                if not title_node or not body_node:
                    continue
                publish_time = None
                if time_node:
                    try:
                        publish_time = dt_parser.parse(time_node.get_text(strip=True))
                    except Exception:
                        publish_time = datetime.now(UTC)
                yield self.build_document(
                    title=title_node.get_text(strip=True),
                    url=detail_url,
                    html=detail_html,
                    text=body_node.get_text("\n", strip=True),
                    publish_time=publish_time,
                )
