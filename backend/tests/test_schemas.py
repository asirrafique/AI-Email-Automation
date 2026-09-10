from app.llm.schemas import GeneratedReply, LeadClassification


def test_sales_lead_schema():
    classification = LeadClassification(
        is_sales_lead=True,
        confidence=0.95,
        lead_name="John Smith",
        company="Acme Inc",
        intent="Looking for AI development services",
        requirements="AI customer support platform",
        reason="The sender is asking about professional development services.",
    )

    assert classification.is_sales_lead is True
    assert classification.confidence == 0.95
    assert classification.lead_name == "John Smith"
    assert classification.company == "Acme Inc"


def test_non_sales_lead_schema():
    classification = LeadClassification(
        is_sales_lead=False,
        confidence=0.98,
        lead_name=None,
        company=None,
        intent="Job alert",
        requirements=None,
        reason="This is a job notification rather than a sales opportunity.",
    )

    assert classification.is_sales_lead is False
    assert classification.confidence == 0.98


def test_generated_reply_schema():
    reply = GeneratedReply(
        subject="Re: AI development inquiry",
        body=(
            "Hi John,\n\n"
            "Thank you for reaching out.\n\n"
            "Best regards,\n"
            "Asir Rafique"
        ),
    )

    assert reply.subject.startswith("Re:")
    assert "Asir Rafique" in reply.body