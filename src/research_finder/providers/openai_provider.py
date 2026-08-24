from __future__ import annotations

import json
import logging

import httpx

from research_finder.config.settings import get_settings
from research_finder.domain.models import AIAnalysisResult
from research_finder.providers.ai_base import AIProvider

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are a research analyst helping a university student find research/skripsi topics.

Analyze this business and provide research insights:

Business: {name}
Category: {category}
Address: {address}
Phone: {phone}
Website: {website}
Rating: {rating}
Reviews: {review_count}

{website_analysis}

Provide your analysis in this EXACT JSON format:
{{
    "operational_problems": "Describe potential operational problems this business might face (2-3 sentences). Only state things that can be reasonably inferred from the business type and public information. Clearly mark any assumptions.",
    "info_system_opportunities": "Describe information system opportunities (2-3 sentences). Focus on digital transformation possibilities.",
    "research_relevance": "Explain why this business could be a good research subject (2-3 sentences).",
    "research_topics": ["Topic 1 title", "Topic 2 title", "Topic 3 title", "Topic 4 title", "Topic 5 title"],
    "validation_questions": ["Question 1 to ask the business owner", "Question 2", "Question 3", "Question 4"]
}}

Important rules:
- Only state facts that can be verified from public information
- Mark assumptions clearly with [ASSUMPTION]
- Do not invent problems that cannot be reasonably inferred
- Focus on information systems and technology opportunities
- Provide exactly 3-5 research topics
- Provide exactly 4-5 validation questions"""


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self._settings = get_settings()

    async def is_available(self) -> bool:
        if not self._settings.ai_enabled:
            return False
        if not self._settings.ai_api_key:
            return False
        return True

    async def analyze_business(
        self,
        business_name: str,
        business_data: dict,
        website_data: dict | None = None,
    ) -> AIAnalysisResult:
        if not await self.is_available():
            return AIAnalysisResult(
                business_id=0,
                operational_problems="AI is disabled or not configured.",
                model_used="none",
            )

        website_analysis = ""
        if website_data:
            website_analysis = f"""Website Analysis:
Title: {website_data.get('title', 'N/A')}
Description: {website_data.get('meta_description', 'N/A')}
Services found: {', '.join(website_data.get('services', [])[:5]) or 'N/A'}
Has forms: {website_data.get('has_forms', False)}
Has booking: {website_data.get('has_booking', False)}
Has ecommerce: {website_data.get('has_ecommerce', False)}
Tech: {', '.join(website_data.get('tech_indicators', [])[:5]) or 'N/A'}
Social links: {len(website_data.get('social_links', []))} found"""
        else:
            website_analysis = "No website analysis available."

        prompt = ANALYSIS_PROMPT.format(
            name=business_name,
            category=business_data.get("category", "N/A"),
            address=business_data.get("address", "N/A"),
            phone=business_data.get("phone", "N/A"),
            website=business_data.get("website", "N/A"),
            rating=business_data.get("rating", "N/A"),
            review_count=business_data.get("review_count", "N/A"),
            website_analysis=website_analysis,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._settings.ai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.ai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._settings.ai_model,
                        "messages": [
                            {"role": "system", "content": "You are a research analyst. Respond only in valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1500,
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)

                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    if content.endswith("```"):
                        content = content[:-3]

                result_data = json.loads(content)

                topics = result_data.get("research_topics", [])
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split("\n") if t.strip()]

                questions = result_data.get("validation_questions", [])
                if isinstance(questions, str):
                    questions = [q.strip() for q in questions.split("\n") if q.strip()]

                return AIAnalysisResult(
                    business_id=0,
                    operational_problems=result_data.get("operational_problems"),
                    info_system_opportunities=result_data.get("info_system_opportunities"),
                    research_relevance=result_data.get("research_relevance"),
                    research_topics=topics[:5],
                    validation_questions=questions[:5],
                    model_used=self._settings.ai_model,
                    tokens_used=tokens_used,
                )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", e)
            return AIAnalysisResult(
                business_id=0,
                operational_problems="AI response was not valid JSON. Raw response saved.",
                model_used=self._settings.ai_model,
            )
        except httpx.HTTPStatusError as e:
            logger.error("AI API error: %s", e.response.status_code)
            return AIAnalysisResult(
                business_id=0,
                operational_problems=f"AI API error: {e.response.status_code}",
                model_used=self._settings.ai_model,
            )
        except Exception as e:
            logger.error("AI analysis failed: %s", e)
            return AIAnalysisResult(
                business_id=0,
                operational_problems=f"Analysis failed: {type(e).__name__}",
                model_used=self._settings.ai_model,
            )
