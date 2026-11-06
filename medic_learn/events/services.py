import hashlib
import json
import uuid

import pika
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models import Inbox, Outbox


def enqueue(topic, payload):
    return Outbox.objects.create(topic=topic, payload=payload)


def connection():
    params = pika.URLParameters(settings.RABBITMQ_URL)
    params.socket_timeout = 10
    params.blocked_connection_timeout = 10
    return pika.BlockingConnection(params)


def topology(channel):
    channel.exchange_declare(exchange="medic.events", exchange_type="topic", durable=True)
    channel.exchange_declare(exchange="medic.dead", exchange_type="fanout", durable=True)
    channel.queue_declare(queue="medic.dead", durable=True)
    channel.queue_bind(queue="medic.dead", exchange="medic.dead")
    channel.queue_declare(
        queue="medic.notifications",
        durable=True,
        arguments={"x-dead-letter-exchange": "medic.dead"},
    )
    channel.queue_bind(
        queue="medic.notifications", exchange="medic.events", routing_key="users.verified"
    )
    channel.queue_bind(
        queue="medic.notifications", exchange="medic.events", routing_key="channels.observation"
    )


def publish_pending():
    with connection() as conn:
        channel = conn.channel()
        topology(channel)
        channel.confirm_delivery()
        for event in Outbox.objects.filter(published=False).order_by("occurred_at")[:100]:
            body = {
                "event_id": str(event.pk),
                "topic": event.topic,
                "occurred_at": event.occurred_at.isoformat(),
                "payload": event.payload,
                "version": 1,
            }
            channel.basic_publish(
                exchange="medic.events",
                routing_key=event.topic,
                body=json.dumps(body).encode(),
                properties=pika.BasicProperties(
                    content_type="application/json", delivery_mode=2, message_id=str(event.pk)
                ),
                mandatory=True,
            )
            Outbox.objects.filter(pk=event.pk).update(published=True)


def consume(body, routing_key, message_id):
    if len(body) > 1048576:
        raise ValueError("Envelope too large")
    event = json.loads(body)
    event_id = uuid.UUID(event["event_id"])
    if (
        event["version"] != 1
        or event["topic"] != routing_key
        or str(event_id) != message_id
        or not isinstance(event["payload"], dict)
    ):
        raise ValueError("Invalid envelope")
    if (
        not isinstance(event.get("occurred_at"), str)
        or parse_datetime(event["occurred_at"]) is None
    ):
        raise ValueError("Invalid occurrence timestamp")
    fingerprint = hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with transaction.atomic():
        receipt, created = Inbox.objects.get_or_create(
            id=event_id, defaults={"fingerprint": fingerprint}
        )
        if receipt.fingerprint != fingerprint:
            raise ValueError("Occurrence conflict")
        if created:
            if event["topic"] == "users.verified":
                from medic_learn.notifications.services import capture

                capture(event_id, event["payload"]["user_id"])
            elif event["topic"] == "channels.observation":
                from medic_learn.messages.services import observe

                observe(event["payload"])
            else:
                raise ValueError("Unsupported topic")
