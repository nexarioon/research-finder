from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class BusinessStatus(Enum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    SAVED = "saved"
    ANALYZED = "analyzed"


class OutreachStatus(Enum):
    NOT_CONTACTED = "not_contacted"
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    DELIVERED = "delivered"
    REPLIED = "replied"
    INTERESTED = "interested"
    DECLINED = "declined"
    NO_RESPONSE = "no_response"
    DO_NOT_CONTACT = "do_not_contact"


@dataclass
class Business:
    name: str
    id: int | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    email: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    category: str | None = None
    rating: float | None = None
    review_count: int | None = None
    is_local_business: bool | None = None
    is_franchise: bool | None = None
    has_online_presence: bool | None = None
    status: BusinessStatus = BusinessStatus.DISCOVERED
    source: str | None = None
    external_id: str | None = None
    notes: str | None = None
    total_score: float | None = None
    score_breakdown: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class LocationQuery:
    latitude: float
    longitude: float
    radius_km: float = 5.0
    address: str | None = None


@dataclass
class DiscoveryFilters:
    min_rating: float = 3.0
    min_review_count: int = 10
    prefer_local_business: bool = True
    prefer_franchise: bool | None = None
    prefer_online_presence: bool | None = None
    categories: list[str] = field(default_factory=list)


@dataclass
class ScoreBreakdown:
    business_size: float = 0.0
    online_presence: float = 0.0
    customer_signal: float = 0.0
    operational_complexity: float = 0.0
    research_accessibility: float = 0.0
    contact_availability: float = 0.0
    total: float = 0.0


@dataclass
class AIAnalysisResult:
    business_id: int
    operational_problems: str | None = None
    info_system_opportunities: str | None = None
    research_relevance: str | None = None
    research_topics: list[str] = field(default_factory=list)
    validation_questions: list[str] = field(default_factory=list)
    model_used: str | None = None
    tokens_used: int | None = None


@dataclass
class ResearchTopicData:
    title: str
    problem_statement: str | None = None
    proposed_system: str | None = None
    target_users: str | None = None
    scope: str | None = None
    validation_questions: list[str] = field(default_factory=list)
    source_business_id: int | None = None
    ai_analysis_id: int | None = None
