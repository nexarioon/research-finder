from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from research_finder.database.connection import Base


class BusinessStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    SAVED = "saved"
    ANALYZED = "analyzed"


class OutreachStatus(str, enum.Enum):
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


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_local_business: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    is_franchise: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    has_online_presence: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    status: Mapped[BusinessStatus] = mapped_column(
        Enum(BusinessStatus), default=BusinessStatus.DISCOVERED, nullable=False
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Score fields
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WebsiteAnalysis(Base):
    __tablename__ = "website_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    services: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_forms: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    has_booking: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    has_ecommerce: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    has_customer_portal: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    social_links: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_indicators: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, nullable=False)
    data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operational_problems: Mapped[str | None] = mapped_column(Text, nullable=True)
    info_system_opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_relevance: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResearchOpportunity(Base):
    __tablename__ = "research_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_analysis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_favorited: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResearchTopic(Base):
    __tablename__ = "research_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_analysis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_system: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_users: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_saved: Mapped[bool] = mapped_column(default=False, nullable=False)
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, nullable=False)
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email_to: Mapped[str] = mapped_column(String(200), nullable=False)
    email_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    email_body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[OutreachStatus] = mapped_column(
        Enum(OutreachStatus), default=OutreachStatus.NOT_CONTACTED, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
