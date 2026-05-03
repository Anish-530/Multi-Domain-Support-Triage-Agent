"""Confidence scoring utilities based on FAISS retrieval similarity scores."""

from typing import List


def compute_confidence(scores: List[float]) -> float:
    if not scores:
        return 0.0

    top_scores = scores[:3]
    average_score = sum(top_scores) / len(top_scores)

    clamped_score = max(0.0, min(1.0, average_score))
    return clamped_score