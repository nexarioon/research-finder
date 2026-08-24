from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_finder.database.models import WebsiteAnalysis


class WebsiteAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_business_id(self, business_id: int) -> WebsiteAnalysis | None:
        result = await self.session.execute(
            select(WebsiteAnalysis).where(WebsiteAnalysis.business_id == business_id)
        )
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> WebsiteAnalysis | None:
        result = await self.session.execute(
            select(WebsiteAnalysis).where(WebsiteAnalysis.url == url)
        )
        return result.scalar_one_or_none()

    async def save(self, business_id: int, data: dict) -> WebsiteAnalysis:
        existing = await self.get_by_business_id(business_id)
        if existing:
            existing.title = data.get("title")
            existing.meta_description = data.get("meta_description")
            existing.services = json.dumps(data.get("services", []))
            existing.contact_details = json.dumps(data.get("contact_details", {}))
            existing.has_forms = data.get("has_forms")
            existing.has_booking = data.get("has_booking")
            existing.has_ecommerce = data.get("has_ecommerce")
            existing.has_customer_portal = data.get("has_customer_portal")
            existing.social_links = json.dumps(data.get("social_links", []))
            existing.tech_indicators = json.dumps(data.get("tech_indicators", []))
            existing.data_hash = data.get("data_hash")
            existing.error = data.get("error")
            model = existing
        else:
            model = WebsiteAnalysis(
                business_id=business_id,
                url=data.get("url", ""),
                title=data.get("title"),
                meta_description=data.get("meta_description"),
                services=json.dumps(data.get("services", [])),
                contact_details=json.dumps(data.get("contact_details", {})),
                has_forms=data.get("has_forms"),
                has_booking=data.get("has_booking"),
                has_ecommerce=data.get("has_ecommerce"),
                has_customer_portal=data.get("has_customer_portal"),
                social_links=json.dumps(data.get("social_links", [])),
                tech_indicators=json.dumps(data.get("tech_indicators", [])),
                data_hash=data.get("data_hash"),
                error=data.get("error"),
            )
            self.session.add(model)

        await self.session.commit()
        return model

    async def has_cached_analysis(self, business_id: int, data_hash: str) -> bool:
        existing = await self.get_by_business_id(business_id)
        return existing is not None and existing.data_hash == data_hash
