import logging
import time

from django.core.management.base import BaseCommand

from medic_learn.events.services import connection, consume, publish_pending, topology
from medic_learn.messages.services import dispatch
from medic_learn.notifications.services import disseminate

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Publish outbox events, consume notifications, and dispatch queued messages."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            try:
                from medic_learn.accounts.operations import run_pending

                run_pending()
                publish_pending()
                with connection() as conn:
                    channel = conn.channel()
                    topology(channel)
                    for _ in range(100):
                        method, properties, body = channel.basic_get("medic.notifications")
                        if method is None:
                            break
                        try:
                            consume(body, method.routing_key, properties.message_id)
                        except Exception:
                            logger.warning("Event rejected: %s", properties.message_id)
                            channel.basic_nack(method.delivery_tag, requeue=False)
                        else:
                            channel.basic_ack(method.delivery_tag)
                disseminate()
                dispatch()
            except Exception:
                logger.warning("Worker cycle failed; pending work will be retried")
                if options["once"]:
                    raise
            if options["once"]:
                break
            time.sleep(5)
