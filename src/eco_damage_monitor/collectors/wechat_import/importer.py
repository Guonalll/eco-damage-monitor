from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from eco_damage_monitor.models.schemas import EcoDocument
from eco_damage_monitor.utils.hashing import stable_hash


class WechatAuthorizedImporter:
    source_name = "wechat_authorized_import"
    source_type = "wechat_import"

    def import_urls(self, url_file: str) -> list[dict]:
        path = Path(url_file)
        return [{"url": line.strip()} for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def import_exported_articles(self, file_path: str) -> Iterable[EcoDocument]:
        path = Path(file_path)
        if path.suffix.lower() == ".json":
            rows = json.loads(path.read_text(encoding="utf-8"))
        else:
            with path.open("r", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
        for row in rows:
            content = row.get("content", "") or row.get("text", "")
            url = row.get("url", "")
            yield EcoDocument(
                doc_id=stable_hash(f"{self.source_name}|{url}|{row.get('title', '')}"),
                title=row.get("title", "未命名文章"),
                content=content,
                summary=content[:160],
                source_name=self.source_name,
                source_type=self.source_type,
                publish_time=_parse_dt(row.get("publish_time")),
                crawl_time=datetime.now(UTC),
                url=url or f"authorized-import://{stable_hash(content)}",
                province=row.get("province"),
                city=row.get("city"),
                district_county=row.get("district_county"),
                normalized_place_names=[],
                channel="authorized_import",
                html=row.get("html", ""),
                text=content,
                attachments=[],
                hash_id=stable_hash(content[:500]),
            )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
