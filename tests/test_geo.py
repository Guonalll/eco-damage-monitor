from eco_damage_monitor.geo.normalizer import GeoNormalizer


def test_geo_normalizer() -> None:
    result = GeoNormalizer().normalize("洞庭湖湿地整改", "岳阳市启动修复")
    assert result.province == "湖南省"
    assert "洞庭湖" in result.normalized_place_names
