from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import delete, func, select

from research_finder.application.ai_service import AIAnalysisService
from research_finder.application.discovery_service import DiscoveryService
from research_finder.application.ranking_service import CandidateRankingService
from research_finder.config.settings import get_settings
from research_finder.database.connection import get_session, init_db
from research_finder.database.models import (
    AIAnalysis as AIAnalysisModel,
    Business as BusinessModel,
    BusinessStatus,
    Outreach as OutreachModel,
    OutreachStatus,
    ResearchOpportunity as OpportunityModel,
    ResearchTopic as TopicModel,
    WebsiteAnalysis as WebsiteAnalysisModel,
)
from research_finder.database.repositories import BusinessRepository
from research_finder.domain.models import (
    Business,
    DiscoveryFilters,
    LocationQuery,
    ScoreBreakdown,
)
from research_finder.providers.nominatim import NominatimProvider
from research_finder.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


# --- Pydantic Schemas ---
class ScanRequest(BaseModel):
    location: str
    radius_km: float = 5.0
    min_rating: float = 0.0
    min_reviews: int = 0
    categories: list[str] | None = None

class SaveBusinessesRequest(BaseModel):
    businesses: list[dict[str, Any]]

class TopicCreateRequest(BaseModel):
    business_id: int
    title: str
    problem_statement: str | None = None
    proposed_system: str | None = None
    target_users: str | None = None
    scope: str | None = None
    validation_questions: list[str] = []
    is_saved: bool = True
    user_notes: str | None = None

class OutreachCreateRequest(BaseModel):
    business_id: int
    topic_id: int | None = None
    email_to: str
    email_subject: str
    email_body: str
    status: str = "draft"

class BusinessUpdateRequest(BaseModel):
    notes: str | None = None
    status: str | None = None

