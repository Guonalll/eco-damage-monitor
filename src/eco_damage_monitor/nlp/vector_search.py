from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorSearchEngine:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
        self.matrix = None
        self.documents: list[dict[str, Any]] = []

    def index(self, docs: list[dict[str, Any]]) -> None:
        self.documents = docs
        corpus = [f"{doc.get('title', '')} {doc.get('content', '')}" for doc in docs]
        self.matrix = self.vectorizer.fit_transform(corpus) if corpus else None

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.matrix is None or not self.documents:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for idx, score in ranked:
            row = dict(self.documents[idx])
            row["semantic_score"] = float(score)
            results.append(row)
        return results
