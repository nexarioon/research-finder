from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass

import httpx

from research_finder.domain.models import Business, BusinessStatus, DiscoveryFilters, LocationQuery
from research_finder.providers.base import BusinessProvider

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org"

# Common amenity types mapped to categories (businesses only)
AMENITY_CATEGORIES = {
    "restaurant": "Food & Dining",
    "cafe": "Food & Dining",
    "bar": "Food & Dining",
    "pub": "Food & Dining",
    "fast_food": "Food & Dining",
    "bakery": "Food & Dining",
    "supermarket": "Retail",
    "convenience": "Retail",
    "clothes": "Retail",
    "shoes": "Retail",
    "electronics": "Retail",
    "furniture": "Retail",
    "hairdresser": "Health & Beauty",
    "beauty_salon": "Health & Beauty",
    "dentist": "Health & Beauty",
    "pharmacy": "Health & Beauty",
    "clinic": "Health & Beauty",
    "bank": "Financial Services",
    "bureau_de_change": "Financial Services",
    "hotel": "Hospitality",
    "motel": "Hospitality",
    "hostel": "Hospitality",
    "car_repair": "Automotive",
    "car_wash": "Automotive",
    "gym": "Sports & Fitness",
    "cinema": "Entertainment",
    "theatre": "Entertainment",
    "nightclub": "Entertainment",
    "computer": "Technology",
    "telecom": "Technology",
    "office": "Business Services",
    "coworking": "Business Services",
    "laundry": "Services",
    "cleaning": "Services",
    "repair": "Services",
    "travel_agency": "Business Services",
    "insurance": "Financial Services",
    "money_lender": "Financial Services",
    "marketplace": "Retail",
    "deli": "Food & Dining",
    "ice_cream": "Food & Dining",
    "coffee": "Food & Dining",
    "tea": "Food & Dining",
    "juice_bar": "Food & Dining",
    "bistro": "Food & Dining",
    "ramen": "Food & Dining",
    "noodle": "Food & Dining",
    "sushi": "Food & Dining",
    "pizza": "Food & Dining",
    "burger": "Food & Dining",
    "steakhouse": "Food & Dining",
    "seafood": "Food & Dining",
    "vegetarian": "Food & Dining",
    "vegan": "Food & Dining",
    "bakery": "Food & Dining",
    "butcher": "Food & Dining",
    "cheese": "Food & Dining",
    "chocolate": "Food & Dining",
    "confectionery": "Food & Dining",
    "diet": "Food & Dining",
    "farm": "Food & Dining",
    "food_court": "Food & Dining",
    "fuze_tea": "Food & Dining",
    "grill": "Food & Dining",
    "han BBQ": "Food & Dining",
    "korean_bbq": "Food & Dining",
    "organic": "Food & Dining",
    "pasta": "Food & Dining",
    "wok": "Food & Dining",
    "yogurt": "Food & Dining",
    "optician": "Health & Beauty",
    "hearing_aids": "Health & Beauty",
    "herbalist": "Health & Beauty",
    "alternative": "Health & Beauty",
    "psychotherapist": "Health & Beauty",
    "chiropractor": "Health & Beauty",
    "osteopath": "Health & Beauty",
    "physiotherapist": "Health & Beauty",
    "massage": "Health & Beauty",
    "tattoo": "Health & Beauty",
    "piercing": "Health & Beauty",
    "nail_salon": "Health & Beauty",
    "waxing": "Health & Beauty",
    "sauna": "Health & Beauty",
    "spa": "Health & Beauty",
    "solarium": "Health & Beauty",
    "veterinary": "Health & Beauty",
    "pet": "Health & Beauty",
    "pet_grooming": "Health & Beauty",
    "bicycle_rental": "Automotive",
    "car_sharing": "Automotive",
    "motorcycle": "Automotive",
    "motorcycle_repair": "Automotive",
    "truck": "Automotive",
    "bus": "Automotive",
    "taxi": "Automotive",
    "boat": "Automotive",
    "aircraft": "Automotive",
    "caravan": "Automotive",
    "motorboat": "Automotive",
    "yacht": "Automotive",
    "bicycle_parking": "Automotive",
    "bicycle_repair_station": "Automotive",
    "motorcycle_parking": "Automotive",
    "caravan_site": "Automotive",
    "charging_station": "Automotive",
    "parking_entrance": "Automotive",
    "parking_space": "Automotive",
    "parking": "Automotive",
    "bench": "Automotive",
    "shelter": "Automotive",
    "drinking_water": "Automotive",
    "fountain": "Automotive",
    "waste_basket": "Automotive",
    "recycling": "Automotive",
    "telephone": "Automotive",
    "post_office": "Logistics",
    "parcel_locker": "Logistics",
    "vending_machine": "Retail",
    "vending_machines": "Retail",
    " ATM": "Financial Services",
}

