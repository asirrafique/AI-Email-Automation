import logging
import os

from ..gmail.service import (
    create_gmail_draft,
    get_unread_emails,
    send_gmail_message,
)
from ..llm.gemini import (
    classify_email,
    generate_sales_reply,
)
from .processed_store import (
    is_processed,
    mark_processed,
)


logger = logging.getLogger(__name__)


def get_email_data(email: dict) -> dict:
    """
    Return safe email metadata for API responses.
    """

    return {
        "id": email.get("id"),
        "thread_id": email.get("thread_id"),
        "sender_name": email.get("sender_name"),
        "sender_email": email.get("sender_email"),
        "subject": email.get("subject"),
        "date": email.get("date"),
        "message_id": email.get("message_id"),
    }


def get_reply_subject(original_subject: str) -> str:
    """
    Create a reply subject from the original email subject.
    """

    original_subject = (original_subject or "").strip()

    if original_subject.lower().startswith("re:"):
        return original_subject

    return f"Re: {original_subject}"


def generate_reply_for_email(email: dict, classification):
    """
    Generate a personalized reply for a confirmed sales lead.
    """

    return generate_sales_reply(
        sender_name=email["sender_name"],
        sender_email=email["sender_email"],
        subject=email["subject"],
        body=email["body"],
        classification=classification,
    )


def create_reply_draft(email: dict, generated_reply) -> dict:
    """
    Create an unsent Gmail draft replying to the original email.
    """

    reply_subject = get_reply_subject(email["subject"])

    return create_gmail_draft(
        to_email=email["sender_email"],
        subject=reply_subject,
        body=generated_reply.body,
        thread_id=email["thread_id"],
        message_id=email["message_id"],
    )


def is_automated_sender(sender_email: str) -> bool:
    """
    Detect common automated or unwanted sender addresses.
    """

    sender_email = (sender_email or "").strip().lower()

    if not sender_email:
        return True

    automated_prefixes = (
        "no-reply@",
        "noreply@",
        "donotreply@",
        "do-not-reply@",
        "mailer-daemon@",
        "notifications@",
        "notification@",
        "newsletter@",
        "updates@",
        "marketing@",
        "bounce@",
    )

    automated_words = (
        "no-reply",
        "noreply",
        "donotreply",
        "notification",
        "newsletter",
        "mailer-daemon",
        "automated",
    )

    if sender_email.startswith(automated_prefixes):
        return True

    return any(word in sender_email for word in automated_words)


def is_self_email(sender_email: str) -> bool:
    """
    Prevent replying to your own Gmail address.
    """

    sender_email = (sender_email or "").strip().lower()
    own_email = os.getenv("GMAIL_USER_EMAIL", "").strip().lower()

    if not own_email:
        return False

    return sender_email == own_email


def get_classification_confidence(classification) -> float:
    """
    Safely read the confidence value from the classification result.

    If the model does not provide confidence, return 0.0 so that
    automatic sending is blocked instead of making an unsafe guess.
    """

    confidence = getattr(classification, "confidence", None)

    if confidence is None:
        return 0.0

    try:
        return float(confidence)
    except (TypeError, ValueError):
        return 0.0


def classify_latest_unread_email():
    """
    Fetch the latest unread email and classify it with Gemini.
    """

    emails = get_unread_emails(max_results=1)

    if not emails:
        return None

    email = emails[0]

    classification = classify_email(
        sender_name=email["sender_name"],
        sender_email=email["sender_email"],
        subject=email["subject"],
        body=email["body"],
    )

    return {
        "email": get_email_data(email),
        "classification": classification.model_dump(),
    }


