import logging

from celery import shared_task
from django.core.cache import cache
from slack_sdk import WebClient

from app.slack.errors import SlackDisabledException
from backend.settings import cfg

client = WebClient(token=cfg.slack.oauth_token.get_secret_value())
logger = logging.getLogger(__name__)


@shared_task
def send_error_message(subject: str, description: str) -> dict:
    if not cfg.slack.enabled:
        raise SlackDisabledException("Slack notifications are disabled.")

    if cache.get(subject):
        logger.info(f"Skipping duplicate admin notification: {subject}")
        return

    response = client.chat_postMessage(
        channel=cfg.slack.error_notification_channel,
        text=f"{subject}\n{description}",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*{subject}*"}},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{description}```"},
            },
        ],
    )
    logger.info(f"Sent message: {subject}")
    return response
