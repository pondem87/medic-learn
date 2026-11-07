from unittest.mock import Mock, patch

from django.core.mail import EmailMessage
from django.test import override_settings

from medic_learn.events.services import connection, topology
from medic_learn.messages.ses_backend import EmailBackend


def test_health_probe_does_not_require_authentication(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@override_settings(RABBITMQ_URL="amqps://medic:secret@broker.example.com:5671/%2F")
def test_managed_broker_tls_verifies_server_name():
    with patch("pika.BlockingConnection") as connect:
        connection()
    params = connect.call_args.args[0]
    assert params.ssl_options.server_hostname == "broker.example.com"
    assert params.ssl_options.context.check_hostname
    assert params.ssl_options.context.verify_mode == 2


@override_settings(RABBITMQ_QUEUE_TYPE="quorum")
def test_managed_broker_uses_quorum_queues():
    channel = Mock()
    topology(channel)
    declarations = channel.queue_declare.call_args_list
    assert all(call.kwargs["arguments"]["x-queue-type"] == "quorum" for call in declarations)
    assert declarations[1].kwargs["arguments"]["x-dead-letter-exchange"] == "medic.dead"


@override_settings(SES_REGION="af-south-1")
def test_ses_backend_reports_acceptance_without_duplicate_retry():
    with patch("medic_learn.messages.ses_backend.boto3.client") as client:
        message = EmailMessage("Welcome", "Hello", "sender@example.com", ["recipient@example.com"])
        assert EmailBackend().send_messages([message]) == 1
    assert client.call_args.kwargs["config"].retries["max_attempts"] == 0
    assert client.return_value.send_raw_email.call_args.kwargs["Destinations"] == [
        "recipient@example.com"
    ]
