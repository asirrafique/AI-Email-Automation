import asyncio
import logging
import os

from .email_classifier import process_latest_unread_email_and_send


logger = logging.getLogger(__name__)


def get_worker_settings():
    """
    Read worker settings from the environment each time the worker starts.
    """

    enabled = (
        os.getenv("AUTO_REPLY_ENABLED", "false").lower() == "true"
    )

    interval_seconds = int(
        os.getenv("AUTO_REPLY_INTERVAL_SECONDS", "60")
    )

    return enabled, max(interval_seconds, 30)


async def email_worker():
    """
    Periodically check Gmail for unread messages.

    The worker processes one unread email per cycle.
    """

    enabled, interval_seconds = get_worker_settings()

    if not enabled:
        logger.info(
            "Automatic email worker is disabled. "
            "Set AUTO_REPLY_ENABLED=true to enable it."
        )
        return

    logger.info(
        "Automatic email worker started. "
        "Checking every %s seconds.",
        interval_seconds,
    )

    while True:
        try:
            result = await asyncio.to_thread(
                process_latest_unread_email_and_send
            )

            logger.info(
                "Automatic email processing result: %s",
                result,
            )

        except Exception:
            logger.exception(
                "Automatic email processing failed."
            )

        await asyncio.sleep(interval_seconds)