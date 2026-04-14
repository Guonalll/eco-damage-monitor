from eco_damage_monitor.analytics.reporting import AnalyticsService


def test_analytics_summary() -> None:
    rows = [
        {
            "title": "a",
            "url": "u",
            "publish_time": "2026-04-10T10:00:00",
            "crawl_time": "2026-04-10T12:00:00",
            "province": "湖南省",
            "city": "岳阳市",
            "source_type": "news",
            "event_type": "湿地侵占",
            "relevance_score": 0.8,
            "credibility_score": 0.7,
            "law_enforcement_action_mention": True,
            "restoration_action_mention": True,
            "rectification_progress": "整改完成",
            "topic_id": "1",
            "involved_enterprise_name": "测试公司",
            "involved_project_name": "测试项目",
            "normalized_place_names": ["洞庭湖"],
            "damage_type": ["wetland_damage_mention"]
        }
    ]
    analytics = AnalyticsService(rows)
    assert analytics.time_series()[0]["count"] == 1
    assert analytics.rectification_ratio()["rectification_ratio"] == 1.0
