from __future__ import annotations

from simhash import Simhash


class SimhashDeduper:
    def __init__(self, threshold: int = 3) -> None:
        self.threshold = threshold

    def cluster(self, texts: list[str]) -> list[int]:
        hashes = [Simhash(text).value for text in texts]
        labels = list(range(len(texts)))
        for i in range(len(hashes)):
            for j in range(i + 1, len(hashes)):
                distance = bin(hashes[i] ^ hashes[j]).count("1")
                if distance <= self.threshold:
                    labels[j] = labels[i]
        return labels