# Excluded amenity types (not businesses)
EXCLUDED_AMENITIES = {
    "school", "university", "college", "kindergarten", "library",
    "fuel", "hospital", "place_of_worship", "mosque", "church",
    "temple", "synagogue", "shrine", "monastery", "chapel",
    "police", "fire_station", "ambulance_station", "court",
    "government", "townhall", "community_centre", "social_facility",
    "shelter", "toilets", "drinking_water", "fountain",
    "bench", "waste_basket", "recycling", "telephone",
    "post_box", "parcel_locker", "vending_machine", "vending_machines",
    "parking", "parking_entrance", "parking_space", "bicycle_parking",
    "motorcycle_parking", "caravan_site", "charging_station",
    "bus_station", "taxi", "car_sharing", "bicycle_rental",
    "caravan", "motorcycle", "motorcycle_repair",
    "truck", "bus", "boat", "aircraft", "motorboat", "yacht",
    "bicycle_repair_station", "motorcycle_parking",
    "caravan_site", "charging_station", "parking_entrance",
    "parking_space", "parking", "bench", "shelter",
    "drinking_water", "fountain", "waste_basket", "recycling",
    "telephone", "post_office", "parcel_locker",
    "vending_machine", "vending_machines",
    "ATM",
}


@dataclass
class CacheEntry:
    data: list[Business]
    timestamp: float
    ttl: float = 3600.0  # 1 hour

    @property
    def is_valid(self) -> bool:
        return time.time() - self.timestamp < self.ttl


