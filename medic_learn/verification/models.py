import uuid

from django.conf import settings
from django.db import models


class Control(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    issued_at = models.JSONField(default=list)
    blocks = models.JSONField(default=list)
    blocked_until = models.DateTimeField(null=True)
    review_required = models.BooleanField(default=False)


class Proof(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    verifier = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    state = models.CharField(max_length=10, default="ready")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"], condition=models.Q(state="ready"), name="one_ready_email_proof"
            )
        ]
