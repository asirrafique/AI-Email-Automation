from app.gmail.service import create_gmail_draft, get_unread_emails
from app.llm.gemini import classify_email, generate_sales_reply
from app.services.processed_store import is_processed, mark_processed


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
      "email": {
        "id": email["id"],
        "thread_id": email["thread_id"],
        "sender_name": email["sender_name"],
        "sender_email": email["sender_email"],
        "subject": email["subject"],
        "date": email["date"],
        "message_id": email["message_id"],
     },
     "classification": classification.model_dump(),
   }


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

    # Preserve the original subject rather than trusting the LLM
    # to construct the subject.
    original_subject = email["subject"]

    if original_subject.lower().startswith("re:"):
        reply_subject = original_subject
    else:
        reply_subject = f"Re: {original_subject}"

    draft = create_gmail_draft(
        to_email=email["sender_email"],
        subject=reply_subject,
        body=generated_reply.body,
        thread_id=email["thread_id"],
        message_id=email["message_id"],
    )

    return draft


def process_latest_unread_email() -> dict:
    """
    Process the latest unread email.

    Sales leads receive an AI-generated Gmail draft.
    Non-sales emails are classified but do not receive a draft.

    Each Gmail message is processed only once.
    """

    emails = get_unread_emails(max_results=1)

    if not emails:
        return {
            "status": "no_email",
            "message": "No unread emails found.",
        }

    email = emails[0]

    # Prevent the same Gmail message from being processed again.
    if is_processed(email["id"]):
        return {
            "status": "already_processed",
            "message": "This email has already been processed.",
            "email": {
                "id": email["id"],
                "thread_id": email["thread_id"],
                "sender_name": email["sender_name"],
                "sender_email": email["sender_email"],
                "subject": email["subject"],
                "date": email["date"],
            },
        }

    classification = classify_email(
        sender_name=email["sender_name"],
        sender_email=email["sender_email"],
        subject=email["subject"],
        body=email["body"],
    )

    result = {
        "email": {
            "id": email["id"],
            "thread_id": email["thread_id"],
            "sender_name": email["sender_name"],
            "sender_email": email["sender_email"],
            "subject": email["subject"],
            "date": email["date"],
        },
        "classification": classification.model_dump(),
    }

    # Do not generate or create a reply for non-sales emails.
    if not classification.is_sales_lead:
        mark_processed(email["id"])

        result["action"] = "ignored"
        result["message"] = "Email was not identified as a sales lead."

        return result

    # Generate a response only for confirmed sales leads.
    generated_reply = generate_reply_for_email(
        email,
        classification,
    )

    # Create the unsent Gmail draft.
    draft = create_reply_draft(
        email,
        generated_reply,
    )

    # Mark the email as processed only after the draft
    # has been successfully created.
    mark_processed(email["id"])

    result["action"] = "draft_created"
    result["reply"] = generated_reply.model_dump()
    result["draft"] = {
        "id": draft.get("id"),
        "message_id": draft.get("message", {}).get("id"),
        "thread_id": draft.get("message", {}).get("threadId"),
    }

    return result   