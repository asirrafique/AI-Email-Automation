import base64
from email.message import EmailMessage
from email.utils import parseaddr

from googleapiclient.discovery import build

from .auth import get_credentials


def get_gmail_service():
    """Return an authenticated Gmail API service."""

    credentials = get_credentials()

    if not credentials:
        raise RuntimeError(
            "Gmail is not authenticated. Please complete Google OAuth first."
        )

    return build("gmail", "v1", credentials=credentials)


def get_profile():
    """Get the authenticated Gmail account profile."""

    service = get_gmail_service()

    return service.users().getProfile(userId="me").execute()


def decode_body(data: str) -> str:
    """Decode Gmail's URL-safe base64 email body."""

    decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    return decoded.decode("utf-8", errors="replace")


def extract_email_body(payload: dict) -> str:
    """Extract plain-text body from a Gmail message payload."""

    if payload.get("body", {}).get("data"):
        return decode_body(payload["body"]["data"])

    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")

        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return decode_body(part["body"]["data"])

        if part.get("parts"):
            body = extract_email_body(part)

            if body:
                return body

    return ""


def get_header(headers: list, name: str) -> str:
    """Get a specific header from Gmail message headers."""

    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


def get_unread_emails(max_results: int = 5) -> list:
    """Fetch the latest unread emails from Gmail."""

    service = get_gmail_service()

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
        )
        .execute()
    )

    messages = response.get("messages", [])

    emails = []

    for message in messages:
        message_data = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="full",
            )
            .execute()
        )

        payload = message_data.get("payload", {})
        headers = payload.get("headers", [])

        sender = get_header(headers, "From")
        subject = get_header(headers, "Subject")
        date = get_header(headers, "Date")
        message_id = get_header(headers, "Message-ID")

        sender_name, sender_email = parseaddr(sender)

        emails.append(
            {
                "id": message_data.get("id"),
                "thread_id": message_data.get("threadId"),
                "sender_name": sender_name,
                "sender_email": sender_email,
                "subject": subject,
                "date": date,
                "message_id": message_id,
                "body": extract_email_body(payload),
            }
        )

    return emails

def create_gmail_draft(
    to_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
    message_id: str | None = None,
) -> dict:
    """
    Create an unsent Gmail draft.

    If thread_id and message_id are provided, the draft is prepared
    as a reply to the original email.
    """

    service = get_gmail_service()

    message = EmailMessage()

    message["To"] = to_email
    message["Subject"] = subject

    # Help Gmail associate the draft with the original conversation.
    if message_id:
        message["In-Reply-To"] = message_id
        message["References"] = message_id

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    gmail_message = {
        "raw": encoded_message,
    }

    if thread_id:
        gmail_message["threadId"] = thread_id

    draft = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body={
                "message": gmail_message,
            },
        )
        .execute()
    )

    return draft