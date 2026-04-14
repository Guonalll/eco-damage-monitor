from eco_damage_monitor.extractors.event_extractor import EventExtractor


def test_event_extractor_flags_and_numbers() -> None:
    text = "某公司非法采砂5000立方米，占用河道300米，立案查处3起。"
    result = EventExtractor().extract(text)
    assert "5000立方米" in result.numeric_mentions
    assert result.flags["sand_excavation_mention"] is True
    assert result.flags["law_enforcement_action_mention"] is True
