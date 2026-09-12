from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]

REDIRECT_URI = "http://localhost:8000/auth/callback"


def get_google_flow():
    """Create and configure the Google OAuth flow."""

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
    )

    flow.redirect_uri = REDIRECT_URI

    return flow


def get_credentials():
    """Load existing Gmail credentials if available."""

    if not TOKEN_FILE.exists():
        return None

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        TOKEN_FILE.write_text(credentials.to_json())

    return credentials