def process_latest_unread_email() -> dict:
    """
    Draft workflow.

    Sales leads receive an AI-generated Gmail draft.
    Non-sales emails are ignored.
    """

    emails = get_unread_emails(max_results=1)

    if not emails:
        return {
            "status": "no_email",
            "message": "No unread emails found.",
        }

    email = emails[0]

    if is_processed(email["id"]):
        return {
            "status": "already_processed",
            "message": "This email has already been processed.",
            "email": get_email_data(email),
        }

    classification = classify_email(
        sender_name=email["sender_name"],
        sender_email=email["sender_email"],
        subject=email["subject"],
        body=email["body"],
    )

    result = {
        "email": get_email_data(email),
        "classification": classification.model_dump(),
    }

    if not classification.is_sales_lead:
        mark_processed(email["id"])

        result["action"] = "ignored"
        result["message"] = (
            "Email was not identified as a sales lead."
        )

        return result

    generated_reply = generate_reply_for_email(
        email,
        classification,
    )

    draft = create_reply_draft(
        email,
        generated_reply,
    )

    mark_processed(email["id"])

    result["action"] = "draft_created"
    result["reply"] = generated_reply.model_dump()
    result["draft"] = {
        "id": draft.get("id"),
        "message_id": draft.get("message", {}).get("id"),
        "thread_id": draft.get("message", {}).get("threadId"),
    }

    return result


def process_latest_unread_email_and_send() -> dict:
    """
    Automatically process the latest unread email.

    Safety protections:
    - Only one email is processed per worker cycle.
    - Previously processed messages are skipped.
    - Your own email address is ignored.
    - Automated sender addresses are ignored.
    - Only sales leads are considered.
    - Low-confidence classifications are skipped.
    - Test mode prevents actual sending.
    - The message is marked processed only after successful sending.
    """

    emails = get_unread_emails(max_results=1)

    if not emails:
        return {
            "status": "no_email",
            "message": "No unread emails found.",
        }

    email = emails[0]
    sender_email = email.get("sender_email", "").strip().lower()

    if is_processed(email["id"]):
        return {
            "status": "already_processed",
            "message": "This email has already been processed.",
            "email": get_email_data(email),
        }

    if is_self_email(sender_email):
        mark_processed(email["id"])

        return {
            "status": "skipped",
            "action": "own_email",
            "message": "The email was sent from your own Gmail address.",
            "email": get_email_data(email),
        }

    if is_automated_sender(sender_email):
        mark_processed(email["id"])

        return {
            "status": "skipped",
            "action": "automated_sender",
            "message": "Automated sender detected. No reply was sent.",
            "email": get_email_data(email),
        }

    classification = classify_email(
        sender_name=email["sender_name"],
        sender_email=email["sender_email"],
        subject=email["subject"],
        body=email["body"],
    )

    result = {
        "email": get_email_data(email),
        "classification": classification.model_dump(),
    }

    if not classification.is_sales_lead:
        mark_processed(email["id"])

        result["action"] = "ignored"
        result["message"] = (
            "Email was not identified as a sales lead."
        )

        return result

    minimum_confidence = float(
        os.getenv("AUTO_REPLY_MIN_CONFIDENCE", "0.85")
    )

    confidence = get_classification_confidence(classification)

    if confidence < minimum_confidence:
        mark_processed(email["id"])

        result["action"] = "low_confidence"
        result["message"] = (
            "The email was skipped because the AI confidence "
            "was below the configured threshold."
        )
        result["confidence"] = confidence
        result["minimum_confidence"] = minimum_confidence

        return result

    generated_reply = generate_reply_for_email(
        email,
        classification,
    )

    reply_subject = get_reply_subject(email["subject"])

    test_mode = (
        os.getenv("AUTO_REPLY_TEST_MODE", "true").lower() == "true"
    )

    if test_mode:
        logger.warning(
            "AUTO_REPLY_TEST_MODE=true. Email was not sent."
        )

        # Do not mark the email as processed in test mode.
        # This allows you to test again after reviewing the result.
        result["action"] = "test_mode"
        result["message"] = (
            "The AI reply was generated but not sent because "
            "AUTO_REPLY_TEST_MODE=true."
        )
        result["reply"] = {
            "subject": reply_subject,
            "body": generated_reply.body,
        }

        return result

    sent_message = send_gmail_message(
        to_email=sender_email,
        subject=reply_subject,
        body=generated_reply.body,
        thread_id=email["thread_id"],
        message_id=email["message_id"],
    )

    # Mark as processed only after Gmail confirms successful sending.
    mark_processed(email["id"])

    result["action"] = "sent_directly"
    result["message"] = (
        "AI reply was sent directly through Gmail."
    )
    result["reply"] = {
        "subject": reply_subject,
        "body": generated_reply.body,
    }
    result["sent_message"] = {
        "id": sent_message.get("id"),
        "thread_id": sent_message.get("threadId"),
    }

    return result