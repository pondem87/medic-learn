"""Account use cases: local policy is independent of the identity provider."""

import hashlib
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .domain import AccountError, AccountState
from .models import Activity, AuthAttempt, Council, Evidence, Operation, Profile, User

EDITABLE = ("name", "phone", "biography", "notifications_enabled")
VERIFIED_FIELDS = (
    "registered_name",
    "council_id",
    "registration_number",
    "profession",
    "programme",
    "school",
)


def audit(actor, subject, action, reason="", before=None, after=None):
    return Activity.objects.create(
        actor=actor,
        subject=subject,
        action=action,
        reason=reason,
        before=before or {},
        after=after or {},
    )


def rate_limit(identity, purpose):
    key = hashlib.sha256(f"{purpose}:{identity.lower()}".encode()).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        entry, _ = AuthAttempt.objects.get_or_create(key=key, defaults={"started_at": now})
        entry = AuthAttempt.objects.select_for_update().get(pk=key)
        if entry.started_at < now - timedelta(minutes=10):
            entry.count, entry.started_at = 0, now
        if entry.count >= 10:
            raise AccountError("rate_limited", "Please wait before trying again.", 429)
        entry.count += 1
        entry.save()


def register(email, password, name, category):
    from . import cognito

    if category not in {"professional", "student"}:
        raise AccountError("invalid_category", "Choose professional or student.")
    email = email.strip().lower()
    rate_limit(email, "register")
    result = cognito.signup(email, password, name)
    # Cognito can succeed before the DB write fails. Confirm/login reconciles by sub.
    return provision(result["UserSub"], email, name, category, confirmed=False)


def provision(subject, email, name="", category="", confirmed=True):
    try:
        with transaction.atomic():
            user = (
                User.objects.select_for_update()
                .filter(cognito_issuer=settings.COGNITO_ISSUER, cognito_subject=subject)
                .first()
            )
            if user is None:
                if User.objects.filter(email__iexact=email).exists():
                    raise AccountError(
                        "identity_conflict", "Contact support to link this account.", 409
                    )
                user = User.objects.create_user(
                    email.strip().lower(),
                    cognito_subject=subject,
                    cognito_issuer=settings.COGNITO_ISSUER,
                )
                user.profile.name, user.profile.category = name, category
                user.profile.save()
                audit(None, user, "account.registered")
            if confirmed and user.state == "registered":
                user.state = "verified"
                user.save(update_fields=["state"])
                audit(None, user, "email.confirmed")
                from medic_learn.events.services import enqueue

                enqueue("users.verified", {"user_id": str(user.pk)})
            return user
    except IntegrityError as exc:
        # Concurrent first logins may race; a retry safely discovers the bound identity.
        raise AccountError("identity_conflict", "Please retry signing in.", 409) from exc


def require_staff(actor):
    if not actor.is_active or actor.state != "verified" or not actor.is_staff:
        raise AccountError("forbidden", "Staff access required.", 403)


def allowed_roles(user):
    if not user.is_active or user.state != "verified" or user.profile.validation != "validated":
        return []
    return (
        ["learner", "trainer"]
        if user.profile.category == "professional"
        else (["learner"] if user.profile.category == "student" else [])
    )


def require_role(user, role):
    if role not in allowed_roles(user):
        raise AccountError("forbidden", "Your verified status does not permit this role.", 403)


def profile_update(user, values):
    with transaction.atomic():
        profile = Profile.objects.select_for_update().get(user=user)
        before = {field: getattr(profile, field) for field in EDITABLE if field in values}
        for field in before:
            setattr(profile, field, values[field])
        profile.full_clean()
        profile.save()
        audit(
            user,
            user,
            "profile.updated",
            before=before,
            after={field: getattr(profile, field) for field in before},
        )
        return profile


def submit(user, category, council_id=None, registration_number="", evidence=None):
    from . import evidence as storage

    if user.state != "verified" or category not in {"professional", "student"}:
        raise AccountError("invalid_category", "Choose a category after confirming your email.")
    if category == "professional":
        if (
            not registration_number.strip()
            or not Council.objects.filter(pk=council_id, active=True).exists()
        ):
            raise AccountError("invalid_submission", "Provide a council and registration number.")
    elif evidence is None:
        raise AccountError("invalid_submission", "Upload your student card.")
    uploaded = storage.upload(user, evidence) if category == "student" else None
    try:
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(user=user)
            if profile.validation in {"submitted", "pending"}:
                raise AccountError(
                    "review_in_progress", "Your submission is already being reviewed.", 409
                )
            before = snapshot(profile)
            if uploaded:
                uploaded.attached = True
                uploaded.save(update_fields=["attached"])
            retire_evidence(user, exclude=uploaded.pk if uploaded else None)
            profile.category, profile.validation = category, "submitted"
            for field in VERIFIED_FIELDS:
                setattr(profile, field, None if field == "council_id" else "")
            # Submitted values are claims until staff approval, and are labelled as such.
            profile.council_id = council_id if category == "professional" else None
            profile.registration_number = (
                registration_number.strip() if category == "professional" else ""
            )
            profile.review_reason = ""
            profile.version += 1
            profile.full_clean()
            profile.save()
            audit(user, user, "verification.submitted", before=before, after=snapshot(profile))
            return profile
    except Exception:
        if uploaded:
            with transaction.atomic():
                retire_evidence(user, only=uploaded.pk)
        raise


