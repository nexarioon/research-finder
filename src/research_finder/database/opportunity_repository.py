from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_finder.database.models import ResearchOpportunity, ResearchTopic


class OpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_business_id(self, business_id: int) -> list[ResearchOpportunity]:
        result = await self.session.execute(
            select(ResearchOpportunity).where(ResearchOpportunity.business_id == business_id)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[ResearchOpportunity]:
        result = await self.session.execute(
            select(ResearchOpportunity).order_by(ResearchOpportunity.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_favorited(self) -> list[ResearchOpportunity]:
        result = await self.session.execute(
            select(ResearchOpportunity).where(ResearchOpportunity.is_favorited == True)
        )
        return list(result.scalars().all())

    async def save(self, data: dict) -> ResearchOpportunity:
        model = ResearchOpportunity(
            business_id=data["business_id"],
            ai_analysis_id=data.get("ai_analysis_id"),
            title=data["title"],
            description=data.get("description"),
            category=data.get("category"),
            is_favorited=data.get("is_favorited", False),
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def toggle_favorite(self, opportunity_id: int) -> bool:
        result = await self.session.execute(
            select(ResearchOpportunity).where(ResearchOpportunity.id == opportunity_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        model.is_favorited = not model.is_favorited
        await self.session.commit()
        return True

    async def delete(self, opportunity_id: int) -> bool:
        result = await self.session.execute(
            select(ResearchOpportunity).where(ResearchOpportunity.id == opportunity_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True


class TopicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_business_id(self, business_id: int) -> list[ResearchTopic]:
        result = await self.session.execute(
            select(ResearchTopic).where(ResearchTopic.business_id == business_id)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[ResearchTopic]:
        result = await self.session.execute(
            select(ResearchTopic).order_by(ResearchTopic.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_saved(self) -> list[ResearchTopic]:
        result = await self.session.execute(
            select(ResearchTopic).where(ResearchTopic.is_saved == True)
        )
        return list(result.scalars().all())

    async def get_by_id(self, topic_id: int) -> ResearchTopic | None:
        result = await self.session.execute(
            select(ResearchTopic).where(ResearchTopic.id == topic_id)
        )
        return result.scalar_one_or_none()

    async def save_topic(self, data: dict) -> ResearchTopic:
        model = ResearchTopic(
            business_id=data["business_id"],
            ai_analysis_id=data.get("ai_analysis_id"),
            opportunity_id=data.get("opportunity_id"),
            title=data["title"],
            problem_statement=data.get("problem_statement"),
            proposed_system=data.get("proposed_system"),
            target_users=data.get("target_users"),
            scope=data.get("scope"),
            validation_questions=json.dumps(data.get("validation_questions", [])),
            is_saved=data.get("is_saved", False),
            user_notes=data.get("user_notes"),
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def update(self, topic_id: int, data: dict) -> bool:
        model = await self.get_by_id(topic_id)
        if not model:
            return False
        for key, val in data.items():
            if hasattr(model, key) and key != "id":
                if key == "validation_questions" and isinstance(val, list):
                    val = json.dumps(val)
                setattr(model, key, val)
        await self.session.commit()
        return True

    async def toggle_save(self, topic_id: int) -> bool:
        model = await self.get_by_id(topic_id)
        if not model:
            return False
        model.is_saved = not model.is_saved
        await self.session.commit()
        return True

    async def delete(self, topic_id: int) -> bool:
        model = await self.get_by_id(topic_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True
