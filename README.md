# AI Email Automation

An AI-powered Gmail automation backend built with **FastAPI, Gmail API, and Google Gemini**.

The system reads unread Gmail messages, identifies potential sales leads, generates professional replies, and creates Gmail drafts. It also supports optional automatic replies through a background worker.

> **Safety:** Keep `AUTO_REPLY_TEST_MODE=true` while testing. Automatic sending should only be enabled after careful review.

## Features

* Google OAuth 2.0 authentication
* Read unread Gmail messages
* Extract email sender, subject, and body
* Classify emails using Google Gemini
* Detect potential sales leads
* Generate personalized professional replies
* Create Gmail drafts for human review
* Optional automatic email sending
* Background worker for periodic email processing
* Confidence threshold for AI decisions
* Duplicate-processing protection using SQLite
* Sender filtering for automated emails and self-sent messages
* Prompt-injection-aware AI instructions
* Automated unit tests

## How It Works

```text
Gmail Inbox
    ↓
Google OAuth Authentication
    ↓
Fetch Unread Emails
    ↓
Extract Email Content
    ↓
Gemini Classifies the Email
    ↓
Is It a Sales Lead?
    ↓
Confidence Check
    ↓
Generate Reply
    ↓
Create Gmail Draft
    or
Send Automatically
    ↓
Store Processed Message ID
```

## Technology Stack

| Technology       | Purpose                                   |
| ---------------- | ----------------------------------------- |
| FastAPI          | Backend API                               |
| Gmail API        | Read and send Gmail messages              |
| Google OAuth 2.0 | Secure Gmail authentication               |
| Google Gemini    | Email classification and reply generation |
| Pydantic         | Validate structured AI responses          |
| SQLite           | Track processed emails                    |
| Python           | Application development                   |
| Pytest           | Automated testing                         |

## Project Structure

```text
AI Email Automation/
│
├── backend/
│   ├── app/
│   │   ├── gmail/
│   │   │   ├── auth.py
│   │   │   └── service.py
│   │   │
│   │   ├── llm/
│   │   │   ├── gemini.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── email_classifier.py
│   │   │   ├── email_worker.py
│   │   │   └── processed_store.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   ├── manual_gemini_test.py
│   ├── manual_reply_test.py
│   ├── manual_prompt_injection_test.py
│   ├── requirements.txt
│   └── .env.example
│
├── pytest.ini
├── .gitignore
└── README.md
```

## Main Workflow

### 1. Manual Draft Workflow

1. Fetch the latest unread email.
2. Check whether the message was already processed.
3. Extract the email content.
4. Classify the email using Gemini.
5. Ignore the email if it is not a sales lead.
6. Check the confidence score.
7. Generate a professional reply.
8. Create an unsent Gmail draft.
9. Review and send the draft manually.

### 2. Automatic Workflow

When the background worker is enabled:

1. Check Gmail at a configured interval.
2. Fetch unread messages.
3. Skip already processed messages.
4. Skip automated senders and self-sent emails.
5. Classify the email using Gemini.
6. Check whether it is a qualified sales lead.
7. Generate a reply.
8. Send the reply only when test mode is disabled.
9. Store the processed message ID in SQLite.

## API Endpoints

| Method | Endpoint                      | Description                      |
| ------ | ----------------------------- | -------------------------------- |
| `GET`  | `/`                           | API status                       |
| `GET`  | `/auth/login`                 | Start Google OAuth               |
| `GET`  | `/auth/callback`              | Handle OAuth callback            |
| `GET`  | `/gmail/profile`              | View Gmail profile               |
| `GET`  | `/gmail/emails`               | Get unread emails                |
| `GET`  | `/ai/classify-latest`         | Classify the latest unread email |
| `POST` | `/ai/process-latest`          | Create a Gmail draft             |
| `POST` | `/gmail/send-draft`           | Send an approved draft           |
| `POST` | `/ai/process-latest-and-send` | Run the automatic reply workflow |
| `GET`  | `/docs`                       | Open Swagger API documentation   |

## Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
SESSION_SECRET_KEY=your_random_session_secret

AUTO_REPLY_ENABLED=true
AUTO_REPLY_TEST_MODE=true
AUTO_REPLY_INTERVAL_SECONDS=60
AUTO_REPLY_MIN_CONFIDENCE=0.85

GMAIL_USER_EMAIL=your_gmail_address
```

### Configuration

* `AUTO_REPLY_ENABLED`: Enables the background worker.
* `AUTO_REPLY_TEST_MODE`: Generates replies without sending them when set to `true`.
* `AUTO_REPLY_INTERVAL_SECONDS`: Time between worker cycles.
* `AUTO_REPLY_MIN_CONFIDENCE`: Minimum confidence required for automatic replies.
* `GMAIL_USER_EMAIL`: Gmail account used for processing.

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it on Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r backend/requirements.txt
```

### 4. Configure Google OAuth

1. Create a project in Google Cloud.
2. Enable the Gmail API.
3. Configure the OAuth consent screen.
4. Create an OAuth client for a web application.
5. Add this redirect URI:

```text
http://localhost:8000/auth/callback
```

6. Download the OAuth client JSON file.
7. Save it as:

```text
backend/credentials.json
```

8. Add your Gmail account as a test user if required.

## Run the Application

From the project root:

```bash
python -m uvicorn app.main:app --app-dir backend --reload
```

Open the application at:

```text
http://127.0.0.1:8000
```

Start Gmail authentication here:

```text
http://127.0.0.1:8000/auth/login
```

Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Testing

Run the automated tests:

```bash
python -m pytest -v
```

The tests cover:

* Sales-lead classification
* Non-sales emails
* Duplicate processing
* SQLite message tracking
* Gmail draft creation
* Pydantic schemas
* Already-processed messages

Manual integration tests are also available for Gemini, reply generation, and prompt-injection behavior.

## Safety Measures

The application includes:

* Test mode to prevent accidental sending
* Human approval through Gmail drafts
* Confidence thresholds
* Duplicate-processing protection
* Sender filtering
* Protection against instructions embedded in email content
* Restrictions against inventing prices, guarantees, discounts, or commitments
* Email-body length limits before sending content to Gemini

## Current Limitations

* Uses polling instead of Gmail push notifications.
* Processes one unread email per worker cycle.
* Uses SQLite for local or single-instance execution.
* Does not include a frontend dashboard.
* Does not yet include a production job queue or distributed locking.
* Uses a local OAuth token file.

## Future Improvements

* Add a frontend review dashboard.
* Use PostgreSQL for production storage.
* Add Celery or RQ for background jobs.
* Add retries and dead-letter handling.
* Add Gmail push notifications.
* Add monitoring and audit logs.
* Add Docker and deployment configuration.
* Add end-to-end tests using a dedicated Gmail account.

## Author

**Asir Rafique**

Full-stack developer focused on AI application development, automation, and modern web technologies.
