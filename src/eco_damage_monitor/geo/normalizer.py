from __future__ import annotations

import re
from dataclasses import dataclass


REGION_MAP = {
    "北京市": ("北京市", "北京市", None),
    "上海市": ("上海市", "上海市", None),
    "广东省": ("广东省", None, None),
    "广州市": ("广东省", "广州市", None),
    "深圳市": ("广东省", "深圳市", None),
    "湖南省": ("湖南省", None, None),
    "岳阳市": ("湖南省", "岳阳市", None),
    "洞庭湖": ("湖南省", "岳阳市", None),
    "祁连山": ("甘肃省", None, None),
}

WEAK_GEO_HINTS = ["河", "湖", "山", "矿区", "林地", "湿地", "自然保护区", "国家公园", "生态红线区", "园区", "村", "镇"]


@dataclass
class GeoResult:
    province: str | None
    city: str | None
    district_county: str | None
    normalized_place_names: list[str]
    lat: float | None = None
    lon: float | None = None


class GeoNormalizer:
    def normalize(self, title: str, content: str) -> GeoResult:
        combined = f"{title} {content}"
        found: list[str] = []
        province = city = county = None
        for place, values in REGION_MAP.items():
            if place in combined:
                found.append(place)
                province = province or values[0]
                city = city or values[1]
                county = county or values[2]
        for hint in WEAK_GEO_HINTS:
            matches = re.findall(rf"[\u4e00-\u9fa5A-Za-z0-9]{{2,20}}{hint}", combined)
            found.extend(matches[:3])
        return GeoResult(
            province=province,
            city=city,
            district_county=county,
            normalized_place_names=list(dict.fromkeys(found)),
        )
