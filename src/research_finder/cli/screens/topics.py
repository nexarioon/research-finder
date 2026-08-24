from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from research_finder.cli.components.empty_state import empty_state
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_select, ask_text
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import truncate
from research_finder.database.connection import get_session_factory
from research_finder.database.models import ResearchTopic
from research_finder.database.opportunity_repository import TopicRepository


class TopicsScreen:
    def __init__(self, console: Console) -> None:
        self.console = console
        self._session_factory = get_session_factory()

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Manage research topic candidates")

        async with self._session_factory() as session:
            repo = TopicRepository(session)
            topics = await repo.get_all()

        if not topics:
            empty_state(
                self.console,
                "No research topics found.",
                hint="Generate topics from AI analysis or opportunities."
            )
            print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
            return

        self._show_table(topics)
        await self._handle_actions(topics)
        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    def _show_table(self, topics: list[ResearchTopic]) -> None:
        table = Table(
            title=f"Research Topics ({len(topics)})",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", style="bold", max_width=38)
        table.add_column("Saved", justify="center", width=5)
        table.add_column("Notes", max_width=20)

        for i, topic in enumerate(topics, 1):
            saved = "[green]\u2605[/green]" if topic.is_saved else " "
            notes = truncate(topic.user_notes, 18) if topic.user_notes else "-"
            table.add_row(
                str(i),
                truncate(topic.title, 36),
                saved,
                notes
            )

        self.console.print(table)
        self.console.print()

    async def _handle_actions(self, topics: list[ResearchTopic]) -> None:
        choice = await ask_select(
            "What would you like to do?",
            [
                "View topic details",
                "Toggle save/unsave",
                "Edit topic notes",
                "Export saved topics to Markdown",
                "Back to menu",
            ],
            
        )

        if choice == "View topic details":
            await self._view_detail(topics)
        elif choice == "Toggle save/unsave":
            await self._toggle_save(topics)
        elif choice == "Edit topic notes":
            await self._edit_notes(topics)
        elif choice == "Export saved topics to Markdown":
            await self._export_topics(topics)

    async def _view_detail(self, topics: list[ResearchTopic]) -> None:
        nums = await ask_text("Enter topic number:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(topics):
                t = topics[idx]
                q_data = t.validation_questions
                questions = json.loads(q_data) if q_data else []
                q_lines = [f"  {i+1}. {q}" for i, q in enumerate(questions)]
                questions_text = "\n".join(q_lines) if q_lines else "  None"
                self.console.print()
                self.console.print(Panel(
                    f"[bold]{t.title}[/bold]\n\n"
                    f"[bold]Problem Statement:[/bold]\n{t.problem_statement or 'Not defined'}\n\n"
                    f"[bold]Proposed System:[/bold]\n{t.proposed_system or 'Not defined'}\n\n"
                    f"[bold]Target Users:[/bold]\n{t.target_users or 'Not defined'}\n\n"
                    f"[bold]Scope:[/bold]\n{t.scope or 'Not defined'}\n\n"
                    f"[bold]Validation Questions:[/bold]\n{questions_text}\n\n"
                    f"[bold]User Notes:[/bold]\n{t.user_notes or 'None'}\n\n"
                    f"Saved: {'Yes' if t.is_saved else 'No'}",
                    title="Topic Details",
                    border_style="cyan"
                ))
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _toggle_save(self, topics: list[ResearchTopic]) -> None:
        nums = await ask_text("Enter topic number to toggle save:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(topics):
                topic = topics[idx]
                async with self._session_factory() as session:
                    repo = TopicRepository(session)
                    await repo.toggle_save(topic.id)
                print_status(self.console, f"Toggled save: {topic.title}", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _edit_notes(self, topics: list[ResearchTopic]) -> None:
        nums = await ask_text("Enter topic number to edit notes:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(topics):
                topic = topics[idx]
                self.console.print(f"  [dim]Current notes: {topic.user_notes or 'None'}[/dim]")
                notes = await ask_text("Enter new notes (empty to cancel):")
                if notes:
                    async with self._session_factory() as session:
                        repo = TopicRepository(session)
                        await repo.update(topic.id, {"user_notes": notes})
                    print_status(self.console, "Notes updated!", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _export_topics(self, topics: list[ResearchTopic]) -> None:
        saved = [t for t in topics if t.is_saved]
        if not saved:
            print_status(self.console, "No saved topics to export.", "warning")
            return
        from pathlib import Path
        filename = await ask_text("Export filename (default: research_topics.md):")
        if not filename:
            filename = "research_topics.md"
        lines = ["# Research Topics\n", "Exported from Research Prospect Finder\n\n"]
        for i, topic in enumerate(saved, 1):
            questions = json.loads(topic.validation_questions) if topic.validation_questions else []
            lines.append(f"## {i}. {topic.title}\n\n")
            lines.append(f"**Business ID:** {topic.business_id}\n\n")
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
        Path(filename).write_text("".join(lines), encoding="utf-8")
        print_status(self.console, f"Exported {len(saved)} topics to {filename}", "success")