def snapshot(profile):
    return {
        field: getattr(profile, field)
        for field in (*VERIFIED_FIELDS, "category", "validation", "review_reason", "version")
    }


def retire_evidence(user, exclude=None, only=None):
    items = Evidence.objects.filter(user=user, available=True)
    if exclude:
        items = items.exclude(pk=exclude)
    if only:
        items = items.filter(pk=only)
    for item in items:
        item.available = False
        item.save(update_fields=["available"])
        Operation.objects.create(user=user, kind="delete_evidence", payload={"id": str(item.pk)})


def review(actor, target_id, action, version, reason, values=None):
    require_staff(actor)
    if actor.pk == target_id:
        raise AccountError("forbidden", "You cannot review your own account.", 403)
    if not reason.strip():
        raise AccountError("reason_required", "Record a reason for this action.")
    with transaction.atomic():
        profile = Profile.objects.select_for_update().select_related("user").get(user_id=target_id)
        if profile.version != version:
            raise AccountError("conflict", "This profile changed. Reload before reviewing.", 409)
        before = snapshot(profile)
        transitions = {
            "review": ({"submitted"}, "pending"),
            "approve": ({"pending"}, "validated"),
            "return": ({"submitted", "pending"}, "unvalidated"),
            "reject": ({"submitted", "pending"}, "rejected"),
            "revoke": ({"validated"}, "revoked"),
            "update": ({"validated"}, "validated"),
        }
        if action not in transitions or profile.validation not in transitions[action][0]:
            raise AccountError("invalid_state", "Review transition unavailable.")
        if action in {"approve", "update"}:
            for field in VERIFIED_FIELDS:
                if field in (values or {}):
                    setattr(profile, field, values[field])
            required = ["registered_name"] + (
                ["council_id", "registration_number", "profession"]
                if profile.category == "professional"
                else ["programme", "school"]
            )
            if not all(getattr(profile, field) for field in required):
                raise AccountError("missing_details", "Complete the verified registration details.")
            if (
                action == "approve"
                and profile.category == "student"
                and not Evidence.objects.filter(
                    user=profile.user, available=True, attached=True
                ).exists()
            ):
                raise AccountError("missing_evidence", "Student card evidence is required.")
        profile.validation = transitions[action][1]
        profile.review_reason, profile.version = reason, profile.version + 1
        profile.full_clean()
        profile.save()
        audit(actor, profile.user, "verification." + action, reason, before, snapshot(profile))
        if action in {"approve", "reject"}:
            retire_evidence(profile.user)
        return profile


def account_action(actor, target_id, action, reason=""):
    require_staff(actor)
    if actor.pk == target_id or not reason.strip():
        raise AccountError(
            "forbidden", "A reason is required; you cannot change your own access.", 403
        )
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=target_id)
        before = user.state
        state = AccountState(user.state, user.previous_state).transition(action)
        user.state, user.previous_state = state.state, state.previous
        user.credential_version += 1
        user.credentials_valid_after = timezone.now()
        user.save()
        audit(actor, user, "account." + action, reason, {"state": before}, {"state": user.state})
        Operation.objects.create(user=user, kind="sync_access")
        if action == "deleted":
            retire_evidence(user)
        return user


def request_mfa_reset(actor, target_id, reason):
    require_staff(actor)
    if actor.pk == target_id or not reason.strip():
        raise AccountError(
            "forbidden", "Record an external identity check; self-reset is forbidden.", 403
        )
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=target_id)
        if not user.cognito_subject:
            raise AccountError("identity_missing", "This account has no Cognito identity.")
        user.credential_version += 1
        user.credentials_valid_after = timezone.now()
        user.save()
        audit(actor, user, "mfa.reset_requested", reason)
        Operation.objects.create(user=user, kind="reset_mfa")


def communication_recipient(user_id):
    user = User.objects.select_related("profile").get(pk=user_id)
    return user.email, user.state == "verified" and user.profile.notifications_enabled
