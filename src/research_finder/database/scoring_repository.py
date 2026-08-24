from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_finder.database.models import Business as BusinessModel
from research_finder.database.models import BusinessStatus
from research_finder.domain.models import BusinessStatus as DomainStatus
from research_finder.domain.models import ScoreBreakdown


class ScoringRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_unscored_businesses(self) -> list[BusinessModel]:
        result = await self.session.execute(
            select(BusinessModel).where(BusinessModel.total_score.is_(None))
        )
        return list(result.scalars().all())

    async def get_scored_businesses(
        self, min_score: float = 0, status: DomainStatus | None = None
    ) -> list[BusinessModel]:
        query = select(BusinessModel).where(
            BusinessModel.total_score.isnot(None),
            BusinessModel.total_score >= min_score,
        )
        if status:
            query = query.where(BusinessModel.status == BusinessStatus(status.value))
        query = query.order_by(BusinessModel.total_score.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_score(
        self, business_id: int, score: float, breakdown: ScoreBreakdown
    ) -> bool:
        result = await self.session.execute(
            select(BusinessModel).where(BusinessModel.id == business_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False

        model.total_score = score
        model.score_breakdown = json.dumps({
            "business_size": breakdown.business_size,
            "online_presence": breakdown.online_presence,
            "customer_signal": breakdown.customer_signal,
            "operational_complexity": breakdown.operational_complexity,
            "research_accessibility": breakdown.research_accessibility,
            "contact_availability": breakdown.contact_availability,
            "total": breakdown.total,
        })
        await self.session.commit()
        return True

    async def update_scores_batch(
        self, scores: list[tuple[int, float, ScoreBreakdown]]
    ) -> int:
        updated = 0
        for business_id, score, breakdown in scores:
            if await self.update_score(business_id, score, breakdown):
                updated += 1
        return updated

    async def get_top_candidates(self, limit: int = 10) -> list[BusinessModel]:
        result = await self.session.execute(
            select(BusinessModel)
            .where(BusinessModel.total_score.isnot(None))
            .order_by(BusinessModel.total_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
