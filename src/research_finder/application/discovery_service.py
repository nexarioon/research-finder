from __future__ import annotations

import logging

from research_finder.database.connection import get_session_factory
from research_finder.database.repositories import BusinessRepository
from research_finder.domain.models import Business, BusinessStatus as DomainStatus, DiscoveryFilters, LocationQuery
from research_finder.providers.base import BusinessProvider

logger = logging.getLogger(__name__)


class DiscoveryService:
    def __init__(self, provider: BusinessProvider) -> None:
        self.provider = provider
        self._session_factory = get_session_factory()

    async def discover_businesses(
        self,
        location: LocationQuery,
        filters: DiscoveryFilters,
        categories: list[str] | None = None,
    ) -> list[Business]:
        all_businesses: list[Business] = []

        if categories:
            for cat in categories:
                results = await self.provider.search_businesses(location, filters, category=cat)
                all_businesses.extend(results)
        else:
            all_businesses = await self.provider.search_businesses(location, filters)

        logger.info("Discovered %d businesses total", len(all_businesses))
        return all_businesses

    async def save_businesses(self, businesses: list[Business]) -> list[Business]:
        for biz in businesses:
            biz.status = DomainStatus.SAVED

        async with self._session_factory() as session:
            repo = BusinessRepository(session)
            saved_models = await repo.save_many(businesses)
            return [
                Business(
                    name=m.name,
                    id=m.id,
                    address=m.address,
                    phone=m.phone,
                    website=m.website,
                    email=m.email,
                    latitude=m.latitude,
                    longitude=m.longitude,
                    category=m.category,
                    rating=m.rating,
                    review_count=m.review_count,
                    is_local_business=m.is_local_business,
                    is_franchise=m.is_franchise,
                    has_online_presence=m.has_online_presence,
                )
                for m in saved_models
            ]

    async def get_categories(self, location: LocationQuery) -> list[str]:
        return await self.provider.get_categories(location)
