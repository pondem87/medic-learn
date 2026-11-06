import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from medic_learn.events.models import Outbox


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    if not settings.WHATSAPP_ENABLED:
        return HttpResponse(status=404)
    if request.method == "GET":
        if (
            settings.WHATSAPP_VERIFY_TOKEN
            and request.GET.get("hub.mode") == "subscribe"
            and hmac.compare_digest(
                request.GET.get("hub.verify_token", ""), settings.WHATSAPP_VERIFY_TOKEN
            )
        ):
            return HttpResponse(request.GET.get("hub.challenge", ""))
        return HttpResponse(status=403)
    if len(request.body) > 1048576:
        return HttpResponse(status=413)
    expected = (
        "sha256="
        + hmac.new(settings.WHATSAPP_APP_SECRET.encode(), request.body, hashlib.sha256).hexdigest()
    )
    if not settings.WHATSAPP_APP_SECRET or not hmac.compare_digest(
        expected, request.headers.get("X-Hub-Signature-256", "")
    ):
        return HttpResponse(status=403)
    try:
        body = json.loads(request.body)
        observations = []
        for entry in body["entry"]:
            for change in entry["changes"]:
                value = change["value"]
                if value["metadata"]["phone_number_id"] != settings.WHATSAPP_PHONE_ID:
                    return HttpResponse(status=403)
                observations.append(value)
        with transaction.atomic():
            for value in observations:
                identity = uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(value, sort_keys=True))
                Outbox.objects.get_or_create(
                    id=identity, defaults={"topic": "channels.observation", "payload": value}
                )
    except (KeyError, ValueError, TypeError):
        return HttpResponse(status=400)
    return HttpResponse(status=200)
