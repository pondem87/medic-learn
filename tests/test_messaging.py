import hashlib
import hmac
import json
import uuid
from unittest.mock import patch

import pytest
from django.core import mail

from medic_learn.accounts.models import User
from medic_learn.events.models import Inbox, Outbox
from medic_learn.events.services import consume
from medic_learn.messages.models import Message
from medic_learn.messages.services import dispatch
from medic_learn.notifications.services import disseminate

pytestmark = pytest.mark.django_db


def envelope(user):
    event_id = str(uuid.uuid4())
    return {
        "event_id": event_id,
        "topic": "users.verified",
        "version": 1,
        "occurred_at": "2026-11-03T00:00:00Z",
        "payload": {"user_id": str(user.pk)},
    }


def test_event_deduplication_and_dispatch():
    user = User.objects.create_user("a@example.com", "secret", state="verified")
    user.profile.notifications_enabled = True
    user.profile.save()
    event = envelope(user)
    for _ in range(2):
        consume(json.dumps(event).encode(), event["topic"], event["event_id"])
    disseminate()
    disseminate()
    dispatch()
    dispatch()
    assert len(mail.outbox) == 1
    assert Message.objects.get().state == "accepted"
    event["payload"]["extra"] = True
    with pytest.raises(ValueError):
        consume(json.dumps(event).encode(), event["topic"], event["event_id"])
    assert Inbox.objects.count() == 1


def test_opt_out_and_uncertain_delivery():
    user = User.objects.create_user("a@example.com", "secret", state="verified")
    event = envelope(user)
    consume(json.dumps(event).encode(), event["topic"], event["event_id"])
    disseminate()
    assert not Message.objects.exists()
    user.profile.notifications_enabled = True
    user.profile.save()
    Message.objects.create(user=user, recipient=user.email, subject="Welcome", body="Hello")
    with patch("medic_learn.email.channel.EmailChannel.send", side_effect=TimeoutError):
        dispatch()
    assert Message.objects.get().state == "uncertain"
    dispatch()
    assert len(mail.outbox) == 0


def test_whatsapp_signature_scope_and_deduplication(client, settings):
    settings.WHATSAPP_ENABLED = True
    settings.WHATSAPP_APP_SECRET = "fixture-only"
    settings.WHATSAPP_PHONE_ID = "123"
    body = json.dumps(
        {
            "entry": [
                {"changes": [{"value": {"metadata": {"phone_number_id": "123"}, "statuses": []}}]}
            ]
        }
    ).encode()
    assert (
        client.post("/webhooks/whatsapp/", body, content_type="application/json").status_code == 403
    )
    signature = "sha256=" + hmac.new(b"fixture-only", body, hashlib.sha256).hexdigest()
    for _ in range(2):
        assert (
            client.post(
                "/webhooks/whatsapp/",
                body,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=signature,
            ).status_code
            == 200
        )
    assert Outbox.objects.count() == 1


def test_provider_rejection_and_unavailable_channel(settings):
    from medic_learn.messages.contracts import ChannelRejected

    Message.objects.create(recipient="test@example.com", subject="test", body="test")
    with patch("medic_learn.email.channel.EmailChannel.send", side_effect=ChannelRejected):
        dispatch()
    assert Message.objects.get().state == "rejected"
    settings.WHATSAPP_ENABLED = False
    message = Message.objects.create(
        channel="whatsapp", recipient="26700000000", subject="welcome", body=""
    )
    dispatch()
    message.refresh_from_db()
    assert message.state == "queued"


def test_whatsapp_template_request(settings):
    import httpx

    from medic_learn.whatsapp.channel import WhatsAppChannel

    settings.WHATSAPP_ENABLED = True
    settings.WHATSAPP_API_VERSION = "v23.0"
    settings.WHATSAPP_PHONE_ID = "fixture-phone"
    settings.WHATSAPP_TOKEN = "fixture-token"
    response = httpx.Response(
        200,
        json={"messages": [{"id": "fixture-message"}]},
        request=httpx.Request("POST", "https://example.invalid"),
    )
    with patch("medic_learn.whatsapp.channel.httpx.post", return_value=response) as post:
        assert (
            WhatsAppChannel().send("26700000000", "approved_template", "ignored")
            == "fixture-message"
        )
    assert post.call_args.kwargs["json"]["template"]["name"] == "approved_template"
    assert post.call_args.kwargs["follow_redirects"] is False


def test_receipt_progress_does_not_regress():
    from medic_learn.messages.services import observe

    message = Message.objects.create(
        channel="whatsapp",
        recipient="26700000000",
        subject="welcome",
        body="",
        state="accepted",
        provider_id="receipt-test",
    )
    for status in ["read", "sent", "failed"]:
        observe(
            {"statuses": [{"id": "receipt-test", "recipient_id": "26700000000", "status": status}]}
        )
    message.refresh_from_db()
    assert message.state == "read"
