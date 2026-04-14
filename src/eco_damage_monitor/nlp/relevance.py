from __future__ import annotations


class RelevanceClassifier:
    KEYWORDS = [
        "生态破坏",
        "毁林",
        "湿地",
        "非法采矿",
        "非法采砂",
        "水体污染",
        "固废",
        "自然保护区",
        "生态修复",
        "违法建设",
    ]

    def score(self, text: str) -> float:
        if not text:
            return 0.0
        hits = sum(1 for kw in self.KEYWORDS if kw in text)
        return min(1.0, hits / max(3, len(self.KEYWORDS) / 2))

    def is_relevant(self, text: str, threshold: float = 0.35) -> bool:
        return self.score(text) >= threshold
