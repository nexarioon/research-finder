from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_finder.database.models import AIAnalysis


class AIAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_business_id(self, business_id: int) -> AIAnalysis | None:
        result = await self.session.execute(
            select(AIAnalysis).where(AIAnalysis.business_id == business_id)
        )
        return result.scalar_one_or_none()

    async def has_cached_analysis(self, business_id: int, data_hash: str) -> bool:
        existing = await self.get_by_business_id(business_id)
        return existing is not None and existing.data_hash == data_hash

    async def save(self, business_id: int, data: dict, data_hash: str) -> AIAnalysis:
        existing = await self.get_by_business_id(business_id)
        if existing:
            existing.data_hash = data_hash
            existing.operational_problems = data.get("operational_problems")
            existing.info_system_opportunities = data.get("info_system_opportunities")
            existing.research_relevance = data.get("research_relevance")
            existing.research_topics = json.dumps(data.get("research_topics", []))
            existing.validation_questions = json.dumps(data.get("validation_questions", []))
            existing.model_used = data.get("model_used")
            existing.tokens_used = data.get("tokens_used")
            model = existing
        else:
            model = AIAnalysis(
                business_id=business_id,
                data_hash=data_hash,
                operational_problems=data.get("operational_problems"),
                info_system_opportunities=data.get("info_info_system_opportunities"),
                research_relevance=data.get("research_relevance"),
                research_topics=json.dumps(data.get("research_topics", [])),
                validation_questions=json.dumps(data.get("validation_questions", [])),
                model_used=data.get("model_used"),
                tokens_used=data.get("tokens_used"),
            )
            self.session.add(model)

        await self.session.commit()
        return model

    async def count_today(self) -> int:
        today = datetime.now(timezone.utc).date()
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(AIAnalysis.id)).where(
                func.date(AIAnalysis.created_at) == today
            )
        )
        return result.scalar() or 0

    async def get_total_tokens_today(self) -> int:
        today = datetime.now(timezone.utc).date()
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.coalesce(func.sum(AIAnalysis.tokens_used), 0)).where(
                func.date(AIAnalysis.created_at) == today
            )
        )
        return result.scalar() or 0
