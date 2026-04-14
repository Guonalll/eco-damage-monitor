from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceRecord(BaseModel):
    source_name: str
    source_type: str
    domain: str
    region_level: str
    category: str
    allowed_methods: list[str] = Field(default_factory=list)


class EcoDocument(BaseModel):
    doc_id: str
    title: str
    content: str
    summary: str = ""
    source_name: str
    source_type: str
    publish_time: datetime | None = None
    crawl_time: datetime
    url: str
    province: str | None = None
    city: str | None = None
    district_county: str | None = None
    township_if_any: str | None = None
    normalized_place_names: list[str] = Field(default_factory=list)
    lat: float | None = None
    lon: float | None = None
    event_type: str | None = None
    damage_type: list[str] = Field(default_factory=list)
    ecosystem_type: list[str] = Field(default_factory=list)
    protected_area_mention: bool = False
    land_use_change_mention: bool = False
    illegal_mining_mention: bool = False
    illegal_construction_mention: bool = False
    illegal_logging_mention: bool = False
    river_lake_occupation_mention: bool = False
    solid_waste_dumping_mention: bool = False
    sewage_pollution_mention: bool = False
    sand_excavation_mention: bool = False
    shoreline_damage_mention: bool = False
    grassland_damage_mention: bool = False
    wetland_damage_mention: bool = False
    forest_damage_mention: bool = False
    farmland_damage_mention: bool = False
    habitat_damage_mention: bool = False
    species_impact_mention: bool = False
    restoration_action_mention: bool = False
    law_enforcement_action_mention: bool = False
    rectification_progress: str | None = None
    severity_level: str | None = None
    area_affected: str | None = None
    involved_project_name: str | None = None
    involved_enterprise_name: str | None = None
    keywords: list[str] = Field(default_factory=list)
    topic_id: str | None = None
    sentiment: str | None = None
    credibility_score: float = 0.6
    relevance_score: float = 0.0
    duplicate_cluster_id: str | None = None
    channel: str | None = None
    html: str = ""
    text: str = ""
    attachments: list[str] = Field(default_factory=list)
    hash_id: str
    extra: dict[str, Any] = Field(default_factory=dict)


class AnalysisRecord(BaseModel):
    doc_id: str
    relevance_score: float
    event_type: str | None = None
    sentiment: str | None = None
    keywords: list[str] = Field(default_factory=list)
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
