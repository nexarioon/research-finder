from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select

from research_finder.cli.components.empty_state import empty_state
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_select, ask_text
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import truncate
from research_finder.database.connection import get_session_factory
from research_finder.database.models import AIAnalysis, ResearchOpportunity
from research_finder.database.opportunity_repository import OpportunityRepository, TopicRepository


class OpportunitiesScreen:
    def __init__(self, console: Console) -> None:
        self.console = console
        self._session_factory = get_session_factory()

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Browse research opportunities from AI analysis")

        async with self._session_factory() as session:
            repo = OpportunityRepository(session)
            opportunities = await repo.get_all()

        if not opportunities:
            empty_state(
                self.console,
                "No research opportunities found.",
                hint="Run AI analysis on businesses to generate opportunities."
            )
            print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
            return

        self._show_table(opportunities)
        await self._handle_actions(opportunities)
        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    def _show_table(self, opportunities: list[ResearchOpportunity]) -> None:
        table = Table(
            title=f"Research Opportunities ({len(opportunities)})",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", style="bold", max_width=35)
        table.add_column("Category", max_width=15)
        table.add_column("Fav", justify="center", width=4)

        for i, opp in enumerate(opportunities, 1):
            fav = "[yellow]\u2605[/yellow]" if opp.is_favorited else " "
            table.add_row(
                str(i),
                truncate(opp.title, 33),
                truncate(opp.category, 13) if opp.category else "-",
                fav
            )

        self.console.print(table)
        self.console.print()

    async def _handle_actions(self, opportunities: list[ResearchOpportunity]) -> None:
        choice = await ask_select(
            "What would you like to do?",
            [
                "View opportunity details",
                "Toggle favorite",
                "Generate topics from opportunity",
                "Back to menu",
            ],
            
        )

        if choice == "View opportunity details":
            await self._view_detail(opportunities)
        elif choice == "Toggle favorite":
            await self._toggle_favorite(opportunities)
        elif choice == "Generate topics from opportunity":
            await self._generate_topics(opportunities)

    async def _view_detail(self, opportunities: list[ResearchOpportunity]) -> None:
        nums = await ask_text("Enter opportunity number:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(opportunities):
                opp = opportunities[idx]
                self.console.print()
                self.console.print(Panel(
                    f"[bold]{opp.title}[/bold]\n\n"
                    f"Category:   {opp.category or 'N/A'}\n"
                    f"Business:   {opp.business_id}\n"
                    f"Favorite:   {'Yes' if opp.is_favorited else 'No'}\n\n"
                    f"[bold]Description:[/bold]\n{opp.description or 'No description'}",
                    title="Opportunity Details",
                    border_style="cyan"
                ))
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _toggle_favorite(self, opportunities: list[ResearchOpportunity]) -> None:
        nums = await ask_text("Enter opportunity number to toggle favorite:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(opportunities):
                opp = opportunities[idx]
                async with self._session_factory() as session:
                    repo = OpportunityRepository(session)
                    await repo.toggle_favorite(opp.id)
                print_status(self.console, f"Toggled favorite: {opp.title}", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _generate_topics(self, opportunities: list[ResearchOpportunity]) -> None:
        nums = await ask_text("Enter opportunity number to generate topics:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(opportunities):
                opp = opportunities[idx]
                async with self._session_factory() as session:
                    result = await session.execute(
                        select(AIAnalysis).where(AIAnalysis.business_id == opp.business_id)
                    )
                    analysis = result.scalar_one_or_none()
                    if not analysis:
                        msg = "No AI analysis found for this business."
                        print_status(self.console, msg, "warning")
                        return
                    t_data = analysis.research_topics
                    q_data = analysis.validation_questions
                    topics = json.loads(t_data) if t_data else []
                    questions = json.loads(q_data) if q_data else []
                    topic_repo = TopicRepository(session)
                    created = 0
                    for topic_title in topics:
                        await topic_repo.save_topic({
                            "business_id": opp.business_id,
                            "ai_analysis_id": analysis.id,
                            "opportunity_id": opp.id,
                            "title": topic_title,
                            "problem_statement": analysis.research_relevance,
                            "validation_questions": questions,
                            "is_saved": False,
                        })
                        created += 1
                    print_status(self.console, f"Generated {created} topic(s).", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")
