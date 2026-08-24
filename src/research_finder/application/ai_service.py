from __future__ import annotations

import json
import logging

from sqlalchemy import select

from research_finder.config.settings import get_settings
from research_finder.database.ai_repository import AIAnalysisRepository
from research_finder.database.connection import get_session_factory
from research_finder.database.models import Business as BusinessModel
from research_finder.domain.models import AIAnalysisResult
from research_finder.providers.ai_base import compute_data_hash
from research_finder.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class AIAnalysisService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._provider = OpenAIProvider()
        self._session_factory = get_session_factory()

    async def is_enabled(self) -> bool:
        return await self._provider.is_available()

    async def get_usage_stats(self) -> dict:
        async with self._session_factory() as session:
            repo = AIAnalysisRepository(session)
            today_count = await repo.count_today()
            today_tokens = await repo.get_total_tokens_today()
            return {
                "enabled": await self.is_enabled(),
                "model": self._settings.ai_model,
                "analyses_today": today_count,
                "max_per_day": self._settings.ai_max_analyses_per_day,
                "remaining_today": max(0, self._settings.ai_max_analyses_per_day - today_count),
                "tokens_today": today_tokens,
            }

    async def analyze_business(
        self,
        business_id: int,
        force_reanalyze: bool = False,
    ) -> AIAnalysisResult:
        async with self._session_factory() as session:
            biz_result = await session.execute(
                select(BusinessModel).where(BusinessModel.id == business_id)
            )
            business = biz_result.scalar_one_or_none()
            if not business:
                return AIAnalysisResult(business_id=business_id, operational_problems="Business not found.")

            business_data = {
                "name": business.name,
                "category": business.category,
                "address": business.address,
                "phone": business.phone,
                "website": business.website,
                "rating": business.rating,
                "review_count": business.review_count,
            }

            website_data = None
            if business.website:
                from research_finder.database.models import WebsiteAnalysis
                wa_result = await session.execute(
                    select(WebsiteAnalysis).where(WebsiteAnalysis.business_id == business_id)
                )
                wa = wa_result.scalar_one_or_none()
                if wa:
                    website_data = {
                        "title": wa.title,
                        "meta_description": wa.meta_description,
                        "services": json.loads(wa.services) if wa.services else [],
                        "has_forms": wa.has_forms,
                        "has_booking": wa.has_booking,
                        "has_ecommerce": wa.has_ecommerce,
                        "tech_indicators": json.loads(wa.tech_indicators) if wa.tech_indicators else [],
                        "social_links": json.loads(wa.social_links) if wa.social_links else [],
                    }

            data_hash = compute_data_hash(business_data, website_data)

            if not force_reanalyze:
                repo = AIAnalysisRepository(session)
                if await repo.has_cached_analysis(business_id, data_hash):
                    cached = await repo.get_by_business_id(business_id)
                    if cached:
                        logger.info("Returning cached AI analysis for business %d", business_id)
                        return AIAnalysisResult(
                            business_id=business_id,
                            operational_problems=cached.operational_problems,
                            info_system_opportunities=cached.info_system_opportunities,
                            research_relevance=cached.research_relevance,
                            research_topics=json.loads(cached.research_topics) if cached.research_topics else [],
                            validation_questions=json.loads(cached.validation_questions) if cached.validation_questions else [],
                            model_used=cached.model_used,
                            tokens_used=cached.tokens_used,
                        )

            ai_repo = AIAnalysisRepository(session)
            today_count = await ai_repo.count_today()
            if today_count >= self._settings.ai_max_analyses_per_day:
                return AIAnalysisResult(
                    business_id=business_id,
                    operational_problems=f"Daily limit reached ({self._settings.ai_max_analyses_per_day}). Try again tomorrow.",
                    model_used="none",
                )

        result = await self._provider.analyze_business(business.name, business_data, website_data)
        result.business_id = business_id

        async with self._session_factory() as session:
            repo = AIAnalysisRepository(session)
            await repo.save(business_id, {
                "operational_problems": result.operational_problems,
                "info_system_opportunities": result.info_system_opportunities,
                "research_relevance": result.research_relevance,
                "research_topics": result.research_topics,
                "validation_questions": result.validation_questions,
                "model_used": result.model_used,
                "tokens_used": result.tokens_used,
            }, data_hash)

        return result
