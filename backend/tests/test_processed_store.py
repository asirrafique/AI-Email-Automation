import app.services.processed_store as processed_store


def test_email_is_not_processed_initially(tmp_path, monkeypatch):
    test_db = tmp_path / "test_processed_emails.db"

    monkeypatch.setattr(
        processed_store,
        "DB_FILE",
        test_db,
    )

    assert processed_store.is_processed("message-123") is False


def test_mark_email_as_processed(tmp_path, monkeypatch):
    test_db = tmp_path / "test_processed_emails.db"

    monkeypatch.setattr(
        processed_store,
        "DB_FILE",
        test_db,
    )

    processed_store.mark_processed("message-123")

    assert processed_store.is_processed("message-123") is True


def test_duplicate_message_is_not_inserted_twice(tmp_path, monkeypatch):
    test_db = tmp_path / "test_processed_emails.db"

    monkeypatch.setattr(
        processed_store,
        "DB_FILE",
        test_db,
    )

    processed_store.mark_processed("message-123")
    processed_store.mark_processed("message-123")

    connection = processed_store.get_connection()

    try:
        cursor = connection.execute(
            "SELECT COUNT(*) FROM processed_emails WHERE message_id = ?",
            ("message-123",),
        )

        count = cursor.fetchone()[0]

    finally:
        connection.close()

    assert count == 1