import uuid

from django.db import transaction

from medic_learn.accounts.services import communication_recipient
from medic_learn.messages.services import enqueue_message

from .models import Notification


def capture(event_id, user_id):
    Notification.objects.get_or_create(
        id=uuid.uuid5(event_id, f"welcome:{user_id}"), defaults={"user_id": user_id}
    )


def disseminate():
    for pk in Notification.objects.filter(state="pending").values_list("pk", flat=True)[:100]:
        with transaction.atomic():
            notice = Notification.objects.select_for_update().get(pk=pk)
            if notice.state != "pending":
                continue
            recipient, eligible = communication_recipient(notice.user_id)
            if not eligible:
                notice.state = "suppressed"
            else:
                enqueue_message(
                    notice.pk,
                    notice.user_id,
                    recipient,
                    "Welcome to Medic Learn",
                    "Your email is verified. Welcome to Medic Learn.",
                )
                notice.state = "handed_off"
            notice.save()
