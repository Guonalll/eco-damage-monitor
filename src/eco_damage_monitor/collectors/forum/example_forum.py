from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dt_parser

from eco_damage_monitor.collectors.base import BaseCollector


class ExampleForumCollector(BaseCollector):
    def collect(self) -> Iterable:
        seen_urls: set[str] = set()
        for seed_url in self.source.seed_urls:
            try:
                self.increment_stat("list_pages_fetched")
                html = self.fetch(seed_url)
            except PermissionError as exc:
                self.record_error("List page blocked", seed_url, exc)
                continue
            except Exception as exc:
                self.record_error("List page fetch", seed_url, exc)
                continue
            soup = BeautifulSoup(html, "lxml")
            for link in soup.select(self.source.list_selector or "a"):
                href = link.get("href")
                if not href:
                    continue
                detail_url = urljoin(seed_url, href)
                parsed = urlparse(detail_url)
                if parsed.scheme not in {"http", "https"}:
                    self.record_skip("unsupported URL scheme", detail_url)
                    continue
                if self.domain not in parsed.netloc:
                    self.record_skip("outside configured domain", detail_url)
                    continue
                if any(x in detail_url.lower() for x in ["javascript:", "mailto:", "#"]):
                    self.record_skip("non-content link", detail_url)
                    continue
                if detail_url in seen_urls:
                    self.record_skip("duplicate detail URL", detail_url)
                    continue

                seen_urls.add(detail_url)
                try:
                    self.increment_stat("detail_pages_fetched")
                    detail_html = self.fetch(detail_url)
                except PermissionError as exc:
                    self.record_error("Detail page blocked", detail_url, exc)
                    continue
                except Exception as exc:
                    self.record_error("Detail page fetch", detail_url, exc)
                    continue
                detail = BeautifulSoup(detail_html, "lxml")
                title_node = detail.select_one(self.source.title_selector or "h1")
                body_node = detail.select_one(self.source.content_selector or "body")
                time_node = detail.select_one(self.source.publish_time_selector or "time")
                if not title_node or not body_node:
                    self.record_skip("missing title or body", detail_url)
                    continue
                body_text = body_node.get_text("\n", strip=True)
                if len(body_text) < 80:
                    self.record_skip("content too short", detail_url)
                    continue
                publish_time = None
                if time_node:
                    try:
                        publish_time = dt_parser.parse(time_node.get_text(strip=True))
                    except Exception:
                        publish_time = datetime.now(UTC)
                doc = self.build_document(
                    title=title_node.get_text(strip=True),
                    url=detail_url,
                    html=detail_html,
                    text=body_text,
                    publish_time=publish_time,
                )
                self.record_success(detail_url)
                yield doc