class BulkOutreachRequest(BaseModel):
    limit: int = 5
    channel: str = "whatsapp"  # "whatsapp" | "email"
    category: str | None = None
    min_score: float | None = None
    only_with_contacts: bool = False
    student_name: str = "Mahasiswa Peneliti"
    university: str = "Perguruan Tinggi"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Research Prospect Finder",
        version="0.1.0",
        description="Web UI for finding research and skripsi objects from local businesses",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event() -> None:
        await init_db()

    # --- API Endpoints ---

    @app.get("/api/stats")
    async def get_dashboard_stats() -> dict[str, Any]:
        async with get_session() as session:
            total_biz = await session.scalar(select(func.count(BusinessModel.id))) or 0
            scored_biz = await session.scalar(
                select(func.count(BusinessModel.id)).where(BusinessModel.total_score.isnot(None))
            ) or 0
            analyzed_biz = await session.scalar(select(func.count(AIAnalysisModel.id))) or 0
            total_topics = await session.scalar(select(func.count(TopicModel.id))) or 0
            saved_topics = await session.scalar(
                select(func.count(TopicModel.id)).where(TopicModel.is_saved == True)
            ) or 0
            total_outreach = await session.scalar(select(func.count(OutreachModel.id))) or 0

            # Get recent 5 businesses
            recent_biz_result = await session.execute(
                select(BusinessModel).order_by(BusinessModel.created_at.desc()).limit(5)
            )
            recent_businesses = [
                {
                    "id": b.id,
                    "name": b.name,
                    "category": b.category,
                    "address": b.address,
                    "rating": b.rating,
                    "review_count": b.review_count,
                    "total_score": b.total_score,
                    "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
                for b in recent_biz_result.scalars().all()
            ]

        ai_service = AIAnalysisService()
        ai_stats = await ai_service.get_usage_stats()

        return {
            "total_businesses": total_biz,
            "scored_businesses": scored_biz,
            "analyzed_businesses": analyzed_biz,
            "total_topics": total_topics,
            "saved_topics": saved_topics,
            "total_outreach": total_outreach,
            "ai_stats": ai_stats,
            "recent_businesses": recent_businesses,
        }

    @app.get("/api/categories")
    async def list_categories() -> list[str]:
        async with get_session() as session:
            result = await session.execute(
                select(BusinessModel.category)
                .where(BusinessModel.category.isnot(None), BusinessModel.category != "")
                .distinct()
                .order_by(BusinessModel.category)
            )
            return [c for c in result.scalars().all() if c]

    @app.get("/api/businesses")
    async def list_businesses(
        search: str | None = None,
        category: str | None = None,
        status: str | None = None,
        min_rating: float | None = None,
        rating_type: str | None = None,
        min_score: float | None = None,
        has_phone: bool | None = None,
        has_website: bool | None = None,
        has_email: bool | None = None,
        has_social: bool | None = None,
        has_ai: bool | None = None,
        page: int = 1,
        limit: int = 50,
        paged: bool = False,
    ) -> Any:
        async with get_session() as session:
            query = select(BusinessModel)

            if search:
                query = query.where(
                    BusinessModel.name.ilike(f"%{search}%")
                    | BusinessModel.address.ilike(f"%{search}%")
                    | BusinessModel.category.ilike(f"%{search}%")
                )
            if category and category != "all":
                query = query.where(BusinessModel.category == category)
            if status and status != "all":
                query = query.where(BusinessModel.status == BusinessStatus(status))
            if rating_type == "none":
                query = query.where(BusinessModel.rating.is_(None) | (BusinessModel.rating == 0))
            elif min_rating is not None and min_rating > 0:
                query = query.where(BusinessModel.rating >= min_rating)
            if min_score is not None and min_score > 0:
                query = query.where(BusinessModel.total_score >= min_score)
            if has_phone:
                query = query.where(BusinessModel.phone.isnot(None), BusinessModel.phone != "")
            if has_website:
                query = query.where(BusinessModel.website.isnot(None), BusinessModel.website != "")
            if has_email:
                query = query.where(BusinessModel.email.isnot(None), BusinessModel.email != "")
            if has_social:
                query = query.where(
                    BusinessModel.id.in_(
                        select(WebsiteAnalysisModel.business_id).where(
                            WebsiteAnalysisModel.social_links.isnot(None),
                            WebsiteAnalysisModel.social_links != "[]",
                            WebsiteAnalysisModel.social_links != "",
                        )
                    )
                )
            if has_ai:
                query = query.where(
                    BusinessModel.id.in_(select(AIAnalysisModel.business_id))
                )

            total_count = await session.scalar(select(func.count()).select_from(query.subquery())) or 0

            query = query.order_by(
                BusinessModel.total_score.desc().nullslast(),
                BusinessModel.id.desc(),
            )

            if limit > 0:
                offset = max(0, (page - 1) * limit)
                query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            rows = result.scalars().all()

            businesses = []
            for b in rows:
                breakdown = json.loads(b.score_breakdown) if b.score_breakdown else None
                businesses.append(
                    {
                        "id": b.id,
                        "name": b.name,
                        "address": b.address,
                        "phone": b.phone,
                        "website": b.website,
                        "email": b.email,
                        "latitude": b.latitude,
                        "longitude": b.longitude,
                        "category": b.category,
                        "rating": b.rating,
                        "review_count": b.review_count,
                        "is_local_business": b.is_local_business,
                        "is_franchise": b.is_franchise,
                        "has_online_presence": b.has_online_presence,
                        "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                        "source": b.source,
                        "notes": b.notes,
                        "total_score": b.total_score,
                        "score_breakdown": breakdown,
                        "created_at": b.created_at.isoformat() if b.created_at else None,
                    }
                )

            if paged:
                return {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "items": businesses,
                }
            return businesses

    @app.delete("/api/businesses")
    async def clear_all_businesses() -> dict[str, Any]:
        async with get_session() as session:
            count = await session.scalar(select(func.count(BusinessModel.id))) or 0
            await session.execute(delete(WebsiteAnalysisModel))
            await session.execute(delete(AIAnalysisModel))
            await session.execute(delete(TopicModel))
            await session.execute(delete(OutreachModel))
            await session.execute(delete(BusinessModel))
            await session.commit()
            return {"status": "ok", "deleted_count": count}

    @app.get("/api/businesses/{business_id}")
    async def get_business_detail(business_id: int) -> dict[str, Any]:
        async with get_session() as session:
            b = await session.scalar(select(BusinessModel).where(BusinessModel.id == business_id))
            if not b:
                raise HTTPException(status_code=404, detail="Business not found")

            # Get website analysis if any
            wa = await session.scalar(
                select(WebsiteAnalysisModel).where(WebsiteAnalysisModel.business_id == business_id)
            )
            # Get AI analysis if any
            ai = await session.scalar(
                select(AIAnalysisModel).where(AIAnalysisModel.business_id == business_id)
            )
            # Get Topics
            topics_result = await session.execute(
                select(TopicModel).where(TopicModel.business_id == business_id)
            )
            topics = topics_result.scalars().all()
            # Get Outreach
            outreach_result = await session.execute(
                select(OutreachModel).where(OutreachModel.business_id == business_id)
            )
            outreach_list = outreach_result.scalars().all()

            return {
                "business": {
                    "id": b.id,
                    "name": b.name,
                    "address": b.address,
                    "phone": b.phone,
                    "website": b.website,
                    "email": b.email,
                    "latitude": b.latitude,
                    "longitude": b.longitude,
                    "category": b.category,
                    "rating": b.rating,
                    "review_count": b.review_count,
                    "is_local_business": b.is_local_business,
                    "is_franchise": b.is_franchise,
                    "has_online_presence": b.has_online_presence,
                    "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                    "source": b.source,
                    "notes": b.notes,
                    "total_score": b.total_score,
                    "score_breakdown": json.loads(b.score_breakdown) if b.score_breakdown else None,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                },
                "website_analysis": {
                    "title": wa.title,
                    "meta_description": wa.meta_description,
                    "services": json.loads(wa.services) if wa.services else [],
                    "has_forms": wa.has_forms,
                    "has_booking": wa.has_booking,
                    "has_ecommerce": wa.has_ecommerce,
                    "tech_indicators": json.loads(wa.tech_indicators) if wa.tech_indicators else [],
                    "social_links": json.loads(wa.social_links) if wa.social_links else [],
                }
                if wa
                else None,
                "ai_analysis": {
                    "operational_problems": ai.operational_problems,
                    "info_system_opportunities": ai.info_system_opportunities,
                    "research_relevance": ai.research_relevance,
                    "research_topics": json.loads(ai.research_topics) if ai.research_topics else [],
                    "validation_questions": json.loads(ai.validation_questions)
                    if ai.validation_questions
                    else [],
                    "model_used": ai.model_used,
                    "tokens_used": ai.tokens_used,
                    "created_at": ai.created_at.isoformat() if ai.created_at else None,
                }
                if ai
                else None,
                "topics": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "problem_statement": t.problem_statement,
                        "proposed_system": t.proposed_system,
                        "target_users": t.target_users,
                        "scope": t.scope,
                        "validation_questions": json.loads(t.validation_questions)
                        if t.validation_questions
                        else [],
                        "is_saved": t.is_saved,
                        "user_notes": t.user_notes,
                    }
                    for t in topics
                ],
                "outreach": [
                    {
                        "id": o.id,
                        "email_to": o.email_to,
                        "email_subject": o.email_subject,
                        "email_body": o.email_body,
                        "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                        "sent_at": o.sent_at.isoformat() if o.sent_at else None,
                    }
                    for o in outreach_list
                ],
            }

    @app.put("/api/businesses/{business_id}")
    async def update_business(business_id: int, req: BusinessUpdateRequest) -> dict[str, Any]:
        async with get_session() as session:
            b = await session.scalar(select(BusinessModel).where(BusinessModel.id == business_id))
            if not b:
                raise HTTPException(status_code=404, detail="Business not found")
            if req.notes is not None:
                b.notes = req.notes
            if req.status is not None:
                b.status = BusinessStatus(req.status)
            await session.commit()
            return {"status": "ok", "id": business_id}

    @app.delete("/api/businesses/{business_id}")
    async def delete_business(business_id: int) -> dict[str, Any]:
        async with get_session() as session:
            await session.execute(
                delete(WebsiteAnalysisModel).where(WebsiteAnalysisModel.business_id == business_id)
            )
            await session.execute(
                delete(AIAnalysisModel).where(AIAnalysisModel.business_id == business_id)
            )
            await session.execute(
                delete(TopicModel).where(TopicModel.business_id == business_id)
            )
            await session.execute(
                delete(OutreachModel).where(OutreachModel.business_id == business_id)
            )
            await session.execute(
                delete(BusinessModel).where(BusinessModel.id == business_id)
            )
            await session.commit()
            return {"status": "ok", "deleted_id": business_id}

    # --- Discovery & Scanning ---

    @app.post("/api/discovery/scan")
    async def scan_businesses(req: ScanRequest) -> dict[str, Any]:
        provider = NominatimProvider()
        lat, lon = await provider.geocode(req.location)
        if lat is None or lon is None:
            raise HTTPException(status_code=400, detail=f"Location not found: '{req.location}'")

        location = LocationQuery(
            latitude=lat,
            longitude=lon,
            radius_km=req.radius_km,
            address=req.location,
        )
        filters = DiscoveryFilters(
            min_rating=req.min_rating,
            min_review_count=req.min_reviews,
            categories=req.categories or [],
        )

        service = DiscoveryService(provider)
        discovered = await service.discover_businesses(
            location=location,
            filters=filters,
            categories=req.categories if req.categories else None,
        )

        return {
            "location": req.location,
            "latitude": lat,
            "longitude": lon,
            "count": len(discovered),
            "businesses": [
                {
                    "name": b.name,
                    "address": b.address,
                    "phone": b.phone,
                    "website": b.website,
                    "email": b.email,
                    "latitude": b.latitude,
                    "longitude": b.longitude,
                    "category": b.category,
                    "rating": b.rating,
                    "review_count": b.review_count,
                    "is_local_business": b.is_local_business,
                    "is_franchise": b.is_franchise,
                    "has_online_presence": b.has_online_presence,
                    "source": b.source,
                    "external_id": b.external_id,
                }
                for b in discovered
            ],
        }

    @app.post("/api/discovery/save")
    async def save_discovered_businesses(req: SaveBusinessesRequest) -> dict[str, Any]:
        domain_businesses = []
        for d in req.businesses:
            domain_businesses.append(
                Business(
                    name=d["name"],
                    address=d.get("address"),
                    phone=d.get("phone"),
                    website=d.get("website"),
                    email=d.get("email"),
                    latitude=d.get("latitude"),
                    longitude=d.get("longitude"),
                    category=d.get("category"),
                    rating=d.get("rating"),
                    review_count=d.get("review_count"),
                    is_local_business=d.get("is_local_business"),
                    is_franchise=d.get("is_franchise"),
                    has_online_presence=d.get("has_online_presence"),
                    source=d.get("source", "nominatim"),
                    external_id=d.get("external_id"),
                )
            )

        async with get_session() as session:
            repo = BusinessRepository(session)
            saved = await repo.save_many(domain_businesses)

        return {"status": "ok", "saved_count": len(saved)}

    # --- Scoring ---

    @app.post("/api/scoring/run-all")
    async def score_all_businesses() -> dict[str, Any]:
        ranking_service = CandidateRankingService()
        count = await ranking_service.score_all_unscored()
        return {"status": "ok", "scored_count": count}

    @app.post("/api/scoring/{business_id}")
    async def score_single_business(business_id: int) -> dict[str, Any]:
        from research_finder.services.scoring import ScoringService

        async with get_session() as session:
            b = await session.scalar(select(BusinessModel).where(BusinessModel.id == business_id))
            if not b:
                raise HTTPException(status_code=404, detail="Business not found")

            domain_biz = Business(
                id=b.id,
                name=b.name,
                rating=b.rating,
                review_count=b.review_count,
                is_franchise=b.is_franchise,
                website=b.website,
                email=b.email,
                phone=b.phone,
                address=b.address,
                category=b.category,
                has_online_presence=b.has_online_presence,
            )
            scoring_service = ScoringService()
            breakdown = scoring_service.score_business(domain_biz)

            b.total_score = breakdown.total
            b.score_breakdown = json.dumps(
                {
                    "business_size": breakdown.business_size,
                    "online_presence": breakdown.online_presence,
                    "customer_signal": breakdown.customer_signal,
                    "operational_complexity": breakdown.operational_complexity,
                    "research_accessibility": breakdown.research_accessibility,
                    "contact_availability": breakdown.contact_availability,
                    "total": breakdown.total,
                }
            )
            await session.commit()

            return {
                "status": "ok",
                "total_score": breakdown.total,
                "breakdown": json.loads(b.score_breakdown),
            }

    # --- AI Analysis ---

    @app.post("/api/ai/analyze/{business_id}")
    async def analyze_business_with_ai(
        business_id: int, force: bool = False
    ) -> dict[str, Any]:
        ai_service = AIAnalysisService()
        if not await ai_service.is_enabled():
            raise HTTPException(
                status_code=400,
                detail="AI provider is not configured. Please check RF_AI_ENABLED and RF_AI_API_KEY in .env",
            )

        result = await ai_service.analyze_business(business_id, force_reanalyze=force)

        # Auto-create research topics in DB from AI analysis result if any
        if result.research_topics:
            async with get_session() as session:
                for topic_title in result.research_topics:
                    # Check if already exists
                    existing = await session.scalar(
                        select(TopicModel).where(
                            TopicModel.business_id == business_id,
                            TopicModel.title == topic_title,
                        )
                    )
                    if not existing:
                        new_topic = TopicModel(
                            business_id=business_id,
                            title=topic_title,
                            problem_statement=result.operational_problems,
                            proposed_system=result.info_system_opportunities,
                            scope=result.research_relevance,
                            validation_questions=json.dumps(result.validation_questions),
                            is_saved=False,
                        )
                        session.add(new_topic)
                await session.commit()

        return {
            "status": "ok",
            "business_id": business_id,
            "operational_problems": result.operational_problems,
            "info_system_opportunities": result.info_system_opportunities,
            "research_relevance": result.research_relevance,
            "research_topics": result.research_topics,
            "validation_questions": result.validation_questions,
            "model_used": result.model_used,
            "tokens_used": result.tokens_used,
        }

    # --- Topics ---

    @app.get("/api/topics")
    async def list_topics(
        saved_only: bool = False,
        business_id: int | None = None,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            query = select(TopicModel, BusinessModel.name.label("business_name")).join(
                BusinessModel, TopicModel.business_id == BusinessModel.id, isouter=True
            )
            if saved_only:
                query = query.where(TopicModel.is_saved == True)
            if business_id:
                query = query.where(TopicModel.business_id == business_id)

            query = query.order_by(TopicModel.created_at.desc())
            result = await session.execute(query)
            rows = result.all()

            topics = []
            for t, biz_name in rows:
                topics.append(
                    {
                        "id": t.id,
                        "business_id": t.business_id,
                        "business_name": biz_name or f"Business #{t.business_id}",
                        "title": t.title,
                        "problem_statement": t.problem_statement,
                        "proposed_system": t.proposed_system,
                        "target_users": t.target_users,
                        "scope": t.scope,
                        "validation_questions": json.loads(t.validation_questions)
                        if t.validation_questions
                        else [],
                        "is_saved": t.is_saved,
                        "user_notes": t.user_notes,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    }
                )
            return topics

    @app.post("/api/topics")
    async def create_topic(req: TopicCreateRequest) -> dict[str, Any]:
        async with get_session() as session:
            t = TopicModel(
                business_id=req.business_id,
                title=req.title,
                problem_statement=req.problem_statement,
                proposed_system=req.proposed_system,
                target_users=req.target_users,
                scope=req.scope,
                validation_questions=json.dumps(req.validation_questions),
                is_saved=req.is_saved,
                user_notes=req.user_notes,
            )
            session.add(t)
            await session.commit()
            await session.refresh(t)
            return {"status": "ok", "id": t.id}

    @app.put("/api/topics/{topic_id}/toggle-save")
    async def toggle_save_topic(topic_id: int) -> dict[str, Any]:
        async with get_session() as session:
            t = await session.scalar(select(TopicModel).where(TopicModel.id == topic_id))
            if not t:
                raise HTTPException(status_code=404, detail="Topic not found")
            t.is_saved = not t.is_saved
            await session.commit()
            return {"status": "ok", "id": topic_id, "is_saved": t.is_saved}

    @app.delete("/api/topics/{topic_id}")
    async def delete_topic(topic_id: int) -> dict[str, Any]:
        async with get_session() as session:
            t = await session.scalar(select(TopicModel).where(TopicModel.id == topic_id))
            if not t:
                raise HTTPException(status_code=404, detail="Topic not found")
            await session.delete(t)
            await session.commit()
            return {"status": "ok", "deleted_id": topic_id}

    # --- Outreach ---

    @app.get("/api/outreach")
    async def list_outreach() -> list[dict[str, Any]]:
        async with get_session() as session:
            query = (
                select(OutreachModel, BusinessModel.name.label("business_name"))
                .join(BusinessModel, OutreachModel.business_id == BusinessModel.id, isouter=True)
                .order_by(OutreachModel.created_at.desc())
            )
            result = await session.execute(query)
            rows = result.all()

            items = []
            for o, biz_name in rows:
                items.append(
                    {
                        "id": o.id,
                        "business_id": o.business_id,
                        "business_name": biz_name or f"Business #{o.business_id}",
                        "topic_id": o.topic_id,
                        "email_to": o.email_to,
                        "email_subject": o.email_subject,
                        "email_body": o.email_body,
                        "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                        "sent_at": o.sent_at.isoformat() if o.sent_at else None,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                    }
                )
            return items

    @app.post("/api/outreach")
    async def create_outreach(req: OutreachCreateRequest) -> dict[str, Any]:
        async with get_session() as session:
            o = OutreachModel(
                business_id=req.business_id,
                topic_id=req.topic_id,
                email_to=req.email_to,
                email_subject=req.email_subject,
                email_body=req.email_body,
                status=OutreachStatus(req.status),
            )
            session.add(o)
            await session.commit()
            await session.refresh(o)
            return {"status": "ok", "id": o.id}

    @app.put("/api/outreach/{outreach_id}/status")
    async def update_outreach_status(outreach_id: int, status: str) -> dict[str, Any]:
        async with get_session() as session:
            o = await session.scalar(select(OutreachModel).where(OutreachModel.id == outreach_id))
            if not o:
                raise HTTPException(status_code=404, detail="Outreach not found")
            o.status = OutreachStatus(status)
            await session.commit()
            return {"status": "ok", "id": outreach_id, "status": o.status.value}

    @app.delete("/api/outreach/{outreach_id}")
    async def delete_outreach(outreach_id: int) -> dict[str, Any]:
        async with get_session() as session:
            o = await session.scalar(select(OutreachModel).where(OutreachModel.id == outreach_id))
            if not o:
                raise HTTPException(status_code=404, detail="Outreach not found")
            await session.delete(o)
            await session.commit()
            return {"status": "ok", "deleted_id": outreach_id}

    @app.post("/api/businesses/{business_id}/audit-website")
    async def audit_business_website(business_id: int) -> dict[str, Any]:
        async with get_session() as session:
            b = await session.scalar(select(BusinessModel).where(BusinessModel.id == business_id))
            if not b:
                raise HTTPException(status_code=404, detail="Business not found")
            if not b.website:
                raise HTTPException(status_code=400, detail="Bisnis ini belum memiliki alamat URL website")

            from research_finder.providers.website import WebsiteAnalyzer

            analyzer = WebsiteAnalyzer()
            res = await analyzer.analyze(b.website)

            wa = await session.scalar(
                select(WebsiteAnalysisModel).where(WebsiteAnalysisModel.business_id == business_id)
            )
            if not wa:
                wa = WebsiteAnalysisModel(business_id=business_id, url=b.website)
                session.add(wa)

            wa.title = res.title
            wa.meta_description = res.meta_description
            wa.services = json.dumps(res.services)
            wa.contact_details = json.dumps(res.contact_details)
            wa.has_forms = res.has_forms
            wa.has_booking = res.has_booking
            wa.has_ecommerce = res.has_ecommerce
            wa.has_customer_portal = res.has_customer_portal
            wa.social_links = json.dumps(res.social_links)
            wa.tech_indicators = json.dumps(res.tech_indicators)
            wa.error = res.error

            # If phone or email found from website, update business record
            if res.contact_details.get("phone") and not b.phone:
                b.phone = res.contact_details["phone"]
            if res.contact_details.get("email") and not b.email:
                b.email = res.contact_details["email"]
            b.has_online_presence = True

            await session.commit()
            return {
                "status": "ok",
                "business_id": business_id,
                "title": res.title,
                "contacts": res.contact_details,
                "social_links": res.social_links,
                "tech_indicators": res.tech_indicators,
                "phone": b.phone,
                "email": b.email,
            }

    @app.post("/api/outreach/generate-bulk")
    async def generate_bulk_outreach(req: BulkOutreachRequest) -> dict[str, Any]:
        ai_provider = OpenAIProvider()
        if not await ai_provider.is_available():
            raise HTTPException(
                status_code=400,
                detail="AI Provider belum aktif. Silakan cek konfigurasi RF_AI_ENABLED dan RF_AI_API_KEY di .env",
            )

        async with get_session() as session:
            query = select(BusinessModel)
            if req.category and req.category != "all":
                query = query.where(BusinessModel.category == req.category)
            if req.min_score is not None and req.min_score > 0:
                query = query.where(BusinessModel.total_score >= req.min_score)
            if req.only_with_contacts:
                if req.channel == "whatsapp":
                    query = query.where(BusinessModel.phone.isnot(None), BusinessModel.phone != "")
                else:
                    query = query.where(BusinessModel.email.isnot(None), BusinessModel.email != "")

            query = query.order_by(
                BusinessModel.total_score.desc().nullslast(),
                BusinessModel.id.desc(),
            ).limit(req.limit)

            result = await session.execute(query)
            businesses = result.scalars().all()

            if not businesses:
                return {"status": "ok", "generated_count": 0, "items": []}

            generated_items = []
            for b in businesses:
                # Retrieve AI analysis if already performed
                ai_data = await session.scalar(
                    select(AIAnalysisModel).where(AIAnalysisModel.business_id == b.id)
                )
                context = ""
                if ai_data:
                    context = f"Masalah: {ai_data.operational_problems or ''}. Solusi: {ai_data.info_system_opportunities or ''}"

                res = await ai_provider.generate_personalized_outreach(
                    business_name=b.name,
                    category=b.category or "Umum",
                    address=b.address or "",
                    context=context,
                    channel=req.channel,
                    student_name=req.student_name,
                    university=req.university,
                )

                contact_to = (b.phone if req.channel == "whatsapp" else b.email) or "-"

                outreach = OutreachModel(
                    business_id=b.id,
                    email_to=contact_to,
                    email_subject=res.get("subject", f"Permohonan Riset - {b.name}"),
                    email_body=res.get("message", ""),
                    status=OutreachStatus.DRAFT,
                )
                session.add(outreach)
                await session.flush()

                generated_items.append(
                    {
                        "id": outreach.id,
                        "business_id": b.id,
                        "business_name": b.name,
                        "contact_to": contact_to,
                        "channel": req.channel,
                        "subject": outreach.email_subject,
                        "message": outreach.email_body,
                        "phone": b.phone,
                        "email": b.email,
                    }
                )

            await session.commit()
            return {
                "status": "ok",
                "generated_count": len(generated_items),
                "items": generated_items,
            }

    # --- Export ---

    @app.get("/api/export")
    async def export_data(format: str = Query("csv", pattern="^(csv|json|markdown)$")) -> Response:
        async with get_session() as session:
            result = await session.execute(
                select(BusinessModel).order_by(BusinessModel.total_score.desc().nullslast())
            )
            businesses = result.scalars().all()

            if format == "json":
                data = [
                    {
                        "id": b.id,
                        "name": b.name,
                        "category": b.category,
                        "address": b.address,
                        "phone": b.phone,
                        "website": b.website,
                        "email": b.email,
                        "rating": b.rating,
                        "review_count": b.review_count,
                        "total_score": b.total_score,
                        "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                    }
                    for b in businesses
                ]
                return Response(
                    content=json.dumps(data, indent=2, ensure_ascii=False),
                    media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="research_prospects.json"'},
                )

            elif format == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(
                    [
                        "ID",
                        "Name",
                        "Category",
                        "Address",
                        "Phone",
                        "Email",
                        "Website",
                        "Rating",
                        "Reviews",
                        "Total Score",
                        "Status",
                    ]
                )
                for b in businesses:
                    writer.writerow(
                        [
                            b.id,
                            b.name,
                            b.category or "",
                            b.address or "",
                            b.phone or "",
                            b.email or "",
                            b.website or "",
                            b.rating or "",
                            b.review_count or "",
                            b.total_score or "",
                            b.status.value if hasattr(b.status, "value") else str(b.status),
                        ]
                    )
                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="research_prospects.csv"'},
                )

            elif format == "markdown":
                md_lines = [
                    "# Research Prospect Finder - Export Data\n",
                    f"Generated on {len(businesses)} businesses.\n",
                    "| ID | Nama Bisnis | Kategori | Rating | Skor Riset | Website |",
                    "|---|---|---|---|---|---|",
                ]
                for b in businesses:
                    website_str = f"[{b.website}]({b.website})" if b.website else "-"
                    md_lines.append(
                        f"| {b.id} | **{b.name}** | {b.category or '-'} | {b.rating or '-'} ({b.review_count or 0}) | {b.total_score or '-'} | {website_str} |"
                    )
                return Response(
                    content="\n".join(md_lines),
                    media_type="text/markdown",
                    headers={"Content-Disposition": 'attachment; filename="research_prospects.md"'},
                )

        raise HTTPException(status_code=400, detail="Invalid format")

    # --- Settings ---

    @app.get("/api/settings")
    async def get_app_settings() -> dict[str, Any]:
        s = get_settings()
        masked_key = ""
        if s.ai_api_key:
            if len(s.ai_api_key) > 8:
                masked_key = s.ai_api_key[:4] + "..." + s.ai_api_key[-4:]
            else:
                masked_key = "********"

        return {
            "ai_enabled": s.ai_enabled,
            "ai_model": s.ai_model,
            "ai_base_url": s.ai_base_url,
            "ai_api_key_masked": masked_key,
            "database_url": s.database_url,
            "default_radius_km": s.default_radius_km,
            "default_min_rating": s.default_min_rating,
            "default_min_reviews": s.default_min_reviews,
        }

    # Serve static files for Web UI SPA
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/")
        async def serve_index() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
