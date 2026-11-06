import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from medic_learn.accounts.domain import AccountError
from medic_learn.accounts.repositories import locked_account
from medic_learn.accounts.services import require_staff

from .models import Control, Proof


def digest(proof_id, user_id, code):
    return hmac.new(
        settings.PROOF_KEY.encode(), f"email:{proof_id}:{user_id}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def issue(user):
    now = timezone.now()
    failure = None
    with transaction.atomic():
        account = locked_account(user.pk)
        if account.state != "registered":
            raise AccountError("invalid_state", "Account is not awaiting verification.")
        control, _ = Control.objects.get_or_create(user=account)
        if control.review_required or (control.blocked_until and control.blocked_until > now):
            raise AccountError("issuance_blocked", "Verification issuance is blocked.", 429)
        recent = [x for x in control.issued_at if x > (now - timedelta(minutes=10)).timestamp()]
        if len(recent) >= 5:
            control.blocks = [
                x for x in control.blocks if x > (now - timedelta(hours=24)).timestamp()
            ] + [now.timestamp()]
            control.blocked_until = now + timedelta(minutes=10)
            control.review_required = len(control.blocks) >= 2
            control.save()
            failure = AccountError("issuance_blocked", "Verification issuance is blocked.", 429)
        else:
            Proof.objects.filter(user=account, state="ready").update(state="replaced")
            code = f"{secrets.randbelow(100000):05d}"
            proof_id = uuid.uuid4()
            Proof.objects.create(
                id=proof_id,
                user=account,
                verifier=digest(proof_id, account.pk, code),
                expires_at=now + timedelta(minutes=10),
            )
            control.issued_at = recent + [now.timestamp()]
            control.save()
    if failure:
        raise failure
    from medic_learn.messages.services import confidential_email

    return confidential_email(account.email, code)


def verify(user, code):
    # Reserve the attempt independently so invalid submissions survive rollback.
    with transaction.atomic():
        account = locked_account(user.pk)
        if account.state != "registered":
            raise AccountError("invalid_state", "Account is not awaiting verification.")
        proof = Proof.objects.select_for_update().filter(user=account, state="ready").first()
        if not proof or proof.expires_at <= timezone.now() or proof.attempts >= 5:
            raise AccountError("invalid_code", "Code is invalid or expired.")
        proof.attempts += 1
        proof.save(update_fields=["attempts"])
        proof_id = proof.id
    with transaction.atomic():
        account = locked_account(user.pk)
        proof = Proof.objects.select_for_update().get(pk=proof_id)
        if (
            account.state != "registered"
            or proof.state != "ready"
            or proof.expires_at <= timezone.now()
            or not hmac.compare_digest(proof.verifier, digest(proof.id, account.pk, code))
        ):
            raise AccountError("invalid_code", "Code is invalid or expired.")
        proof.state = "used"
        proof.save(update_fields=["state"])
        account.state = "verified"
        account.save(update_fields=["state"])
        from medic_learn.events.services import enqueue

        enqueue("users.verified", {"user_id": str(account.pk)})


def review(actor, user_id, approve):
    require_staff(actor)
    if actor.pk == user_id:
        raise AccountError("forbidden", "Cannot review your own verification controls.", 403)
    with transaction.atomic():
        account = locked_account(user_id)
        control = Control.objects.filter(user=account).first()
        if control is None:
            raise AccountError("invalid_state", "No verification review is pending.")
        if account.state != "registered" or not control.review_required:
            raise AccountError("invalid_state", "No verification review is pending.")
        if approve:
            control.review_required = False
            control.blocks = []
            control.save()
        else:
            account.previous_state = account.state
            account.state = "disabled"
            account.credential_version += 1
            account.save()
