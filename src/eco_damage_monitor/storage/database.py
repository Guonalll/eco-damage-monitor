from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, MetaData, String, Table, Text, create_engine, select
from sqlalchemy.engine import Engine

from eco_damage_monitor.models.schemas import EcoDocument


metadata = MetaData()

documents = Table(
    "documents",
    metadata,
    Column("doc_id", String(128), primary_key=True),
    Column("title", String(500), nullable=False),
    Column("content", Text, nullable=False),
    Column("summary", Text),
    Column("source_name", String(128)),
    Column("source_type", String(64)),
    Column("publish_time", DateTime, nullable=True),
    Column("crawl_time", DateTime, nullable=False),
    Column("url", String(1000), unique=True, nullable=False),
    Column("province", String(64)),
    Column("city", String(64)),
    Column("district_county", String(64)),
    Column("normalized_place_names", JSON),
    Column("lat", Float),
    Column("lon", Float),
    Column("event_type", String(128)),
    Column("damage_type", JSON),
    Column("ecosystem_type", JSON),
    Column("severity_level", String(64)),
    Column("area_affected", String(128)),
    Column("involved_project_name", String(256)),
    Column("involved_enterprise_name", String(256)),
    Column("keywords", JSON),
    Column("topic_id", String(64)),
    Column("sentiment", String(64)),
    Column("credibility_score", Float),
    Column("relevance_score", Float),
    Column("duplicate_cluster_id", String(64)),
    Column("channel", String(128)),
    Column("html", Text),
    Column("text", Text),
    Column("attachments", JSON),
    Column("hash_id", String(128)),
    Column("protected_area_mention", Boolean),
    Column("land_use_change_mention", Boolean),
    Column("illegal_mining_mention", Boolean),
    Column("illegal_construction_mention", Boolean),
    Column("illegal_logging_mention", Boolean),
    Column("river_lake_occupation_mention", Boolean),
    Column("solid_waste_dumping_mention", Boolean),
    Column("sewage_pollution_mention", Boolean),
    Column("sand_excavation_mention", Boolean),
    Column("shoreline_damage_mention", Boolean),
    Column("grassland_damage_mention", Boolean),
    Column("wetland_damage_mention", Boolean),
    Column("forest_damage_mention", Boolean),
    Column("farmland_damage_mention", Boolean),
    Column("habitat_damage_mention", Boolean),
    Column("species_impact_mention", Boolean),
    Column("restoration_action_mention", Boolean),
    Column("law_enforcement_action_mention", Boolean),
    Column("rectification_progress", String(256)),
    Column("extra", JSON),
)


class Database:
    def __init__(self, db_url: str) -> None:
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(db_url, future=True)

    def init_db(self) -> None:
        metadata.create_all(self.engine)

    def upsert_documents(self, docs: list[EcoDocument]) -> None:
        with self.engine.begin() as conn:
            for doc in docs:
                payload = doc.model_dump(mode="json")
                if payload["publish_time"]:
                    payload["publish_time"] = datetime.fromisoformat(payload["publish_time"])
                payload["crawl_time"] = datetime.fromisoformat(payload["crawl_time"])
                existing = conn.execute(select(documents.c.doc_id).where(documents.c.doc_id == doc.doc_id)).first()
                if existing:
                    conn.execute(documents.update().where(documents.c.doc_id == doc.doc_id).values(**payload))
                else:
                    conn.execute(documents.insert().values(**payload))

    def fetch_documents(self) -> list[dict]:
        with self.engine.begin() as conn:
            rows = conn.execute(select(documents)).mappings().all()
            return [dict(row) for row in rows]

    def export_jsonl(self, path: str) -> None:
        rows = self.fetch_documents()
        with Path(path).open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
