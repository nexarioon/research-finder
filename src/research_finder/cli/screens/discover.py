from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from research_finder.application.discovery_service import DiscoveryService
from research_finder.cli.components.empty_state import empty_state
from research_finder.cli.components.header import print_header
from research_finder.cli.components.prompts import ask_checkbox, ask_select, ask_text
from research_finder.cli.components.shortcuts import print_shortcuts
from research_finder.cli.components.status import print_status
from research_finder.cli.utils import truncate
from research_finder.domain.models import Business, DiscoveryFilters, LocationQuery
from research_finder.providers.location import geocode_address, get_current_location
from research_finder.providers.nominatim import NominatimProvider


class DiscoverScreen:
    def __init__(self, console: Console) -> None:
        self.console = console

    async def run(self) -> None:
        self.console.clear()
        print_header(self.console, "Search for local businesses using OpenStreetMap")

        location = await self._select_location()
        if not location:
            empty_state(self.console, "Could not determine location.")
            return

        radius = await self._select_radius()
        filters = await self._select_filters()
        categories = await self._select_categories(location)

        addr = location.address or f"({location.latitude:.4f}, {location.longitude:.4f})"
        self.console.print(f"  [dim]Near: {addr}[/dim]")
        cats = ", ".join(categories) if categories else "All"
        self.console.print(f"  [dim]Radius: {radius} km | Categories: {cats}[/dim]")
        self.console.print()

        provider = NominatimProvider()
        service = DiscoveryService(provider)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Discovering businesses...", total=None)
            location.radius_km = radius
            businesses = await service.discover_businesses(location, filters, categories or None)
            progress.update(task, completed=True, description=f"Found {len(businesses)} businesses")

        if not businesses:
            empty_state(
                self.console,
                "No businesses found with current filters.",
                hint="Try adjusting your search radius or filters."
            )
            return

        selected = await self._show_results(businesses)

        if selected:
            self.console.print(f"  [dim]Saving {len(selected)} businesses...[/dim]")
            saved = await service.save_businesses(selected)
            print_status(self.console, f"Saved {len(saved)} new businesses!", "success")

        print_shortcuts(self.console, [("Esc", "Back"), ("q", "Quit")])

    async def _select_location(self) -> LocationQuery | None:
        self.console.print("  [bold]Location Selection[/bold]")
        self.console.print()

        choice = await ask_select(
            "How would you like to set the location?",
            [
                "Auto-detect from IP",
                "Enter address",
                "Enter coordinates",
            ],
            
        )

        if choice is None:
            return None

        if choice == "Auto-detect from IP":
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Detecting location...", total=None)
                location = await get_current_location()
                progress.update(task, completed=True)
            if location:
                print_status(self.console, f"Detected: {location.address}", "success")
            return location

        elif choice == "Enter address":
            address = await ask_text("Enter address:")
            if not address:
                return None
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Geocoding...", total=None)
                location = await geocode_address(address)
                progress.update(task, completed=True)
            if location:
                print_status(self.console, f"Found: {location.address}", "success")
            return location

        elif choice == "Enter coordinates":
            try:
                lat_str = await ask_text("Latitude:")
                lon_str = await ask_text("Longitude:")
                if not lat_str or not lon_str:
                    return None
                return LocationQuery(latitude=float(lat_str), longitude=float(lon_str))
            except ValueError:
                print_status(self.console, "Invalid coordinates.", "error")
                return None

        return None

    async def _select_radius(self) -> float:
        self.console.print()
        self.console.print("  [bold]Search Radius[/bold]")
        self.console.print()

        choice = await ask_select(
            "Select search radius:",
            [
                "1 km  (very close)",
                "3 km  (nearby)",
                "5 km  (default)",
                "10 km (wide area)",
                "20 km (city-wide)",
            ],
            default="5 km  (default)",
            
        )

        radius_map = {
            "1 km  (very close)": 1.0,
            "3 km  (nearby)": 3.0,
            "5 km  (default)": 5.0,
            "10 km (wide area)": 10.0,
            "20 km (city-wide)": 20.0,
        }
        return radius_map.get(choice, 5.0) if choice else 5.0

    async def _select_filters(self) -> DiscoveryFilters:
        filters = DiscoveryFilters()
        self.console.print()
        self.console.print("  [bold]Quick Filters[/bold]")
        self.console.print()

        choice = await ask_select(
            "Select filter preset:",
            [
                "Default (recommended)",
                "Strict (local only, good ratings)",
                "Loose (include everything)",
            ],
            
        )

        if choice == "Strict (local only, good ratings)":
            filters.prefer_online_presence = True
            filters.prefer_local_business = True
        elif choice == "Loose (include everything)":
            filters.prefer_online_presence = None
            filters.prefer_local_business = None

        return filters

    async def _select_categories(self, location: LocationQuery) -> list[str]:
        provider = NominatimProvider()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Loading categories...", total=None)
            categories = await provider.get_categories(location)
            progress.update(task, completed=True)

        if not categories:
            return []

        self.console.print()
        self.console.print("  [bold]Categories[/bold]")
        self.console.print()

        choices = ["All categories"] + categories
        selected = await ask_checkbox(
            "Select categories (space to toggle, enter to confirm):",
            choices,
            
        )

        if not selected or "All categories" in selected:
            return []

        return [c for c in selected if c != "All categories"]

    async def _show_results(self, businesses: list[Business]) -> list[Business]:
        self.console.print()

        table = Table(
            title=f"Found {len(businesses)} Businesses",
            show_lines=True,
            border_style="dim"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold", max_width=30)
        table.add_column("Category", max_width=18)
        table.add_column("Address", max_width=25)
        table.add_column("Contact", max_width=20)

        for i, biz in enumerate(businesses, 1):
            contact = biz.phone or biz.email or "-"
            table.add_row(
                str(i),
                truncate(biz.name, 28),
                truncate(biz.category, 16),
                truncate(biz.address, 23),
                truncate(contact, 18)
            )

        self.console.print(table)
        self.console.print()

        choice = await ask_select(
            "What would you like to do?",
            [
                "Save ALL businesses",
                "Select specific businesses to save",
                "Don't save anything",
            ],
            
        )

        if choice == "Save ALL businesses":
            return businesses
        elif choice == "Select specific businesses to save":
            nums = await ask_text("Enter business numbers (comma-separated):")
            if not nums:
                return []
            selected = []
            for n in nums.split(","):
                try:
                    idx = int(n.strip()) - 1
                    if 0 <= idx < len(businesses):
                        selected.append(businesses[idx])
                except ValueError:
                    pass
            return selected

        return []
