from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup


BOILERPLATE_PATTERNS = [
    r"责任编辑[:：]\S+",
    r"来源[:：]\S+",
    r"扫一扫在手机打开当前页",
]


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\xa0", " ")
    return text


def clean_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = normalize_text(text)
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])", text)
    return [p.strip() for p in parts if p.strip()]
