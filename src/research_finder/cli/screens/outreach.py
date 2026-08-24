from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select

from research_finder.cli.components.confirm import confirm
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_select, ask_text
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import truncate
from research_finder.database.connection import get_session_factory
from research_finder.database.models import Business as BusinessModel
from research_finder.database.models import Outreach, OutreachStatus
from research_finder.database.outreach_repository import OutreachRepository
from research_finder.services.email_templates import generate_email

STATUS_COLORS = {
    OutreachStatus.NOT_CONTACTED: "dim",
    OutreachStatus.DRAFT: "yellow",
    OutreachStatus.READY: "cyan",
    OutreachStatus.SENT: "green",
    OutreachStatus.DELIVERED: "green",
    OutreachStatus.REPLIED: "blue",
    OutreachStatus.INTERESTED: "bold green",
    OutreachStatus.DECLINED: "red",
    OutreachStatus.NO_RESPONSE: "yellow",
    OutreachStatus.DO_NOT_CONTACT: "bold red",
}


class OutreachScreen:
    def __init__(self, console: Console) -> None:
        self.console = console
        self._session_factory = get_session_factory()

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Manage business outreach and email drafts")

        async with self._session_factory() as session:
            repo = OutreachRepository(session)
            outreach_list = await repo.get_all()

        if outreach_list:
            self._show_table(outreach_list)

        await self._handle_actions(outreach_list)
        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    def _show_table(self, outreach_list: list[Outreach]) -> None:
        table = Table(
            title=f"Outreach History ({len(outreach_list)})",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("To", max_width=25)
        table.add_column("Subject", max_width=30)
        table.add_column("Status", justify="center", width=12)

        for i, item in enumerate(outreach_list[:15], 1):
            color = STATUS_COLORS.get(item.status, "white")
            table.add_row(
                str(i),
                truncate(item.email_to, 23),
                truncate(item.email_subject, 28),
                f"[{color}]{item.status.value}[/{color}]"
            )

        self.console.print(table)
        self.console.print()

    async def _handle_actions(self, outreach_list: list[Outreach]) -> None:
        choice = await ask_select(
            "What would you like to do?",
            [
                "Create new outreach draft",
                "View outreach details",
                "Edit draft",
                "Send draft",
                "Mark as do-not-contact",
                "Back to menu",
            ],
            
        )

        if choice == "Create new outreach draft":
            await self._create_draft()
        elif choice == "View outreach details":
            await self._view_detail(outreach_list)
        elif choice == "Edit draft":
            await self._edit_draft(outreach_list)
        elif choice == "Send draft":
            await self._send_draft(outreach_list)
        elif choice == "Mark as do-not-contact":
            await self._mark_do_not_contact(outreach_list)

    async def _create_draft(self) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(BusinessModel).where(
                    BusinessModel.email.isnot(None), BusinessModel.email != ""
                )
            )
            businesses = list(result.scalars().all())

        if not businesses:
            print_status(self.console, "No businesses with email addresses found.", "warning")
            return

        table = Table(title="Select Business", border_style="dim")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold", max_width=30)
        table.add_column("Email", max_width=25)
        table.add_column("Category", max_width=15)

        for i, biz in enumerate(businesses, 1):
            table.add_row(
                str(i),
                truncate(biz.name, 28),
                biz.email or "-",
                truncate(biz.category, 13)
            )

        self.console.print(table)
        nums = await ask_text("Enter business number:")
        if not nums:
            return

        try:
            idx = int(nums) - 1
            if 0 <= idx < len(businesses):
                biz = businesses[idx]
                email = biz.email
                category = biz.category or "your industry"
                if not confirm(self.console, f"Draft email to {biz.name} <{email}>?"):
                    return
                subject, body = generate_email(biz.name, category)
                self.console.print(Panel(
                    f"[bold]To:[/bold] {email}\n[bold]Subject:[/bold] {subject}\n\n{body}",
                    title="Email Preview",
                    border_style="cyan"
                ))
                edit = confirm(self.console, "Edit before saving?")
                if edit:
                    new_subject = await ask_text("Subject (empty to keep):")
                    if new_subject:
                        subject = new_subject
                    new_body = await ask_text("Body (empty to keep):")
                    if new_body:
                        body = new_body
                if confirm(self.console, "Save as draft?"):
                    async with self._session_factory() as session:
                        repo = OutreachRepository(session)
                        await repo.save({
                            "business_id": biz.id,
                            "email_to": email,
                            "email_subject": subject,
                            "email_body": body,
                            "status": "draft",
                        })
                    print_status(self.console, "Draft saved!", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _view_detail(self, outreach_list: list[Outreach]) -> None:
        nums = await ask_text("Enter outreach number:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(outreach_list):
                item = outreach_list[idx]
                self.console.print()
                self.console.print(Panel(
                    f"[bold]To:[/bold] {item.email_to}\n"
                    f"[bold]Subject:[/bold] {item.email_subject}\n"
                    f"[bold]Status:[/bold] {item.status.value}\n"
                    f"[bold]Business:[/bold] {item.business_id}\n"
                    f"[bold]Created:[/bold] {item.created_at}\n"
                    f"[bold]Sent:[/bold] {item.sent_at or 'Not sent'}\n\n"
                    f"[bold]Body:[/bold]\n{item.email_body}",
                    title="Outreach Details",
                    border_style="cyan"
                ))
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _edit_draft(self, outreach_list: list[Outreach]) -> None:
        nums = await ask_text("Enter draft number to edit:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(outreach_list):
                item = outreach_list[idx]
                if item.status not in (OutreachStatus.DRAFT, OutreachStatus.NOT_CONTACTED):
                    print_status(self.console, "Can only edit drafts.", "error")
                    return
                self.console.print(f"  [dim]Current subject: {item.email_subject}[/dim]")
                new_subject = await ask_text("New subject (empty to keep):")
                self.console.print(f"  [dim]Current body preview: {item.email_body[:100]}...[/dim]")
                new_body = await ask_text("New body (empty to keep):")
                updates = {}
                if new_subject:
                    updates["email_subject"] = new_subject
                if new_body:
                    updates["email_body"] = new_body
                if updates:
                    async with self._session_factory() as session:
                        repo = OutreachRepository(session)
                        await repo.update(item.id, updates)
                    print_status(self.console, "Draft updated!", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _send_draft(self, outreach_list: list[Outreach]) -> None:
        nums = await ask_text("Enter draft number to send:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(outreach_list):
                item = outreach_list[idx]
                if item.status not in (OutreachStatus.DRAFT, OutreachStatus.READY):
                    print_status(self.console, "Can only send drafts.", "error")
                    return
                self.console.print(Panel(
                    f"[bold]To:[/bold] {item.email_to}\n"
                    f"[bold]Subject:[/bold] {item.email_subject}\n\n"
                    f"{item.email_body[:500]}{'...' if len(item.email_body) > 500 else ''}",
                    title="Email Preview",
                    border_style="cyan"
                ))
                if not confirm(self.console, "SEND this email?", default=False):
                    print_status(self.console, "Send cancelled.", "warning")
                    return
                from research_finder.providers.email import ConsoleEmailProvider
                provider = ConsoleEmailProvider()
                success = await provider.send_email(
                    item.email_to, item.email_subject, item.email_body
                )
                if success:
                    async with self._session_factory() as session:
                        repo = OutreachRepository(session)
                        await repo.update_status(item.id, OutreachStatus.SENT)
                    print_status(self.console, "Email sent!", "success")
                else:
                    print_status(self.console, "Failed to send email.", "error")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")

    async def _mark_do_not_contact(self, outreach_list: list[Outreach]) -> None:
        nums = await ask_text("Enter outreach number:")
        if not nums:
            return
        try:
            idx = int(nums) - 1
            if 0 <= idx < len(outreach_list):
                item = outreach_list[idx]
                if confirm(self.console, f"Mark {item.email_to} as DO NOT CONTACT?"):
                    async with self._session_factory() as session:
                        repo = OutreachRepository(session)
                        await repo.update_status(item.id, OutreachStatus.DO_NOT_CONTACT)
                    print_status(self.console, "Marked as do-not-contact.", "success")
        except (ValueError, IndexError):
            print_status(self.console, "Invalid selection.", "error")
