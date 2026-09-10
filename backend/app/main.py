import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .gmail.auth import get_google_flow, get_credentials
from .gmail.service import get_profile, get_unread_emails
from .services.email_classifier import (
    classify_latest_unread_email,
    process_latest_unread_email,
)


load_dotenv()

logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI Email Automation",
    description="AI-powered email classification and sales lead response automation.",
    version="1.0.0",
)


session_secret = os.getenv("SESSION_SECRET_KEY")

if not session_secret:
    raise RuntimeError(
        "SESSION_SECRET_KEY is not configured. "
        "Please add it to the .env file."
    )


app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
)


@app.get("/")
def root():
    return {
        "message": "AI Email Automation API is running"
    }


@app.get("/auth/login")
def auth_login(request: Request):
    """Start Google OAuth authentication."""

    try:
        flow = get_google_flow()

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        request.session["oauth_state"] = state
        request.session["code_verifier"] = flow.code_verifier

        return RedirectResponse(authorization_url)

    except Exception:
        logger.exception("Failed to start Gmail authentication.")

        raise HTTPException(
            status_code=500,
            detail="Unable to start Gmail authentication.",
        )


@app.get("/auth/callback")
def auth_callback(request: Request, code: str, state: str):
    """Handle Google's OAuth callback."""

    saved_state = request.session.get("oauth_state")
    code_verifier = request.session.get("code_verifier")

    if not saved_state or state != saved_state:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state. Please start authentication again.",
        )

    if not code_verifier:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth code verifier. Please start authentication again.",
        )

    try:
        flow = get_google_flow()

        flow.code_verifier = code_verifier

        flow.fetch_token(code=code)

        credentials = flow.credentials

        token_file = Path(__file__).resolve().parents[1] / "token.json"

        token_file.write_text(
            credentials.to_json()
        )

        request.session.pop("oauth_state", None)
        request.session.pop("code_verifier", None)

        return {
            "message": "Gmail authentication successful!",
            "next": "You can now use the Gmail API.",
        }

    except Exception:
        logger.exception("Gmail OAuth callback failed.")

        raise HTTPException(
            status_code=500,
            detail="Gmail authentication failed.",
        )


@app.get("/gmail/profile")
def gmail_profile():
    """Test the authenticated Gmail connection."""

    try:
        credentials = get_credentials()

        if not credentials:
            return {
                "authenticated": False,
                "message": "Please visit /auth/login first.",
            }

        profile = get_profile()

        return {
            "authenticated": True,
            "email": profile.get("emailAddress"),
            "messages_total": profile.get("messagesTotal"),
            "threads_total": profile.get("threadsTotal"),
        }

    except Exception:
        logger.exception("Unable to access Gmail profile.")

        raise HTTPException(
            status_code=502,
            detail="Unable to access Gmail.",
        )


@app.get("/gmail/emails")
def gmail_emails():
    """Fetch metadata for the latest unread emails."""

    try:
        emails = get_unread_emails(max_results=5)

        safe_emails = []

        for email in emails:
            safe_emails.append(
                {
                    "id": email.get("id"),
                    "thread_id": email.get("thread_id"),
                    "sender_name": email.get("sender_name"),
                    "sender_email": email.get("sender_email"),
                    "subject": email.get("subject"),
                    "date": email.get("date"),
                    "message_id": email.get("message_id"),
                }
            )

        return {
            "count": len(safe_emails),
            "emails": safe_emails,
        }

    except Exception:
        logger.exception("Unable to fetch Gmail emails.")

        raise HTTPException(
            status_code=502,
            detail="Unable to fetch Gmail emails.",
        )


@app.get("/ai/classify-latest")
def classify_latest_email():
    """Classify the latest unread Gmail email using Gemini."""

    try:
        result = classify_latest_unread_email()

        if result is None:
            return {
                "message": "No unread emails found."
            }

        return result

    except Exception:
        logger.exception("Email classification failed.")

        raise HTTPException(
            status_code=502,
            detail="Email classification failed.",
        )


@app.post("/ai/process-latest")
def process_latest_email():
    """
    Classify the latest unread email and create a draft
    if it is a sales lead.
    """

    try:
        return process_latest_unread_email()

    except Exception:
        logger.exception("Email automation failed.")

        raise HTTPException(
            status_code=502,
            detail="Email automation failed.",
        )