from datetime import datetime

from eco_damage_monitor.collectors.base import BaseCollector
from eco_damage_monitor.config import AppFileConfig, SourceDefinition


class DummyCollector(BaseCollector):
    def collect(self):
        yield self.build_document(
            title="测试",
            url="https://example.com/1",
            html="<html><body>内容</body></html>",
            text="内容",
            publish_time=datetime(2026, 4, 10, 10, 0, 0),
        )


def test_base_collector_build_document() -> None:
    source = SourceDefinition(
        name="dummy",
        source_type="news",
        domain="example.com",
        region_level="national",
        category="environment",
    )
    collector = DummyCollector(source, AppFileConfig())
    doc = list(collector.collect())[0]
    assert doc.source_name == "dummy"
    assert doc.title == "测试"
