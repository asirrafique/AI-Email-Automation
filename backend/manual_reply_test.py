from app.llm.gemini import generate_sales_reply
from app.llm.schemas import LeadClassification


classification = LeadClassification(
    is_sales_lead=True,
    confidence=0.98,
    lead_name="John Smith",
    company="Acme Inc",
    intent="Looking for an AI development team",
    requirements=(
        "Build an AI-powered customer support platform. "
        "The customer wants pricing, availability, and a call next week."
    ),
    reason="The sender has clear commercial intent and is requesting development services.",
)


result = generate_sales_reply(
    sender_name="John Smith",
    sender_email="john@example.com",
    subject="Interested in your AI development services",
    body="""
Hello,

We are looking for a development team to help us build an
AI-powered customer support platform.

Could you please share your pricing and availability?

We would like to schedule a call next week.

Best regards,
John
""",
    classification=classification,
)


print("Generated reply:")
print(result.model_dump_json(indent=2))