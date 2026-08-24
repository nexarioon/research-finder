from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from research_finder.application.ranking_service import CandidateRankingService
from research_finder.cli.components.empty_state import empty_state
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_select, ask_text
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import truncate
from research_finder.domain.models import Business


class AnalyzeScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Score and rank business candidates")

        service = CandidateRankingService()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Scoring businesses...", total=None)
            scored = await service.score_all_unscored()
            progress.update(task, completed=True, description=f"Scored {scored} new businesses")

        min_score = await self._get_min_score()
        candidates = await service.get_ranked_candidates(min_score=min_score, limit=30)

        if not candidates:
            empty_state(
                self.console,
                "No scored candidates found.",
                hint="Discover and save businesses first."
            )
            print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])
            return

        selected = await self._show_ranked_table(candidates)

        if selected:
            count = await service.select_top_candidates(selected)
            print_status(self.console, f"Saved {count} candidates for further analysis.", "success")

        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    async def _get_min_score(self) -> float:
        self.console.print()
        self.console.print("  [bold]Score Filter[/bold]")
        self.console.print()

        choice = await ask_select(
            "Minimum score threshold:",
            [
                "Show all scored (0+)",
                "Show good candidates (40+)",
                "Show strong candidates (55+)",
                "Show top candidates (70+)",
            ],
            
        )

        score_map = {
            "Show all scored (0+)": 0,
            "Show good candidates (40+)": 40,
            "Show strong candidates (55+)": 55,
            "Show top candidates (70+)": 70,
        }
        return float(score_map.get(choice, 0) if choice else 0)

    async def _show_ranked_table(self, candidates: list[tuple[Business, dict]]) -> list[int]:
        table = Table(
            title=f"Ranked Candidates (top {len(candidates)})",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold", max_width=22)
        table.add_column("Category", max_width=14)
        table.add_column("Score", justify="center", width=5)
        table.add_column("Size", justify="center", width=4)
        table.add_column("Online", justify="center", width=5)
        table.add_column("Cust", justify="center", width=4)
        table.add_column("Complex", justify="center", width=5)
        table.add_column("Access", justify="center", width=5)
        table.add_column("Contact", justify="center", width=5)

        for i, (biz, breakdown) in enumerate(candidates, 1):
            score = biz.total_score or 0
            score_style = "green" if score >= 60 else "yellow" if score >= 40 else "red"
            table.add_row(
                str(i),
                truncate(biz.name, 20),
                truncate(biz.category, 12),
                f"[{score_style}]{score:.0f}[/{score_style}]",
                f"{breakdown.get(chr(39) + 'business_size' + chr(39), 0):.0f}",
                f"{breakdown.get(chr(39) + 'online_presence' + chr(39), 0):.0f}",
                f"{breakdown.get(chr(39) + 'customer_signal' + chr(39), 0):.0f}",
                f"{breakdown.get(chr(39) + 'operational_complexity' + chr(39), 0):.0f}",
                f"{breakdown.get(chr(39) + 'research_accessibility' + chr(39), 0):.0f}",
                f"{breakdown.get(chr(39) + 'contact_availability' + chr(39), 0):.0f}"
            )

        self.console.print(table)
        self.console.print()

        choice = await ask_select(
            "What would you like to do?",
            [
                "Select candidates to save for AI analysis",
                "Audit websites for candidates",
                "Show score details for a candidate",
                "Continue without saving",
            ],
            
        )

        if choice == "Select candidates to save for AI analysis":
            return await self._select_candidates(candidates)
        elif choice == "Audit websites for candidates":
            from research_finder.cli.screens.website_audit import WebsiteAuditScreen
            await WebsiteAuditScreen(self.console).run()
            return []
        elif choice == "Show score details for a candidate":
            await self._show_detail(candidates)
            return []
        return []

    async def _select_candidates(self, candidates: list[tuple[Business, dict]]) -> list[int]:
        nums = await ask_text("Enter candidate numbers (comma-separated):")
        if not nums:
            return []
        selected_ids = []
        for n in nums.split(","):
            try:
                idx = int(n.strip()) - 1
                if 0 <= idx < len(candidates):
                    biz, _ = candidates[idx]
                    if biz.id:
                        selected_ids.append(biz.id)
            except ValueError:
                pass
        return selected_ids

    async def _show_detail(self, candidates: list[tuple[Business, dict]]) -> None:
        nums = await ask_text("Enter candidate number to view:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(candidates):
                biz, breakdown = candidates[idx]
                from rich.panel import Panel
                score_text = f"{biz.total_score:.0f}" if biz.total_score else "-"
                self.console.print()
                self.console.print(Panel(
                    f"[bold]{biz.name}[/bold]\n\n"
                    f"Category:  {biz.category or chr(45)}\n"
                    f"Address:   {biz.address or chr(45)}\n"
                    f"Phone:     {biz.phone or chr(45)}\n"
                    f"Email:     {biz.email or chr(45)}\n"
                    f"Website:   {biz.website or chr(45)}\n"
                    f"Rating:    {biz.rating or chr(45)}\n"
                    f"Reviews:   {biz.review_count or chr(45)}\n"
                    f"Score:     {score_text}",
                    title="Candidate Details",
                    border_style="cyan"
                ))
                if breakdown:
                    self.console.print("\n[bold]Score Breakdown:[/bold]")
                    for key, val in breakdown.items():
                        if key != "total":
                            self.console.print(f"  {key}: {val:.0f}")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")
