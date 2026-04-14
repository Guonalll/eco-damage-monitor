from __future__ import annotations

import json
from pathlib import Path

import typer

from eco_damage_monitor.analytics.reporting import AnalyticsService
from eco_damage_monitor.collectors.forum.example_forum import ExampleForumCollector
from eco_damage_monitor.collectors.gov.example_gov import ExampleGovCollector
from eco_damage_monitor.collectors.news.example_news import ExampleNewsCollector
from eco_damage_monitor.collectors.wechat_import.importer import WechatAuthorizedImporter
from eco_damage_monitor.config import SourceDefinition, load_settings
from eco_damage_monitor.dashboards.streamlit_app import run_dashboard
from eco_damage_monitor.dedup.simhash_deduper import SimhashDeduper
from eco_damage_monitor.extractors.event_extractor import EventExtractor
from eco_damage_monitor.geo.normalizer import GeoNormalizer
from eco_damage_monitor.nlp.event_classifier import EventClassifier
from eco_damage_monitor.nlp.relevance import RelevanceClassifier
from eco_damage_monitor.nlp.sentiment import SentimentClassifier
from eco_damage_monitor.nlp.topic_modeling import TopicModeler
from eco_damage_monitor.storage.database import Database
from eco_damage_monitor.utils.logging_utils import setup_logging

app = typer.Typer(help="广域生态破坏公开网络信息采集与分析系统 CLI")


def _collector_for_source(source: SourceDefinition, app_config):
    mapping = {
        "news": ExampleNewsCollector,
        "government": ExampleGovCollector,
        "gov": ExampleGovCollector,
        "forum": ExampleForumCollector,
    }
    collector_cls = mapping.get(source.source_type)
    if collector_cls is None:
        raise typer.BadParameter(f"Unsupported source type: {source.source_type}")
    return collector_cls(source, app_config)


@app.command("init-db")
def init_db() -> None:
    _, app_config, _, _ = load_settings()
    setup_logging(app_config.log_level)
    db = Database(app_config.db_url)
    db.init_db()
    typer.echo(f"Database initialized: {app_config.db_url}")


@app.command("collect")
def collect(only_enabled: bool = True) -> None:
    _, app_config, sources_config, _ = load_settings()
    setup_logging(app_config.log_level)
    db = Database(app_config.db_url)
    db.init_db()
    all_docs = []
    for source in sources_config.sources:
        if only_enabled and not source.enabled:
            continue
        collector = _collector_for_source(source, app_config)
        try:
            all_docs.extend(list(collector.collect()))
        finally:
            collector.close()
    db.upsert_documents(all_docs)
    typer.echo(f"Collected {len(all_docs)} documents")


@app.command("import-wechat")
def import_wechat(file_path: str) -> None:
    _, app_config, _, _ = load_settings()
    db = Database(app_config.db_url)
    db.init_db()
    importer = WechatAuthorizedImporter()
    docs = list(importer.import_exported_articles(file_path))
    db.upsert_documents(docs)
    typer.echo(f"Imported {len(docs)} authorized WeChat articles")


@app.command("analyze")
def analyze() -> None:
    _, app_config, _, _ = load_settings()
    db = Database(app_config.db_url)
    rows = db.fetch_documents()
    relevance = RelevanceClassifier()
    event_classifier = EventClassifier()
    sentiment = SentimentClassifier()
    extractor = EventExtractor()
    geo = GeoNormalizer()
    deduper = SimhashDeduper(app_config.analysis.near_duplicate_threshold)
    texts = [row.get("content", "") for row in rows]
    topic_model = TopicModeler(n_topics=min(5, max(1, len(texts)))) if texts else None
    topic_ids = topic_model.fit_transform(texts) if topic_model and texts else []
    dedup_labels = deduper.cluster(texts) if texts else []

    updated_docs = []
    for idx, row in enumerate(rows):
        text = row.get("content", "") or ""
        result = extractor.extract(text)
        geo_result = geo.normalize(row.get("title", ""), text)
        row["relevance_score"] = relevance.score(text)
        row["event_type"] = event_classifier.predict(text)
        row["sentiment"] = sentiment.predict(text)
        row["keywords"] = result.keywords
        row["rectification_progress"] = result.rectification_progress
        row["involved_enterprise_name"] = result.involved_enterprise_name
        row["involved_project_name"] = result.involved_project_name
        row["province"] = row.get("province") or geo_result.province
        row["city"] = row.get("city") or geo_result.city
        row["district_county"] = row.get("district_county") or geo_result.district_county
        row["normalized_place_names"] = geo_result.normalized_place_names
        row["topic_id"] = str(topic_ids[idx]) if idx < len(topic_ids) else None
        row["duplicate_cluster_id"] = str(dedup_labels[idx]) if idx < len(dedup_labels) else None
        row["damage_type"] = [key for key, val in result.flags.items() if val]
        row.update(result.flags)
        updated_docs.append(row)

    from eco_damage_monitor.models.schemas import EcoDocument

    docs = [EcoDocument.model_validate(doc) for doc in updated_docs]
    db.upsert_documents(docs)
    typer.echo(f"Analyzed {len(docs)} documents")


@app.command("export")
def export(output: str = "data/exports/documents.jsonl") -> None:
    _, app_config, _, _ = load_settings()
    db = Database(app_config.db_url)
    db.export_jsonl(output)
    typer.echo(f"Exported data to {output}")


@app.command("generate-report")
def generate_report(output: str = "data/exports/daily_report.md", period_name: str = "日报") -> None:
    _, app_config, _, _ = load_settings()
    db = Database(app_config.db_url)
    analytics = AnalyticsService(db.fetch_documents())
    report = analytics.markdown_report(period_name)
    Path(output).write_text(report, encoding="utf-8")
    typer.echo(f"Generated report: {output}")


@app.command("pipeline-run")
def pipeline_run() -> None:
    init_db()
    analyze()
    generate_report()


@app.command("seed-demo")
def seed_demo(input_file: str = "tests/fixtures/sample_docs.json") -> None:
    _, app_config, _, _ = load_settings()
    db = Database(app_config.db_url)
    db.init_db()
    from eco_damage_monitor.models.schemas import EcoDocument

    rows = json.loads(Path(input_file).read_text(encoding="utf-8"))
    docs = [EcoDocument.model_validate(row) for row in rows]
    db.upsert_documents(docs)
    typer.echo(f"Seeded {len(docs)} demo documents")


@app.command("dashboard")
def dashboard() -> None:
    run_dashboard()
