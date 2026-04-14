from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    keywords: list[str]
    numeric_mentions: list[str]
    rectification_progress: str | None
    involved_enterprise_name: str | None
    involved_project_name: str | None
    flags: dict[str, bool]


RULE_FLAGS = {
    "illegal_mining_mention": [r"非法采矿", r"盗采矿产", r"矿区破坏"],
    "illegal_construction_mention": [r"违法建设", r"违建", r"违规建设"],
    "illegal_logging_mention": [r"毁林", r"乱砍滥伐"],
    "river_lake_occupation_mention": [r"占用河道", r"侵占河湖", r"围湖"],
    "solid_waste_dumping_mention": [r"倾倒固废", r"堆放固废", r"建筑垃圾倾倒"],
    "sewage_pollution_mention": [r"偷排污水", r"污水直排", r"黑臭水体"],
    "sand_excavation_mention": [r"非法采砂", r"盗采砂石"],
    "wetland_damage_mention": [r"破坏湿地", r"侵占湿地"],
    "forest_damage_mention": [r"毁林", r"破坏林地"],
    "grassland_damage_mention": [r"毁草", r"破坏草地"],
    "restoration_action_mention": [r"生态修复", r"恢复治理", r"启动修复"],
    "law_enforcement_action_mention": [r"立案查处", r"行政处罚", r"通报批评", r"罚款"],
}


class EventExtractor:
    KEYWORDS = [
        "毁林",
        "侵占生态红线",
        "违法建设",
        "偷排污水",
        "非法采矿",
        "违规开垦",
        "破坏岸线",
        "倾倒固废",
        "整改完成",
        "启动生态修复",
    ]
    NUMERIC_PATTERNS = [r"\d+(?:\.\d+)?\s*(?:亩|公顷|平方米|米|公里|立方米|起|万元|万)"]

    def extract(self, text: str) -> ExtractionResult:
        keywords = [kw for kw in self.KEYWORDS if kw in text]
        numeric_mentions = []
        for pattern in self.NUMERIC_PATTERNS:
            numeric_mentions.extend(re.findall(pattern, text))
        progress = "整改完成" if "整改完成" in text else ("整改中" if "整改" in text else None)
        enterprise = _find_named_entity(text, r"([A-Za-z0-9\u4e00-\u9fa5]{4,30}(?:公司|集团|企业))")
        project = _find_named_entity(text, r"([A-Za-z0-9\u4e00-\u9fa5]{4,40}(?:项目|工程|矿区))")
        flags = {
            field: any(re.search(pattern, text) for pattern in patterns)
            for field, patterns in RULE_FLAGS.items()
        }
        return ExtractionResult(
            keywords=keywords,
            numeric_mentions=numeric_mentions,
            rectification_progress=progress,
            involved_enterprise_name=enterprise,
            involved_project_name=project,
            flags=flags,
        )


def _find_named_entity(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None
