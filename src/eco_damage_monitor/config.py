from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - fallback for lean environments
    import os

    SettingsConfigDict = dict

    class BaseSettings(BaseModel):
        def __init__(self, **data: Any) -> None:
            merged = {
                "app_config": os.getenv("ECO_MONITOR_APP_CONFIG", "configs/app.yaml"),
                "sources_config": os.getenv("ECO_MONITOR_SOURCES_CONFIG", "configs/sources.example.yaml"),
                "models_config": os.getenv("ECO_MONITOR_MODELS_CONFIG", "configs/models.example.yaml"),
                "db_url": os.getenv("ECO_MONITOR_DB_URL"),
                "log_level": os.getenv("ECO_MONITOR_LOG_LEVEL"),
            }
            merged.update(data)
            super().__init__(**merged)


class RequestConfig(BaseModel):
    timeout: int = 15
    retries: int = 3
    rate_limit_per_domain: float = 1.0


class AnalysisConfig(BaseModel):
    relevance_threshold: float = 0.35
    credibility_default: float = 0.6
    near_duplicate_threshold: int = 3


class AppFileConfig(BaseModel):
    app_name: str = "eco-damage-monitor"
    environment: str = "dev"
    log_level: str = "INFO"
    db_url: str = "sqlite:///data/eco_monitor.db"
    data_dir: str = "data"
    respect_robots: bool = True
    request: RequestConfig = Field(default_factory=RequestConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)


class SourceDefinition(BaseModel):
    name: str
    source_type: str
    domain: str
    region_level: str
    category: str
    enabled: bool = False
    seed_urls: list[str] = Field(default_factory=list)
    list_selector: str | None = None
    title_selector: str | None = None
    content_selector: str | None = None
    publish_time_selector: str | None = None
    channel: str | None = None
    allowed_methods: list[str] = Field(default_factory=lambda: ["list_detail", "known_url", "file_import"])


class SourcesFileConfig(BaseModel):
    sources: list[SourceDefinition] = Field(default_factory=list)


class ModelBackendConfig(BaseModel):
    model_config = {"protected_namespaces": ()}
    backend: str = "keyword"
    model_name: str | None = None


class ModelsFileConfig(BaseModel):
    models: dict[str, ModelBackendConfig] = Field(default_factory=dict)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ECO_MONITOR_", env_file=".env", extra="ignore")
    app_config: str = "configs/app.yaml"
    sources_config: str = "configs/sources.example.yaml"
    models_config: str = "configs/models.example.yaml"
    db_url: str | None = None
    log_level: str | None = None


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings() -> tuple[Settings, AppFileConfig, SourcesFileConfig, ModelsFileConfig]:
    env = Settings()
    app = AppFileConfig.model_validate(load_yaml(env.app_config))
    sources = SourcesFileConfig.model_validate(load_yaml(env.sources_config))
    models = ModelsFileConfig.model_validate(load_yaml(env.models_config))
    if env.db_url:
        app.db_url = env.db_url
    if env.log_level:
        app.log_level = env.log_level
    return env, app, sources, models
