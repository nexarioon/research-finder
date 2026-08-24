from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod

from research_finder.domain.models import AIAnalysisResult

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def analyze_business(
        self,
        business_name: str,
        business_data: dict,
        website_data: dict | None = None,
    ) -> AIAnalysisResult:
        """Analyze a business and return research insights."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the AI provider is available."""
        ...


def compute_data_hash(business_data: dict, website_data: dict | None = None) -> str:
    combined = json.dumps({"business": business_data, "website": website_data}, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()
