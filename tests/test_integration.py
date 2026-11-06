import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections

from medic_learn.accounts.domain import AccountError
from medic_learn.accounts.models import User
from medic_learn.events.models import Outbox
from medic_learn.events.services import connection, consume, enqueue, publish_pending, topology
from medic_learn.messages.models import Message
from medic_learn.messages.services import dispatch
from medic_learn.notifications.services import disseminate
from medic_learn.verification.services import issue, verify


@pytest.mark.django_db(transaction=True)
def test_concurrent_verification_has_one_winner():
    import re

    from django.core import mail

    user = User.objects.create_user("race@example.com", "secret")
    issue(user)
    code = re.search(r"\b[0-9]{5}\b", mail.outbox[-1].body).group()

    def attempt():
        close_old_connections()
        try:
            verify(User.objects.get(pk=user.pk), code)
            return "verified"
        except AccountError:
            return "rejected"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: attempt(), range(2))) == ["rejected", "verified"]
    assert Outbox.objects.count() == 1


@pytest.mark.skipif(
    os.environ.get("RUN_BROKER_TESTS") != "1", reason="Set RUN_BROKER_TESTS=1 for local RabbitMQ"
)
@pytest.mark.django_db(transaction=True)
def test_real_broker_pipeline_and_dead_letter():
    import pika
    from django.core import mail

    user = User.objects.create_user(f"{uuid.uuid4()}@example.com", "secret", state="verified")
    user.profile.notifications_enabled = True
    user.profile.save()
    event = enqueue("users.verified", {"user_id": str(user.pk)})
    publish_pending()
    event.refresh_from_db()
    assert event.published
    with connection() as conn:
        channel = conn.channel()
        topology(channel)
        method, props, body = channel.basic_get("medic.notifications")
        assert method is not None
        consume(body, method.routing_key, props.message_id)
        channel.basic_ack(method.delivery_tag)
        # Replay the original occurrence is harmless.
        consume(body, method.routing_key, props.message_id)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange="medic.events",
            routing_key="users.verified",
            body=b"invalid",
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True,
        )
        method, props, body = channel.basic_get("medic.notifications")
        assert method is not None
        with pytest.raises(ValueError):
            consume(body, method.routing_key, props.message_id)
        channel.basic_nack(method.delivery_tag, requeue=False)
        import time

        deadline = time.monotonic() + 5
        dead = None
        while time.monotonic() < deadline:
            dead, _, payload = channel.basic_get("medic.dead")
            if dead:
                break
            time.sleep(0.05)
        assert dead is not None
        assert payload == b"invalid"
        channel.basic_ack(dead.delivery_tag)
    disseminate()
    dispatch()
    assert Message.objects.get().state == "accepted"
    assert len(mail.outbox) == 1
