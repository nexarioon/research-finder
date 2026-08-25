from __future__ import annotations

import json
import logging

from research_finder.database.connection import get_session_factory
from research_finder.database.scoring_repository import ScoringRepository
from research_finder.domain.models import Business, ScoreBreakdown
from research_finder.domain.models import BusinessStatus as DomainStatus

logger = logging.getLogger(__name__)


class ScoringService:
    """Calculates research suitability scores for businesses."""

    def score_business(self, business: Business) -> ScoreBreakdown:
        # 1. Business Size & Scale (max 25)
        # Small/local independent businesses score higher for thesis viability
        size_score = 25.0
        if business.is_franchise:
            size_score = 8.0

        # 2. Operational Complexity (max 30)
        # Businesses with higher inventory/workflow complexity score higher
        category_weights = {
            "Retail": 28.0,
            "Food & Dining": 25.0,
            "Automotive": 26.0,
            "Health & Beauty": 24.0,
            "Business Services": 22.0,
            "Services": 22.0,
            "Technology": 20.0,
            "Entertainment": 18.0,
            "Financial Services": 18.0,
            "Other": 15.0,
        }
        complexity_score = category_weights.get(business.category or "Other", 18.0)

        # 3. Online Presence & Digitalization Gap (max 25)
        # High score if business exists but needs better digital systems
        online_score = 10.0
        if business.has_online_presence or business.website:
            online_score = 22.0

        # 4. Contact Availability (max 20)
        # Higher score if easy to reach out (phone/WA, email)
        contact_score = 0.0
        if business.phone:
            contact_score += 12.0
        if business.email:
            contact_score += 8.0

        total = size_score + complexity_score + online_score + contact_score
        total = round(min(100.0, max(0.0, total)), 1)

        return ScoreBreakdown(
            business_size=size_score,
            operational_complexity=complexity_score,
            online_presence=online_score,
            contact_availability=contact_score,
            total=total,
        )


class CandidateRankingService:
    def __init__(self, scoring_service: ScoringService | None = None) -> None:
        self.scoring_service = scoring_service or ScoringService()
        self._session_factory = get_session_factory()

    async def score_all_unscored(self) -> int:
        async with self._session_factory() as session:
            repo = ScoringRepository(session)
            unscored = await repo.get_unscored_businesses()

            scores = []
            for model in unscored:
                business = Business(
                    id=model.id,
                    name=model.name,
                    rating=model.rating,
                    review_count=model.review_count,
                    is_franchise=model.is_franchise,
                    website=model.website,
                    email=model.email,
                    phone=model.phone,
                    address=model.address,
                    category=model.category,
                    has_online_presence=model.has_online_presence,
                )
                breakdown = self.scoring_service.score_business(business)
                scores.append((model.id, breakdown.total, breakdown))

            updated = await repo.update_scores_batch(scores)
            logger.info("Scored %d businesses", updated)
            return updated

    async def get_ranked_candidates(
        self, min_score: float = 0, limit: int = 50
    ) -> list[tuple[Business, dict]]:
        async with self._session_factory() as session:
            repo = ScoringRepository(session)
            models = await repo.get_scored_businesses(min_score=min_score)

            results = []
            for m in models[:limit]:
                business = Business(
                    id=m.id,
                    name=m.name,
                    address=m.address,
                    phone=m.phone,
                    website=m.website,
                    email=m.email,
                    category=m.category,
                    rating=m.rating,
                    review_count=m.review_count,
                    total_score=m.total_score,
                    status=DomainStatus(m.status.value),
                )
                breakdown = json.loads(m.score_breakdown) if m.score_breakdown else {}
                results.append((business, breakdown))

            return results

    async def select_top_candidates(self, business_ids: list[int]) -> int:
        async with self._session_factory() as session:
            from sqlalchemy import select

            from research_finder.database.models import Business as BusinessModel
            from research_finder.database.models import BusinessStatus

            count = 0
            for bid in business_ids:
                result = await session.execute(
                    select(BusinessModel).where(BusinessModel.id == bid)
                )
                model = result.scalar_one_or_none()
                if model:
                    model.status = BusinessStatus.SAVED
                    count += 1
            await session.commit()
            return count
