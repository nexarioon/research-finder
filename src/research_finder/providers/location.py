from __future__ import annotations

import logging

from research_finder.domain.models import LocationQuery

logger = logging.getLogger(__name__)


async def get_current_location() -> LocationQuery | None:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://ip-api.com/json")
            response.raise_for_status()
            data = response.json()

            lat = data.get("lat")
            lon = data.get("lon")
            city = data.get("city", "")

            if lat and lon:
                logger.info("Detected location: %s (%.4f, %.4f)", city, lat, lon)
                return LocationQuery(
                    latitude=float(lat),
                    longitude=float(lon),
                    address=city,
                )
    except Exception as e:
        logger.warning("Could not detect location: %s", e)

    return None


async def geocode_address(address: str) -> LocationQuery | None:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": address, "format": "json", "limit": 1},
                headers={"User-Agent": "ResearchFinder/0.1"},
            )
            response.raise_for_status()
            results = response.json()

            if results:
                r = results[0]
                lat = float(r["lat"])
                lon = float(r["lon"])
                display = r.get("display_name", address)
                logger.info("Geocoded '%s' to (%.4f, %.4f)", address, lat, lon)
                return LocationQuery(
                    latitude=lat,
                    longitude=lon,
                    address=display,
                )
    except Exception as e:
        logger.error("Geocoding failed for '%s': %s", address, e)

    return None


async def reverse_geocode(lat: float, lon: float) -> str | None:
    """Convert coordinates to a human-readable address using Nominatim reverse geocoding."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "zoom": 14,
                    "addressdetails": 1,
                },
                headers={"User-Agent": "ResearchFinder/0.1"},
            )
            response.raise_for_status()
            data = response.json()

            if "address" in data:
                addr = data["address"]
                # Build a readable address from components
                parts = []
                for key in [
                    "village", "suburb", "neighbourhood",
                    "city_district", "city", "town",
                    "county", "state",
                ]:
                    if key in addr and addr[key] not in parts:
                        parts.append(addr[key])

                if parts:
                    result = ", ".join(parts)
                    logger.info("Reverse geocoded (%.4f, %.4f) to '%s'", lat, lon, result)
                    return result

            # Fallback to display_name
            display = data.get("display_name")
            if display:
                logger.info("Reverse geocoded (%.4f, %.4f) to '%s'", lat, lon, display)
                return display

    except Exception as e:
        logger.error("Reverse geocoding failed for (%.4f, %.4f): %s", lat, lon, e)

    return None


def parse_maps_link(url_or_text: str) -> dict[str, Any]:
    """Parse Google Maps URL or text link to extract coordinates and place name."""
    import re
    from urllib.parse import unquote

    result: dict[str, Any] = {
        "latitude": None,
        "longitude": None,
        "name": None,
        "address": None,
    }

    if not url_or_text:
        return result

    # 1. Extract coordinates pattern @-6.12345,106.12345 or ll=-6.12345,106.12345 or q=-6.12345,106.12345
    coord_match = re.search(r'[@?&](?:ll|q|center)=?(-?\d+\.\d+),(-?\d+\.\d+)', url_or_text)
    if not coord_match:
        coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url_or_text)

    if coord_match:
        try:
            result["latitude"] = float(coord_match.group(1))
            result["longitude"] = float(coord_match.group(2))
        except ValueError:
            pass

    # 2. Extract place name pattern /place/Nama+Bisnis/ or /place/Nama%20Bisnis/
    place_match = re.search(r'/place/([^/@?]+)', url_or_text)
    if place_match:
        raw_name = place_match.group(1).replace("+", " ")
        cleaned_name = unquote(raw_name).strip()
        if cleaned_name and not cleaned_name.startswith("http"):
            result["name"] = cleaned_name

    return result
