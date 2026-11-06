import uuid

from django.conf import settings
from django.db import models


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    channel = models.CharField(max_length=12, default="email")
    recipient = models.CharField(max_length=254)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    state = models.CharField(max_length=16, default="queued")
    provider_id = models.CharField(max_length=200, blank=True)


class Observation(models.Model):
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
