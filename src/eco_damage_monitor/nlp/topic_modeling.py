from __future__ import annotations

from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer


class TopicModeler:
    def __init__(self, n_topics: int = 5) -> None:
        self.n_topics = n_topics
        self.vectorizer = TfidfVectorizer(max_features=1500)
        self.model = NMF(n_components=n_topics, random_state=42)

    def fit_transform(self, texts: list[str]) -> list[int]:
        if not texts:
            return []
        matrix = self.vectorizer.fit_transform(texts)
        topic_matrix = self.model.fit_transform(matrix)
        return topic_matrix.argmax(axis=1).tolist()

    def topic_keywords(self, top_n: int = 8) -> dict[int, list[str]]:
        feature_names = self.vectorizer.get_feature_names_out()
        output: dict[int, list[str]] = {}
        for topic_idx, topic in enumerate(self.model.components_):
            output[topic_idx] = [feature_names[i] for i in topic.argsort()[:-top_n - 1:-1]]
        return output
