from __future__ import annotations

from typing import Any


class ReviewEngine:
    def __init__(self) -> None:
        self._reviews: list[dict[str, Any]] = []

    def submit(self, proposal: str, reviewer: str) -> dict[str, Any]:
        review = {"proposal": proposal, "reviewer": reviewer, "status": "pending"}
        self._reviews.append(review)
        return review

    def approve(self, proposal: str) -> dict[str, Any]:
        for review in self._reviews:
            if review["proposal"] == proposal:
                review["status"] = "approved"
                return review
        raise KeyError(f"Unknown proposal: {proposal}")

    def list_reviews(self) -> list[dict[str, Any]]:
        return list(self._reviews)
