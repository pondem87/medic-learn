"""Serialize durable external work per account, recording safe outcomes."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from . import cognito, evidence, services
from .domain import AccountError
from .models import Evidence, Operation, User


def run_pending():
    # Recover uploads interrupted between object storage and submission commit.
    stale = Evidence.objects.filter(
        created_at__lt=timezone.now() - timedelta(hours=1), deleted_at=None
    )
    for item in stale:
        if (
            not item.attached
            or not item.available
            or item.user.profile.validation
            not in {
                "submitted",
                "pending",
                "unvalidated",
            }
        ):
            with transaction.atomic():
                item.available = False
                item.save(update_fields=["available"])
                if not Operation.objects.filter(
                    kind="delete_evidence", payload={"id": str(item.pk)}, completed_at=None
                ).exists():
                    Operation.objects.create(
                        user=item.user, kind="delete_evidence", payload={"id": str(item.pk)}
                    )
    for operation_id in (
        Operation.objects.filter(completed_at=None)
        .order_by("pk")
        .values_list("pk", flat=True)[:100]
    ):
        with transaction.atomic():
            task = (
                Operation.objects.select_for_update(skip_locked=True)
                .filter(pk=operation_id, completed_at=None)
                .first()
            )
            if task is None:
                continue
            # Explicit bounded external I/O while locked prevents stale enable/disable ordering.
            user = User.objects.select_for_update().get(pk=task.user_id)
            task.attempts += 1
            try:
                args = {"UserPoolId": settings.COGNITO_POOL_ID, "Username": user.cognito_subject}
                if task.kind == "delete_evidence":
                    record = Evidence.objects.get(pk=task.payload["id"], user=user)
                    evidence.delete(record)
                    record.deleted_at = timezone.now()
                    record.available = False
                    record.save()
                elif user.cognito_subject:
                    try:
                        cognito.call("admin_user_global_sign_out", **args)
                    except AccountError as exc:
                        if exc.code != "confirmation_required":
                            raise
                        # Unconfirmed users have no sessions to revoke.

                    if task.kind == "sync_access":
                        cognito.call(
                            "admin_enable_user"
                            if user.state in {"registered", "verified"}
                            else "admin_disable_user",
                            **args,
                        )
                    elif task.kind == "reset_mfa":
                        cognito.call(
                            "admin_set_user_mfa_preference",
                            **args,
                            SoftwareTokenMfaSettings={"Enabled": False, "PreferredMfa": False},
                        )
                    else:
                        raise ValueError("Unknown operation")
                if task.kind in {"sync_access", "reset_mfa"}:
                    user.credential_version += 1
                    user.credentials_valid_after = timezone.now()
                    user.save(update_fields=["credential_version", "credentials_valid_after"])
                task.completed_at, task.last_error = timezone.now(), ""
                services.audit(
                    None,
                    user,
                    "operation.completed",
                    after={"operation": task.pk, "kind": task.kind},
                )
            except Exception:
                task.last_error = "external_operation_failed"
                if task.attempts == 1:
                    services.audit(
                        None,
                        user,
                        "operation.retry_pending",
                        after={"operation": task.pk, "kind": task.kind},
                    )
            task.save()
