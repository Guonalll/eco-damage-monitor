from __future__ import annotations

import logging
import time
import urllib.parse
import urllib.robotparser
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import UTC, datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from eco_damage_monitor.cleaners.text_cleaner import clean_html_text
from eco_damage_monitor.config import AppFileConfig, SourceDefinition
from eco_damage_monitor.models.schemas import EcoDocument
from eco_damage_monitor.utils.hashing import stable_hash


class BaseCollector(ABC):
    def __init__(self, source: SourceDefinition, app_config: AppFileConfig) -> None:
        self.source = source
        self.app_config = app_config
        self.client = httpx.Client(timeout=app_config.request.timeout, follow_redirects=True)
        self._last_request_time = 0.0
        self._robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.logger = logging.getLogger(f"eco_damage_monitor.collectors.{self.source_name}")
        self.stats: dict[str, int] = {
            "seed_urls": len(self.source.seed_urls),
            "list_pages_fetched": 0,
            "detail_pages_fetched": 0,
            "documents_collected": 0,
            "skipped": 0,
            "errors": 0,
            "robots_blocked": 0,
        }

    @property
    def source_name(self) -> str:
        return self.source.name

    @property
    def source_type(self) -> str:
        return self.source.source_type

    @property
    def domain(self) -> str:
        return self.source.domain

    @property
    def region_level(self) -> str:
        return self.source.region_level

    @property
    def category(self) -> str:
        return self.source.category

    @property
    def allowed_methods(self) -> list[str]:
        return self.source.allowed_methods

    def close(self) -> None:
        self.client.close()

    def throttle(self) -> None:
        elapsed = time.time() - self._last_request_time
        wait_time = max(0.0, self.app_config.request.rate_limit_per_domain - elapsed)
        if wait_time:
            time.sleep(wait_time)
        self._last_request_time = time.time()

    def increment_stat(self, key: str, amount: int = 1) -> None:
        self.stats[key] = self.stats.get(key, 0) + amount

    def record_skip(self, reason: str, url: str | None = None) -> None:
        self.increment_stat("skipped")
        if url:
            self.logger.info("Skipping %s: %s", url, reason)
        else:
            self.logger.info("Skipping item: %s", reason)

    def record_error(self, stage: str, url: str, exc: Exception) -> None:
        self.increment_stat("errors")
        self.logger.warning("%s failed for %s: %s", stage, url, exc)

    def record_success(self, url: str) -> None:
        self.increment_stat("documents_collected")
        self.logger.info("Collected document from %s", url)

    def get_stats_snapshot(self) -> dict[str, int]:
        return dict(self.stats)

    def _get_robot_parser(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots_cache:
            parser = urllib.robotparser.RobotFileParser()
            robots_url = f"{base}/robots.txt"
            parser.set_url(robots_url)
            last_exc: Exception | None = None
            attempts = max(1, self.app_config.request.retries)
            for _ in range(attempts):
                try:
                    self.throttle()
                    response = self.client.get(
                        robots_url,
                        headers={"User-Agent": "eco-damage-monitor/0.1"},
                    )
                    if response.status_code in (401, 403):
                        parser.disallow_all = True
                        parser.modified()
                        self._robots_cache[base] = parser
                        return parser
                    if 400 <= response.status_code < 500:
                        parser.allow_all = True
                        parser.modified()
                        self._robots_cache[base] = parser
                        return parser
                    response.raise_for_status()
                    parser.parse(response.text.splitlines())
                    parser.modified()
                    self._robots_cache[base] = parser
                    return parser
                except Exception as exc:
                    last_exc = exc
            self.logger.warning(
                "Unable to read robots.txt for %s after %s attempts; proceeding without robots enforcement: %s",
                base,
                attempts,
                last_exc,
            )
            self._robots_cache[base] = None
            return None
        return self._robots_cache[base]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=lambda state: (
            state.outcome.failed()
            and not isinstance(state.outcome.exception(), PermissionError)
        ),
    )
    def fetch(self, url: str) -> str:
        if self.app_config.respect_robots:
            parser = self._get_robot_parser(url)
            if parser is not None and not parser.can_fetch("*", url):
                self.increment_stat("robots_blocked")
                raise PermissionError(f"robots.txt disallows fetching {url}")
        self.throttle()
        response = self.client.get(url, headers={"User-Agent": "eco-damage-monitor/0.1"})
        response.raise_for_status()
        return response.text

    def build_document(
        self,
        *,
        title: str,
        url: str,
        html: str,
        text: str,
        publish_time: datetime | None,
        province: str | None = None,
        city: str | None = None,
        county: str | None = None,
        attachments: list[str] | None = None,
    ) -> EcoDocument:
        attachments = attachments or []
        doc_id = stable_hash(f"{self.source_name}|{url}")
        return EcoDocument(
            doc_id=doc_id,
            title=title,
            content=text,
            summary=text[:160],
            source_name=self.source_name,
            source_type=self.source_type,
            publish_time=publish_time,
            crawl_time=datetime.now(UTC),
            url=url,
            province=province,
            city=city,
            district_county=county,
            normalized_place_names=[],
            channel=self.source.channel,
            html=html,
            text=clean_html_text(html) if not text else text,
            attachments=attachments,
            hash_id=stable_hash(text[:500]),
        )

    @abstractmethod
    def collect(self) -> Iterable[EcoDocument]:
        raise NotImplementedError
