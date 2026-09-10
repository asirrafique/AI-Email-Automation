from unittest.mock import patch

from app.llm.schemas import GeneratedReply, LeadClassification
from app.services.email_classifier import process_latest_unread_email


def fake_email():
    return {
        "id": "test-message-123",
        "thread_id": "thread-123",
        "sender_name": "John Smith",
        "sender_email": "john@example.com",
        "subject": "Interested in AI development services",
        "date": "Thu, 10 Sep 2026 19:00:00 +0530",
        "message_id": "<test-message-123@example.com>",
        "body": "We are interested in building an AI customer support platform.",
    }


def test_sales_lead_creates_draft():
    classification = LeadClassification(
        is_sales_lead=True,
        confidence=0.95,
        lead_name="John Smith",
        company="Acme Inc",
        intent="Looking for AI development services",
        requirements="AI customer support platform",
        reason="The sender is asking about professional development services.",
    )

    reply = GeneratedReply(
        subject="Re: Interested in AI development services",
        body=(
            "Hi John,\n\n"
            "Thank you for reaching out. We would be happy to discuss "
            "your AI customer support platform.\n\n"
            "Best regards,\n"
            "Asir Rafique"
        ),
    )

    with patch(
        "app.services.email_classifier.get_unread_emails",
        return_value=[fake_email()],
    ), patch(
        "app.services.email_classifier.is_processed",
        return_value=False,
    ), patch(
        "app.services.email_classifier.classify_email",
        return_value=classification,
    ), patch(
        "app.services.email_classifier.generate_reply_for_email",
        return_value=reply,
    ), patch(
        "app.services.email_classifier.create_reply_draft",
        return_value={
            "id": "draft-123",
            "message": {
                "id": "draft-message-123",
                "threadId": "thread-123",
            },
        },
    ), patch(
        "app.services.email_classifier.mark_processed",
    ) as mock_mark_processed:

        result = process_latest_unread_email()

    assert result["action"] == "draft_created"
    assert result["classification"]["is_sales_lead"] is True
    assert result["reply"]["subject"].startswith("Re:")
    assert result["draft"]["id"] == "draft-123"

    mock_mark_processed.assert_called_once_with("test-message-123")


def test_non_sales_email_is_ignored():
    classification = LeadClassification(
        is_sales_lead=False,
        confidence=0.98,
        lead_name=None,
        company=None,
        intent="Newsletter",
        requirements=None,
        reason="This is a newsletter rather than a sales opportunity.",
    )

    with patch(
        "app.services.email_classifier.get_unread_emails",
        return_value=[fake_email()],
    ), patch(
        "app.services.email_classifier.is_processed",
        return_value=False,
    ), patch(
        "app.services.email_classifier.classify_email",
        return_value=classification,
    ), patch(
        "app.services.email_classifier.generate_reply_for_email",
    ) as mock_generate_reply, patch(
        "app.services.email_classifier.create_reply_draft",
    ) as mock_create_draft, patch(
        "app.services.email_classifier.mark_processed",
    ) as mock_mark_processed:

        result = process_latest_unread_email()

    assert result["action"] == "ignored"
    assert result["classification"]["is_sales_lead"] is False

    mock_generate_reply.assert_not_called()
    mock_create_draft.assert_not_called()
    mock_mark_processed.assert_called_once_with("test-message-123")


def test_already_processed_email_is_skipped():
    with patch(
        "app.services.email_classifier.get_unread_emails",
        return_value=[fake_email()],
    ), patch(
        "app.services.email_classifier.is_processed",
        return_value=True,
    ), patch(
        "app.services.email_classifier.classify_email",
    ) as mock_classify:

        result = process_latest_unread_email()

    assert result["status"] == "already_processed"

    mock_classify.assert_not_called()