class NominatimProvider(BusinessProvider):
    def __init__(self) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._last_request_time = 0.0
        self._min_interval = 1.1  # Nominatim requires 1 req/sec

    def _make_cache_key(self, location: LocationQuery, filters: DiscoveryFilters, category: str | None) -> str:
        raw = json.dumps({
            "lat": location.latitude,
            "lon": location.longitude,
            "radius": location.radius_km,
            "min_rating": filters.min_rating,
            "min_reviews": filters.min_review_count,
            "category": category,
        }, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    async def _rate_limit(self) -> None:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    async def search_businesses(
        self,
        location: LocationQuery,
        filters: DiscoveryFilters,
        category: str | None = None,
    ) -> list[Business]:
        cache_key = self._make_cache_key(location, filters, category)
        cached = self._cache.get(cache_key)
        if cached and cached.is_valid:
            logger.info("Returning cached results for %s", cache_key[:8])
            return cached.data

        await self._rate_limit()

        radius_m = int(location.radius_km * 1000)
        amenity_filter = self._build_amenity_filter(category, filters)

        query = f"""
        [out:json][timeout:60];
        (
          node["amenity"]{amenity_filter}(around:{radius_m},{location.latitude},{location.longitude});
        );
        out body tags;
        """

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        OVERPASS_URL,
                        data={"data": query},
                        headers={"User-Agent": "ResearchFinder/0.1"},
                    )
                    if response.status_code == 429:
                        import asyncio as _aio
                        await _aio.sleep(5 * (attempt + 1))
                        continue
                    response.raise_for_status()
                    data = response.json()
                    break
            except httpx.HTTPStatusError as e:
                logger.error("Overpass API error (attempt %d): %s", attempt + 1, e.response.status_code)
                if attempt == 2:
                    return []
            except httpx.RequestError as e:
                logger.error("Network error (attempt %d): %s", attempt + 1, e)
                if attempt == 2:
                    return []

        businesses = self._parse_elements(data.get("elements", []))
        businesses = self._apply_filters(businesses, filters)

        self._cache[cache_key] = CacheEntry(data=businesses, timestamp=time.time())
        logger.info("Found %d businesses near (%.4f, %.4f)", len(businesses), location.latitude, location.longitude)

        return businesses

    async def get_categories(self, location: LocationQuery) -> list[str]:
        radius_m = int(location.radius_km * 1000)
        query = f"""
        [out:json][timeout:30];
        node["amenity"](around:{radius_m},{location.latitude},{location.longitude});
        out tags;
        """

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await self._rate_limit()
                response = await client.post(
                    OVERPASS_URL,
                    data={"data": query},
                    headers={"User-Agent": "ResearchFinder/0.1"},
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error("Failed to fetch categories: %s", e)
            return sorted(set(AMENITY_CATEGORIES.values()))

        amenity_types: set[str] = set()
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            amenity = tags.get("amenity", "")
            if amenity:
                amenity_types.add(amenity)

        categories: set[str] = set()
        for amenity in amenity_types:
            if amenity in AMENITY_CATEGORIES:
                categories.add(AMENITY_CATEGORIES[amenity])

        return sorted(categories) if categories else sorted(set(AMENITY_CATEGORIES.values()))

    async def get_business_details(self, external_id: str) -> Business | None:
        await self._rate_limit()
        query = f"""
        [out:json][timeout:15];
        node(id:{external_id});
        out body tags;
        """

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    OVERPASS_URL,
                    data={"data": query},
                    headers={"User-Agent": "ResearchFinder/0.1"},
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error("Failed to fetch business details: %s", e)
            return None

        elements = data.get("elements", [])
        if not elements:
            return None

        parsed = self._parse_elements(elements)
        return parsed[0] if parsed else None

    def _build_amenity_filter(self, category: str | None, filters: DiscoveryFilters) -> str:
        if not category:
            return ""

        amenity_types = [
            k for k, v in AMENITY_CATEGORIES.items() if v == category
        ]
        if not amenity_types:
            return ""

        if len(amenity_types) == 1:
            return f'["amenity"="{amenity_types[0]}"]'

        values = "|".join(amenity_types)
        return f'["amenity"~"^{values}$"]'

    def _parse_elements(self, elements: list[dict]) -> list[Business]:
        businesses: list[Business] = []

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "")
            if not name:
                continue

            amenity = tags.get("amenity", "")

            # Exclude non-business amenities
            if amenity in EXCLUDED_AMENITIES:
                continue

            # Exclude places with non-business names
            name_lower = name.lower()
            exclude_keywords = [
                "masjid", "mosque", "gereja", "church", "temple", "pura",
                "kuil", "vihara", "monastery", "shrine", "chapel",
                "sekolah", "school", "universitas", "university", "kampus",
                "sd ", "smp ", "sma ", "smk ", "tk ", "paud",
                "polsek", "polres", "polisi", "police", "kantor polisi",
                "koramil", "tni", "military", "militer",
                "puskesmas", "puskesmas kelurahan",
                "kantor lurah", "kantor camat", "kelurahan", "kecamatan",
                "rw ", "rt ", "rw.", "rt.",
                "pos ronda", "pos kamling", "pos security",
                "substation", "substasi",
                "substation pln", "pln",
                "subsektor", "subsek",
                "pom bensin", "spbu", "spbg", "spbkb",
                "atm ", "atm.",
                "bandara", "airport", "pelabuhan", "port",
                "stasiun", "station",
                "terminal",
                "museum", "monumen", "taman",
                "perpustakaan", "library",
                "gedung", "aula",
                "kantor", "office",
            ]

            for keyword in exclude_keywords:
                if keyword in name_lower:
                    break
            else:
                # Only add if no exclude keyword matched
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                category = AMENITY_CATEGORIES.get(amenity, "Other")

                website = tags.get("website") or tags.get("contact:website")
                phone = tags.get("phone") or tags.get("contact:phone")
                email = tags.get("email") or tags.get("contact:email")

                business = Business(
                    name=name,
                    address=tags.get("addr:street", ""),
                    phone=phone,
                    website=website,
                    email=email,
                    latitude=float(lat) if lat else None,
                    longitude=float(lon) if lon else None,
                    category=category,
                    rating=None,
                    review_count=None,
                    is_local_business=True,
                    is_franchise=None,
                    has_online_presence=bool(website),
                    status=BusinessStatus.DISCOVERED,
                    source="openstreetmap",
                    external_id=str(el.get("id", "")),
                )

                addr_parts = []
                if tags.get("addr:housenumber"):
                    addr_parts.append(tags["addr:housenumber"])
                if tags.get("addr:street"):
                    addr_parts.append(tags["addr:street"])
                if tags.get("addr:city"):
                    addr_parts.append(tags["addr:city"])
                if addr_parts:
                    business.address = ", ".join(addr_parts)

                businesses.append(business)

        return businesses

    def _apply_filters(self, businesses: list[Business], filters: DiscoveryFilters) -> list[Business]:
        result = []
        for biz in businesses:
            if filters.categories and biz.category not in filters.categories:
                continue
            if filters.prefer_online_presence is True and not biz.has_online_presence:
                continue
            if filters.prefer_online_presence is False and biz.has_online_presence:
                continue
            if filters.prefer_local_business is False and biz.is_local_business:
                continue
            result.append(biz)
        return result
