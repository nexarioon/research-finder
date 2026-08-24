from __future__ import annotations

import csv
import json
from pathlib import Path

from rich.console import Console

from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_select
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.database.connection import get_session_factory
from research_finder.database.models import (
    AIAnalysis,
    Business,
    Outreach,
    ResearchOpportunity,
    ResearchTopic,
    WebsiteAnalysis,
)


class ExportScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Export your research data")

        choice = await ask_select(
            "Select export format:",
            [
                "Export businesses (CSV)",
                "Export businesses (JSON)",
                "Export research topics (Markdown)",
                "Export everything (JSON)",
                "Back to menu",
            ],
            
        )

        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        session_factory = get_session_factory()

        if choice == "Export businesses (CSV)":
            await self._export_businesses_csv(session_factory, export_dir)
        elif choice == "Export businesses (JSON)":
            await self._export_businesses_json(session_factory, export_dir)
        elif choice == "Export research topics (Markdown)":
            await self._export_topics_markdown(session_factory, export_dir)
        elif choice == "Export everything (JSON)":
            await self._export_all_json(session_factory, export_dir)

        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    async def _export_businesses_csv(self, session_factory, export_dir: Path) -> None:
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Business).order_by(Business.total_score.desc().nullslast())
            )
            businesses = list(result.scalars().all())

        if not businesses:
            print_status(self.console, "No businesses to export.", "warning")
            return

        filename = export_dir / "businesses.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Name", "Category", "Address", "Phone", "Email", "Website",
                "Rating", "Reviews", "Score", "Status", "Source",
            ])
            for biz in businesses:
                writer.writerow([
                    biz.id, biz.name, biz.category, biz.address,
                    biz.phone, biz.email, biz.website,
                    biz.rating, biz.review_count, biz.total_score,
                    biz.status.value, biz.source,
                ])

        count = len(businesses)
        print_status(
            self.console,
            f"Exported {count} businesses to {filename}",
            "success"
        )

    async def _export_businesses_json(self, session_factory, export_dir: Path) -> None:
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Business).order_by(Business.total_score.desc().nullslast())
            )
            businesses = list(result.scalars().all())

        if not businesses:
            print_status(self.console, "No businesses to export.", "warning")
            return

        data = []
        for biz in businesses:
            data.append({
                "id": biz.id, "name": biz.name, "category": biz.category,
                "address": biz.address, "phone": biz.phone, "email": biz.email,
                "website": biz.website, "rating": biz.rating,
                "review_count": biz.review_count, "total_score": biz.total_score,
                "status": biz.status.value, "source": biz.source,
                "created_at": biz.created_at.isoformat() if biz.created_at else None,
            })

        filename = export_dir / "businesses.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        count = len(businesses)
        print_status(
            self.console,
            f"Exported {count} businesses to {filename}",
            "success"
        )

    async def _export_topics_markdown(self, session_factory, export_dir: Path) -> None:
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ResearchTopic).where(ResearchTopic.is_saved)
            )
            topics = list(result.scalars().all())

        if not topics:
            print_status(self.console, "No saved topics to export.", "warning")
            return

        lines = ["# Research Topics\n\n"]
        for i, topic in enumerate(topics, 1):
            questions = json.loads(topic.validation_questions) if topic.validation_questions else []
            lines.append(f"## {i}. {topic.title}\n\n")
            if topic.problem_statement:
                lines.append(f"### Problem Statement\n{topic.problem_statement}\n\n")
            if topic.proposed_system:
                lines.append(f"### Proposed System\n{topic.proposed_system}\n\n")
            if topic.target_users:
                lines.append(f"### Target Users\n{topic.target_users}\n\n")
            if topic.scope:
                lines.append(f"### Scope\n{topic.scope}\n\n")
            if questions:
                lines.append("### Validation Questions\n")
                for q in questions:
                    lines.append(f"- {q}")
                lines.append("\n\n")
            if topic.user_notes:
                lines.append(f"### Notes\n{topic.user_notes}\n\n")
            lines.append("---\n\n")

        filename = export_dir / "research_topics.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print_status(self.console, f"Exported {len(topics)} topics to {filename}", "success")

    async def _export_all_json(self, session_factory, export_dir: Path) -> None:
        async with session_factory() as session:
            from sqlalchemy import select

            businesses = list((await session.execute(select(Business))).scalars().all())
            analyses = list((await session.execute(select(AIAnalysis))).scalars().all())
            list(
                (await session.execute(select(WebsiteAnalysis))).scalars().all()
            )
            q = select(ResearchOpportunity)
            opportunities = list((await session.execute(q)).scalars().all())
            topics = list((await session.execute(select(ResearchTopic))).scalars().all())
            outreach = list((await session.execute(select(Outreach))).scalars().all())

        from datetime import datetime, timezone
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "businesses": [
                {"id": b.id, "name": b.name, "category": b.category,
                 "address": b.address, "phone": b.phone, "email": b.email,
                 "website": b.website, "rating": b.rating,
                 "review_count": b.review_count, "total_score": b.total_score,
                 "status": b.status.value}
                for b in businesses
            ],
            "ai_analyses": [
                {"id": a.id, "business_id": a.business_id,
                 "operational_problems": a.operational_problems,
                 "research_relevance": a.research_relevance,
                 "model_used": a.model_used}
                for a in analyses
            ],
            "opportunities": [
                {"id": o.id, "business_id": o.business_id,
                 "title": o.title, "category": o.category,
                 "is_favorited": o.is_favorited}
                for o in opportunities
            ],
            "topics": [
                {"id": t.id, "business_id": t.business_id,
                 "title": t.title, "is_saved": t.is_saved,
                 "user_notes": t.user_notes}
                for t in topics
            ],
            "outreach": [
                {"id": o.id, "business_id": o.business_id,
                 "email_to": o.email_to, "status": o.status.value}
                for o in outreach
            ],
        }

        filename = export_dir / "full_export.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print_status(self.console, f"Full export saved to {filename}", "success")
        n_biz = len(businesses)
        n_ana = len(analyses)
        n_top = len(topics)
        n_out = len(outreach)
        summary = f"Businesses: {n_biz} | Analyses: {n_ana} | Topics: {n_top} | Outreach: {n_out}"
        print_status(self.console, summary, "info")
