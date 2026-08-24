from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_finder.database.models import Outreach, OutreachStatus


class OutreachRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Outreach]:
        result = await self.session.execute(
            select(Outreach).order_by(Outreach.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_business_id(self, business_id: int) -> list[Outreach]:
        result = await self.session.execute(
            select(Outreach).where(Outreach.business_id == business_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, outreach_id: int) -> Outreach | None:
        result = await self.session.execute(
            select(Outreach).where(Outreach.id == outreach_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: OutreachStatus) -> list[Outreach]:
        result = await self.session.execute(
            select(Outreach).where(Outreach.status == status)
        )
        return list(result.scalars().all())

    async def is_do_not_contact(self, business_id: int) -> bool:
        result = await self.session.execute(
            select(Outreach).where(
                Outreach.business_id == business_id,
                Outreach.status == OutreachStatus.DO_NOT_CONTACT,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save(self, data: dict) -> Outreach:
        model = Outreach(
            business_id=data["business_id"],
            topic_id=data.get("topic_id"),
            email_to=data["email_to"],
            email_subject=data["email_subject"],
            email_body=data["email_body"],
            status=OutreachStatus(data.get("status", "draft")),
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def update_status(self, outreach_id: int, status: OutreachStatus) -> bool:
        model = await self.get_by_id(outreach_id)
        if not model:
            return False
        model.status = status
        if status == OutreachStatus.SENT:
            model.sent_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def update(self, outreach_id: int, data: dict) -> bool:
        model = await self.get_by_id(outreach_id)
        if not model:
            return False
        for key, val in data.items():
            if hasattr(model, key) and key != "id":
                if key == "status" and isinstance(val, str):
                    val = OutreachStatus(val)
                setattr(model, key, val)
        await self.session.commit()
        return True

    async def delete(self, outreach_id: int) -> bool:
        model = await self.get_by_id(outreach_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True

    async def count_by_status(self) -> dict[str, int]:
        from sqlalchemy import func
        result = await self.session.execute(
            select(Outreach.status, func.count(Outreach.id)).group_by(Outreach.status)
        )
        return {row[0].value: row[1] for row in result.all()}
