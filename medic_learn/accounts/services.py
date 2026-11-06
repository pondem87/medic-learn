from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction

from .domain import AccountError, AccountState
from .models import Profile, User
from .repositories import locked_account


def register(email, password, name, role):
    if role not in {"learner", "trainer"}:
        raise AccountError("invalid_role", "Choose learner or trainer.")
    validate_password(password, User(email=email))
    try:
        with transaction.atomic():
            user = User.objects.create_user(email, password)
            Profile.objects.filter(user=user).update(name=name, role=role)
    except IntegrityError as exc:
        raise AccountError(
            "registration_unavailable", "Registration could not be completed."
        ) from exc
    return user


def require_staff(actor):
    if actor.state != "verified" or actor.profile.role != "staff":
        raise AccountError("forbidden", "Staff access required.", 403)


def profile_update(user, values):
    with transaction.atomic():
        profile = Profile.objects.select_for_update().get(user=user)
        if profile.validation != "unvalidated":
            raise AccountError("invalid_state", "Only unvalidated profiles can be edited.")
        for field in ["name", "phone", "biography", "notifications_enabled"]:
            if field in values:
                setattr(profile, field, values[field])
        profile.full_clean()
        profile.save()
        return profile


def profile_action(actor, target_id, action, reason="", role=""):
    with transaction.atomic():
        target = locked_account(target_id)
        profile = Profile.objects.select_for_update().get(user=target)
        if action == "submit":
            if (
                actor.pk != target.pk
                or profile.validation != "unvalidated"
                or not profile.name.strip()
            ):
                raise AccountError("invalid_state", "Profile cannot be submitted.")
            profile.validation = "submitted"
        else:
            require_staff(actor)
            if actor.pk == target.pk:
                raise AccountError(
                    "forbidden", "Self review and role assignment are unavailable.", 403
                )
            if action == "role" and role in {"staff", "trainer", "learner"}:
                profile.role = role
            elif action == "review" and profile.validation == "submitted":
                profile.validation = "pending"
            elif action == "validate" and profile.validation == "pending":
                profile.validation = "validated"
            elif (
                action == "return"
                and profile.validation in {"submitted", "pending"}
                and reason.strip()
            ):
                profile.validation, profile.review_reason = "unvalidated", reason
            else:
                raise AccountError("invalid_state", "Review transition unavailable.")
        profile.save()
        return profile


def account_action(actor, target_id, action):
    require_staff(actor)
    if actor.pk == target_id:
        raise AccountError("forbidden", "Cannot block your own account.", 403)
    with transaction.atomic():
        user = locked_account(target_id)
        state = AccountState(user.state, user.previous_state).transition(action)
        user.state, user.previous_state = state.state, state.previous
        user.credential_version += 1
        user.save()
        return user


def communication_recipient(user_id):
    """Return the current email and optional-notification eligibility."""
    user = User.objects.select_related("profile").get(pk=user_id)
    return user.email, user.state == "verified" and user.profile.notifications_enabled
