from __future__ import annotations

EMAIL_TEMPLATE = """Dear {business_name} Team,

I am a university student conducting research on information systems and digital transformation in local businesses. I found your business through my research on established businesses in the {category} sector.

I am writing to kindly request an opportunity to:

1. Conduct a brief interview (15-30 minutes) about your business operations and technology use
2. Learn about any challenges you face with your current systems
3. Understand how digital tools have impacted your business

This research is purely academic and will help contribute to understanding how local businesses can benefit from information system implementations.

Your participation would be voluntary, and I would be happy to share my findings with you after the research is complete.

Would you be available for a brief conversation? I can accommodate your schedule and meet in person or online.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your University]
[Your Contact Information]"""


def generate_email(
    business_name: str,
    category: str = "your industry",
    custom_intro: str | None = None,
) -> tuple[str, str]:
    subject = f"Research Participation Request - {business_name}"
    body = EMAIL_TEMPLATE.format(
        business_name=business_name,
        category=category,
    )
    if custom_intro:
        body = custom_intro + "\n\n" + body
    return subject, body
