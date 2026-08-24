from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from research_finder.domain.models import Business, ScoreBreakdown

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    business_size: float = 0.25
    online_presence: float = 0.15
    customer_signal: float = 0.15
    operational_complexity: float = 0.20
    research_accessibility: float = 0.15
    contact_availability: float = 0.10

    def validate(self) -> bool:
        total = (
            self.business_size
            + self.online_presence
            + self.customer_signal
            + self.operational_complexity
            + self.research_accessibility
            + self.contact_availability
        )
        return abs(total - 1.0) < 0.01


DEFAULT_WEIGHTS = ScoringWeights()


class ScoringService:
    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS
        if not self.weights.validate():
            raise ValueError("Scoring weights must sum to 1.0")

    def score_business(self, business: Business) -> ScoreBreakdown:
        breakdown = ScoreBreakdown(
            business_size=self._score_business_size(business),
            online_presence=self._score_online_presence(business),
            customer_signal=self._score_customer_signal(business),
            operational_complexity=self._score_operational_complexity(business),
            research_accessibility=self._score_research_accessibility(business),
            contact_availability=self._score_contact_availability(business),
        )

        breakdown.total = round(
            (
                breakdown.business_size * self.weights.business_size
                + breakdown.online_presence * self.weights.online_presence
                + breakdown.customer_signal * self.weights.customer_signal
                + breakdown.operational_complexity * self.weights.operational_complexity
                + breakdown.research_accessibility * self.weights.research_accessibility
                + breakdown.contact_availability * self.weights.contact_availability
            ),
            1,
        )

        return breakdown

    def _score_business_size(self, business: Business) -> float:
        score = 50.0

        if business.review_count is not None:
            if business.review_count >= 500:
                score += 30
            elif business.review_count >= 100:
                score += 20
            elif business.review_count >= 50:
                score += 15
            elif business.review_count >= 20:
                score += 10
            elif business.review_count >= 10:
                score += 5

        if business.rating is not None:
            if business.rating >= 4.5:
                score += 10
            elif business.rating >= 4.0:
                score += 5
            elif business.rating >= 3.5:
                score += 0
            else:
                score -= 5

        if business.is_franchise is True:
            score += 10
        elif business.is_franchise is False:
            score -= 5

        return min(max(score, 0), 100)

    def _score_online_presence(self, business: Business) -> float:
        score = 20.0

        if business.website:
            score += 40
        if business.email:
            score += 20
        if business.has_online_presence:
            score += 20

        return min(max(score, 0), 100)

    def _score_customer_signal(self, business: Business) -> float:
        score = 30.0

        if business.review_count is not None:
            if business.review_count >= 100:
                score += 40
            elif business.review_count >= 50:
                score += 30
            elif business.review_count >= 20:
                score += 20
            elif business.review_count >= 10:
                score += 10

        if business.rating is not None:
            if business.rating >= 4.0:
                score += 15
            elif business.rating >= 3.5:
                score += 10
            elif business.rating >= 3.0:
                score += 5

        return min(max(score, 0), 100)

    def _score_operational_complexity(self, business: Business) -> float:
        score = 50.0

        complex_categories = {
            "Health & Beauty": 20,
            "Financial Services": 25,
            "Technology": 20,
            "Hospitality": 15,
            "Education": 15,
            "Automotive": 15,
        }

        if business.category in complex_categories:
            score += complex_categories[business.category]
        elif business.category in ("Food & Dining", "Retail"):
            score += 10

        if business.phone:
            score += 10
        if business.email:
            score += 5

        return min(max(score, 0), 100)

    def _score_research_accessibility(self, business: Business) -> float:
        score = 40.0

        if business.website:
            score += 25
        if business.phone:
            score += 15
        if business.email:
            score += 15
        if business.address:
            score += 5

        return min(max(score, 0), 100)

    def _score_contact_availability(self, business: Business) -> float:
        score = 0.0

        if business.phone:
            score += 35
        if business.email:
            score += 35
        if business.website:
            score += 20
        if business.address:
            score += 10

        return min(max(score, 0), 100)

    def score_to_dict(self, breakdown: ScoreBreakdown) -> str:
        return json.dumps({
            "business_size": breakdown.business_size,
            "online_presence": breakdown.online_presence,
            "customer_signal": breakdown.customer_signal,
            "operational_complexity": breakdown.operational_complexity,
            "research_accessibility": breakdown.research_accessibility,
            "contact_availability": breakdown.contact_availability,
            "total": breakdown.total,
        })

    def dict_to_score(self, data: str) -> ScoreBreakdown:
        d = json.loads(data)
        return ScoreBreakdown(**d)
