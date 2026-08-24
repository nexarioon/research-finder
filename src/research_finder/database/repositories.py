from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_finder.database.models import Business as BusinessModel
from research_finder.database.models import BusinessStatus
from research_finder.domain.models import Business
from research_finder.domain.models import BusinessStatus as DomainStatus

logger = logging.getLogger(__name__)


class BusinessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_by_external_id(self, external_id: str) -> bool:
        result = await self.session.execute(
            select(BusinessModel).where(BusinessModel.external_id == external_id)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_name_and_location(
        self, name: str, latitude: float | None, longitude: float | None
    ) -> bool:
        query = select(BusinessModel).where(BusinessModel.name == name)
        if latitude and longitude:
            query = query.where(
                BusinessModel.latitude.between(latitude - 0.001, latitude + 0.001),
                BusinessModel.longitude.between(longitude - 0.001, longitude + 0.001),
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def save(self, business: Business) -> BusinessModel:
        model = BusinessModel(
            name=business.name,
            address=business.address,
            phone=business.phone,
            website=business.website,
            email=business.email,
            latitude=business.latitude,
            longitude=business.longitude,
            category=business.category,
            rating=business.rating,
            review_count=business.review_count,
            is_local_business=business.is_local_business,
            is_franchise=business.is_franchise,
            has_online_presence=business.has_online_presence,
            status=BusinessStatus(business.status.value),
            source=business.source,
            external_id=business.external_id,
            notes=business.notes,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        logger.info("Saved business: %s (id=%d)", model.name, model.id)
        return model

    async def save_many(self, businesses: list[Business]) -> list[BusinessModel]:
        saved = []
        for biz in businesses:
            is_dup = False
            if biz.external_id:
                is_dup = await self.exists_by_external_id(biz.external_id)
            if not is_dup:
                is_dup = await self.exists_by_name_and_location(
                    biz.name, biz.latitude, biz.longitude
                )
            if not is_dup:
                model = await self.save(biz)
                saved.append(model)
            else:
                logger.debug("Skipping duplicate: %s", biz.name)
        return saved

    async def get_all(self) -> list[BusinessModel]:
        result = await self.session.execute(
            select(BusinessModel).order_by(BusinessModel.name)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: DomainStatus) -> list[BusinessModel]:
        result = await self.session.execute(
            select(BusinessModel).where(
                BusinessModel.status == BusinessStatus(status.value)
            ).order_by(BusinessModel.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, business_id: int) -> BusinessModel | None:
        result = await self.session.execute(
            select(BusinessModel).where(BusinessModel.id == business_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, business_id: int, status: DomainStatus) -> bool:
        model = await self.get_by_id(business_id)
        if not model:
            return False
        model.status = BusinessStatus(status.value)
        await self.session.commit()
        return True

    async def count(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(BusinessModel.id)))
        return result.scalar() or 0

    async def count_by_status(self, status: DomainStatus) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(BusinessModel.id)).where(
                BusinessModel.status == BusinessStatus(status.value)
            )
        )
        return result.scalar() or 0

    async def get_saved(self) -> list[BusinessModel]:
        return await self.get_by_status(DomainStatus.SAVED)

    async def get_qualified(self) -> list[BusinessModel]:
        return await self.get_by_status(DomainStatus.QUALIFIED)
