"""Application email through SES using the Fargate task role (no SMTP credentials)."""

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        client = boto3.client(
            "ses",
            region_name=settings.SES_REGION,
            config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 0}),
        )
        sent = 0
        for message in email_messages:
            if not message.recipients():
                continue
            try:
                client.send_raw_email(
                    Source=message.from_email,
                    Destinations=message.recipients(),
                    RawMessage={"Data": message.message().as_bytes()},
                )
            except Exception:
                if not self.fail_silently:
                    raise
            else:
                sent += 1
        return sent
