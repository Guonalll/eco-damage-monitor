from __future__ import annotations

from bs4 import BeautifulSoup


def extract_main_text(html: str, selector: str | None = None) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else ""
    if selector:
        node = soup.select_one(selector)
        text = node.get_text("\n", strip=True) if node else soup.get_text("\n", strip=True)
    else:
        text = soup.get_text("\n", strip=True)
    return title, text
