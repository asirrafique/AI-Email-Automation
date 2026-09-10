import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DB_FILE = BASE_DIR / "processed_emails.db"


def get_connection():
    """Create a connection to the local SQLite database."""

    connection = sqlite3.connect(DB_FILE)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id TEXT PRIMARY KEY
        )
        """
    )

    connection.commit()

    return connection


def is_processed(message_id: str) -> bool:
    """Check whether a Gmail message has already been processed."""

    connection = get_connection()

    try:
        cursor = connection.execute(
            "SELECT 1 FROM processed_emails WHERE message_id = ?",
            (message_id,),
        )

        return cursor.fetchone() is not None

    finally:
        connection.close()


def mark_processed(message_id: str) -> None:
    """Mark a Gmail message as processed."""

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT OR IGNORE INTO processed_emails (message_id)
            VALUES (?)
            """,
            (message_id,),
        )

        connection.commit()

    finally:
        connection.close()