from __future__ import annotations

from abc import ABC, abstractmethod

from research_finder.domain.models import Business, DiscoveryFilters, LocationQuery


class BusinessProvider(ABC):
    @abstractmethod
    async def search_businesses(
        self,
        location: LocationQuery,
        filters: DiscoveryFilters,
        category: str | None = None,
    ) -> list[Business]:
        """Search for businesses near a location with given filters."""
        ...

    @abstractmethod
    async def get_categories(self, location: LocationQuery) -> list[str]:
        """Get available business categories near a location."""
        ...

    @abstractmethod
    async def get_business_details(self, external_id: str) -> Business | None:
        """Get detailed information about a specific business."""
        ...
