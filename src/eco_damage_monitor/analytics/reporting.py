from __future__ import annotations

from collections import Counter
from datetime import datetime

import pandas as pd


class AnalyticsService:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.df = pd.DataFrame(rows)
        if not self.df.empty:
            for col in ("publish_time", "crawl_time"):
                if col in self.df.columns:
                    self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

    def time_series(self) -> list[dict]:
        if self.df.empty:
            return []
        frame = self.df.copy()
        frame["date"] = frame["publish_time"].fillna(frame["crawl_time"]).dt.date
        return frame.groupby("date").size().reset_index(name="count").to_dict("records")

    def by_region(self) -> list[dict]:
        if self.df.empty or "province" not in self.df.columns:
            return []
        frame = self.df.fillna({"province": "未知"})
        return frame.groupby(["province", "event_type"]).size().reset_index(name="count").to_dict("records")

    def by_source_type(self) -> list[dict]:
        if self.df.empty:
            return []
        return self.df.groupby("source_type").size().reset_index(name="count").to_dict("records")

    def high_impact_cases(self, top_k: int = 10) -> list[dict]:
        if self.df.empty:
            return []
        frame = self.df.copy()
        frame["impact_score"] = frame["relevance_score"].fillna(0) + frame["credibility_score"].fillna(0)
        if "law_enforcement_action_mention" in frame.columns:
            frame["impact_score"] += frame["law_enforcement_action_mention"].astype(int) * 0.4
        return frame.sort_values("impact_score", ascending=False).head(top_k).to_dict("records")

    def topic_evolution(self) -> list[dict]:
        if self.df.empty or "topic_id" not in self.df.columns:
            return []
        frame = self.df.copy()
        frame["date"] = frame["publish_time"].fillna(frame["crawl_time"]).dt.date
        return frame.groupby(["date", "topic_id"]).size().reset_index(name="count").to_dict("records")

    def map_aggregation(self) -> list[dict]:
        if self.df.empty:
            return []
        frame = self.df.fillna({"province": "未知", "city": "未知"})
        return frame.groupby(["province", "city"]).size().reset_index(name="count").to_dict("records")

    def frequent_entities(self) -> dict[str, list[tuple[str, int]]]:
        if self.df.empty:
            return {}
        enterprise_counter = Counter(x for x in self.df.get("involved_enterprise_name", []) if isinstance(x, str) and x)
        project_counter = Counter(x for x in self.df.get("involved_project_name", []) if isinstance(x, str) and x)
        place_counter = Counter()
        for names in self.df.get("normalized_place_names", []):
            if isinstance(names, list):
                place_counter.update(names)
        damage_counter = Counter()
        for names in self.df.get("damage_type", []):
            if isinstance(names, list):
                damage_counter.update(names)
        return {
            "enterprises": enterprise_counter.most_common(10),
            "projects": project_counter.most_common(10),
            "places": place_counter.most_common(10),
            "damage_types": damage_counter.most_common(10),
        }

    def rectification_ratio(self) -> dict[str, float]:
        if self.df.empty:
            return {"rectification_ratio": 0.0, "restoration_ratio": 0.0}
        total = len(self.df)
        return {
            "rectification_ratio": float(self.df["rectification_progress"].notna().sum() / total),
            "restoration_ratio": float(self.df["restoration_action_mention"].fillna(False).astype(int).sum() / total),
        }

    def enforcement_and_restoration_list(self) -> list[dict]:
        if self.df.empty:
            return []
        frame = self.df[
            self.df["law_enforcement_action_mention"].fillna(False)
            | self.df["restoration_action_mention"].fillna(False)
        ]
        return frame[["title", "url", "event_type", "province", "publish_time"]].to_dict("records")

    def markdown_report(self, period_name: str = "日报") -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        top_cases = self.high_impact_cases(5)
        lines = [
            f"# 广域生态破坏信息{period_name}",
            "",
            f"- 生成日期：{today}",
            f"- 样本总量：{len(self.rows)}",
            "",
            "## 时间趋势",
        ]
        lines.extend([f"- {item['date']}: {item['count']}" for item in self.time_series()[:10]])
        lines.append("")
        lines.append("## 典型高影响案例")
        lines.extend([f"- {item['title']} | {item.get('province', '未知')} | {item['url']}" for item in top_cases])
        return "\n".join(lines)
