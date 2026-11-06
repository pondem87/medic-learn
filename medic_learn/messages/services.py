import logging

from django.conf import settings
from django.db import transaction

from medic_learn.email.channel import EmailChannel

from .contracts import Channel, ChannelRejected
from .models import Message, Observation

logger = logging.getLogger(__name__)


def confidential_email(recipient, code):
    # Proof exists in process memory only, never in an outbox or message body.
    try:
        EmailChannel().send(
            recipient,
            "Verify your email",
            f"Your verification code is {code}. It expires in ten minutes.",
        )
        return "accepted"
    except ChannelRejected:
        return "rejected"
    except Exception:
        logger.warning("Confidential email dispatch uncertain")
        return "uncertain"


def dispatch():
    for pk in Message.objects.filter(state="queued").values_list("pk", flat=True)[:100]:
        with transaction.atomic():
            message = Message.objects.select_for_update().get(pk=pk)
            if message.state != "queued":
                continue
            if message.user and (
                not message.user.profile.notifications_enabled or message.user.state != "verified"
            ):
                message.state = "suppressed"
                message.save()
                continue
            if message.channel not in {"email", "whatsapp"} or (
                message.channel == "whatsapp" and not settings.WHATSAPP_ENABLED
            ):
                continue
            message.state = "dispatching"
            message.save()
        try:
            channel: Channel
            if message.channel == "email":
                channel = EmailChannel()
            else:
                from medic_learn.whatsapp.channel import WhatsAppChannel

                channel = WhatsAppChannel()
            provider_id = channel.send(message.recipient, message.subject, message.body)
            Message.objects.filter(pk=pk).update(state="accepted", provider_id=provider_id)
            if message.channel == "whatsapp":
                for receipt in Observation.objects.all().iterator():
                    apply_observation(receipt.payload)
        except ChannelRejected:
            Message.objects.filter(pk=pk).update(state="rejected")
        except Exception:
            Message.objects.filter(pk=pk).update(state="uncertain")
            logger.warning("Message dispatch uncertain: %s", pk)


def observe(payload):
    Observation.objects.create(payload=payload)
    apply_observation(payload)


def apply_observation(payload):
    for status in payload.get("statuses", []):
        ranks = {"accepted": 0, "sent": 1, "failed": 2, "delivered": 3, "read": 4}
        with transaction.atomic():
            message = (
                Message.objects.select_for_update()
                .filter(
                    channel="whatsapp",
                    provider_id=status.get("id"),
                    recipient=status.get("recipient_id"),
                )
                .first()
            )
            state = status.get("status")
            if message and state in ranks and ranks[state] > ranks.get(message.state, -1):
                message.state = state
                message.save()


def enqueue_message(request_id, user_id, recipient, subject, body):
    """Idempotently accept a notification request within the caller's transaction."""
    return Message.objects.get_or_create(
        id=request_id,
        defaults={"user_id": user_id, "recipient": recipient, "subject": subject, "body": body},
    )[0]
