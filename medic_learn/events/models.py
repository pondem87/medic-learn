import uuid

from django.db import models


class Outbox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=100)
    payload = models.JSONField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=False)


class Inbox(models.Model):
    id = models.UUIDField(primary_key=True)
    fingerprint = models.CharField(max_length=64)
