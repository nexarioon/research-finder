from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class WebsiteAnalysisResult:
    url: str
    title: str | None = None
    meta_description: str | None = None
    services: list[str] = field(default_factory=list)
    contact_details: dict[str, str] = field(default_factory=dict)
    has_forms: bool = False
    has_booking: bool = False
    has_ecommerce: bool = False
    has_customer_portal: bool = False
    social_links: list[str] = field(default_factory=list)
    tech_indicators: list[str] = field(default_factory=list)
    error: str | None = None
    data_hash: str | None = None


SOCIAL_DOMAINS = [
    "facebook.com", "fb.com", "twitter.com", "x.com",
    "instagram.com", "linkedin.com", "youtube.com",
    "tiktok.com", "wa.me", "whatsapp.com", "t.me", "telegram.org",
]

BOOKING_KEYWORDS = ["booking", "reservation", "appoint", "schedule", "jadwal", "reservasi"]
ECOMMERCE_KEYWORDS = ["cart", "checkout", "add to cart", "beli", "purchase", "shop", "buy now"]
PORTAL_KEYWORDS = ["login", "sign in", "register", "daftar", "my account", "dashboard", "portal"]

TECH_PATTERNS = {
    "WordPress": [r"wp-content", r"wp-includes"],
    "Laravel": [r"laravel", r"csrf-token"],
    "Next.js": [r"__next", r"_next/static"],
    "React": [r"react", r"__react"],
    "Vue.js": [r"vue\.js", r"__vue__"],
    "Bootstrap": [r"bootstrap"],
    "Tailwind CSS": [r"tailwindcss", r"tailwind"],
    "jQuery": [r"jquery"],
    "Google Analytics": [r"google-analytics", r"gtag"],
    "Google Tag Manager": [r"googletagmanager"],
    "Facebook Pixel": [r"fbq\(", r"facebook\.net/en_US/fbevents"],
    "Stripe": [r"stripe\.com"],
    "Midtrans": [r"midtrans"],
    "Xendit": [r"xendit"],
}


class WebsiteAnalyzer:
    def __init__(self) -> None:
        self._cache: dict[str, WebsiteAnalysisResult] = {}
        self._last_request_time = 0.0
        self._min_interval = 2.0

    def _cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    async def _rate_limit(self) -> None:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            import asyncio
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    async def analyze(self, url: str) -> WebsiteAnalysisResult:
        cache_key = self._cache_key(url)
        if cache_key in self._cache:
            return self._cache[cache_key]

        await self._rate_limit()
        result = WebsiteAnalysisResult(url=url)

        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "ResearchFinder/0.1 (research analysis)"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    result.error = f"Not HTML: {content_type}"
                    return result

                html = response.text
                result.data_hash = hashlib.sha256(html.encode()).hexdigest()
                soup = BeautifulSoup(html, "lxml")

                result.title = self._extract_title(soup)
                result.meta_description = self._extract_meta_description(soup)
                result.services = self._extract_services(soup)
                result.contact_details = self._extract_contacts(soup)
                result.has_forms = self._detect_forms(soup)
                result.has_booking = self._detect_booking(soup)
                result.has_ecommerce = self._detect_ecommerce(soup)
                result.has_customer_portal = self._detect_portal(soup)
                result.social_links = self._extract_social_links(soup)
                result.tech_indicators = self._detect_tech(html)

        except httpx.HTTPStatusError as e:
            result.error = f"HTTP {e.response.status_code}"
        except httpx.RequestError as e:
            result.error = f"Network error: {type(e).__name__}"
        except Exception as e:
            result.error = f"Analysis error: {type(e).__name__}"

        self._cache[cache_key] = result
        return result

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else None

    def _extract_meta_description(self, soup: BeautifulSoup) -> str | None:
        tag = soup.find("meta", attrs={"name": "description"})
        if tag:
            return tag.get("content", "").strip() or None
        tag = soup.find("meta", attrs={"property": "og:description"})
        if tag:
            return tag.get("content", "").strip() or None
        return None

    def _extract_services(self, soup: BeautifulSoup) -> list[str]:
        services: list[str] = []
        nav = soup.find("nav")
        if nav:
            for link in nav.find_all("a"):
                text = link.get_text(strip=True)
                if text and len(text) < 50:
                    services.append(text)
        for h in soup.find_all(["h1", "h2", "h3"])[:10]:
            text = h.get_text(strip=True)
            if text and len(text) < 80 and text not in services:
                services.append(text)
        return services[:20]

    def _extract_contacts(self, soup: BeautifulSoup) -> dict[str, str]:
        contacts: dict[str, str] = {}
        text = soup.get_text()

        phone = re.search(r'(?:\+62|62|0)\d{9,13}', text)
        if phone:
            contacts["phone"] = phone.group()

        email = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        if email:
            contacts["email"] = email.group()

        return contacts

    def _detect_forms(self, soup: BeautifulSoup) -> bool:
        return len(soup.find_all("form")) > 0

    def _detect_booking(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text().lower()
        return any(kw in text for kw in BOOKING_KEYWORDS)

    def _detect_ecommerce(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text().lower()
        return any(kw in text for kw in ECOMMERCE_KEYWORDS)

    def _detect_portal(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text().lower()
        return any(kw in text for kw in PORTAL_KEYWORDS)

    def _extract_social_links(self, soup: BeautifulSoup) -> list[str]:
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(domain in href for domain in SOCIAL_DOMAINS):
                if href not in links:
                    links.append(href)
        return links[:10]

    def _detect_tech(self, html: str) -> list[str]:
        found: list[str] = []
        for tech, patterns in TECH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    found.append(tech)
                    break
        return found
