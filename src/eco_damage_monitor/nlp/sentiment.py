from __future__ import annotations


SENTIMENT_RULES = {
    "中性通报": ["通报", "发布", "印发"],
    "风险担忧": ["风险", "担忧", "隐患"],
    "举报投诉": ["举报", "投诉", "反映"],
    "媒体批评": ["曝光", "批评", "质疑"],
    "整改反馈": ["整改", "完成治理", "修复完成"],
}


class SentimentClassifier:
    def predict(self, text: str) -> str:
        for label, patterns in SENTIMENT_RULES.items():
            if any(p in text for p in patterns):
                return label
        return "中性通报"
