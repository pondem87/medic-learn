import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from medic_learn.accounts.domain import AccountError
from medic_learn.accounts.models import User
from medic_learn.accounts.services import account_action, profile_action, register
from medic_learn.events.models import Outbox
from medic_learn.verification.models import Control, Proof
from medic_learn.verification.services import issue, verify

pytestmark = pytest.mark.django_db


def account(email="learner@example.com", state="registered"):
    user = register(email, "A-long-private-phrase-214!", "Learner", "learner")
    user.state = state
    user.save()
    return user


def code():
    return re.search(r"\b[0-9]{5}\b", mail.outbox[-1].body).group()


def test_registration_uniqueness_and_role():
    user = account("Learner@Example.com")
    assert user.email == "learner@example.com"
    assert user.check_password("A-long-private-phrase-214!")
    assert user.profile.validation == "unvalidated"
    with pytest.raises(AccountError):
        account()
    with pytest.raises(AccountError):
        register("staff@example.com", "A-long-private-phrase-214!", "Staff", "staff")


def test_verification_replacement_attempts_and_atomic_event():
    user = account()
    issue(user)
    old = code()
    issue(user)
    current = code()
    assert Proof.objects.filter(state="replaced").count() == 1
    with pytest.raises(AccountError):
        verify(user, "not-a-code")
    assert Proof.objects.get(state="ready").attempts == 1
    verify(user, current)
    user.refresh_from_db()
    assert user.state == "verified"
    assert Outbox.objects.filter(topic="users.verified").count() == 1
    with pytest.raises(AccountError):
        verify(user, current)
    assert all(
        current not in str(x.payload) and old not in str(x.payload) for x in Outbox.objects.all()
    )


def test_expired_and_exhausted_codes():
    user = account()
    issue(user)
    value = code()
    Proof.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(AccountError):
        verify(user, value)
    issue(user)
    value = code()
    for _ in range(5):
        with pytest.raises(AccountError):
            verify(user, "invalid")
    with pytest.raises(AccountError):
        verify(user, value)


def test_generation_block_persists():
    user = account()
    for _ in range(5):
        issue(user)
    with pytest.raises(AccountError):
        issue(user)
    assert Control.objects.get(user=user).blocked_until > timezone.now()


def test_profile_review_and_state_restoration():
    user = account(state="verified")
    staff = User.objects.create_superuser("staff@example.com", "secret")
    profile_action(user, user.pk, "submit")
    with pytest.raises(AccountError):
        profile_action(user, user.pk, "validate")
    profile_action(staff, user.pk, "review")
    profile_action(staff, user.pk, "validate")
    user.profile.refresh_from_db()
    assert user.profile.validation == "validated"
    account_action(staff, user.pk, "suspended")
    account_action(staff, user.pk, "disabled")
    user = account_action(staff, user.pk, "restore")
    assert user.state == "verified"
    account_action(staff, user.pk, "deleted")
    with pytest.raises(AccountError):
        account_action(staff, user.pk, "restore")
    with pytest.raises(AccountError):
        account_action(staff, staff.pk, "disabled")


def test_jwt_scope_block_and_refresh_rotation():
    user = account()
    api = APIClient()
    response = api.post(
        "/api/v1/auth/token/", {"email": user.email, "password": "A-long-private-phrase-214!"}
    )
    assert response.status_code == 200
    tokens = response.json()
    api.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access"])
    assert api.get("/api/v1/me/").status_code == 403
    issue(user)
    assert api.post("/api/v1/auth/verify/", {"code": code()}).status_code == 200
    assert api.get("/api/v1/me/").status_code == 200
    refreshed = api.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]})
    assert refreshed.status_code == 200
    assert (
        api.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]}).status_code == 401
    )
    staff = User.objects.create_superuser("staff@example.com", "secret")
    account_action(staff, user.pk, "suspended")
    assert api.get("/api/v1/me/").status_code == 401
    account_action(staff, user.pk, "restore")
    assert api.get("/api/v1/me/").status_code == 401
    assert (
        api.post(
            "/api/v1/auth/token/refresh/", {"refresh": refreshed.json()["refresh"]}
        ).status_code
        == 401
    )


def test_web_session_invalidation_and_csrf(client):
    user = account(state="verified")
    client.force_login(user)
    assert client.get("/profile/").status_code == 200
    staff = User.objects.create_superuser("staff@example.com", "secret")
    account_action(staff, user.pk, "suspended")
    account_action(staff, user.pk, "restore")
    assert client.get("/profile/").status_code == 302
    from django.test import Client

    browser = Client(enforce_csrf_checks=True)
    assert browser.post("/register/", {}).status_code == 403


def test_activation_rolls_back_when_outbox_fails():
    from unittest.mock import patch

    user = account()
    issue(user)
    value = code()
    with patch("medic_learn.events.services.enqueue", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            verify(user, value)
    user.refresh_from_db()
    proof = Proof.objects.get(state="ready")
    assert user.state == "registered"
    assert proof.attempts == 1
    verify(user, value)


def test_web_signup_and_verification(client):
    response = client.post(
        "/register/",
        {
            "email": "web@example.com",
            "password": "A-long-private-phrase-214!",
            "name": "Web learner",
            "role": "trainer",
        },
    )
    assert response.status_code == 302
    assert response.url == "/verify/"
    assert client.get("/profile/").url == "/verify/"
    response = client.post("/verify/", {"code": code()})
    assert response.url == "/profile/"
    assert client.get("/profile/").status_code == 200


def test_verification_escalation_and_staff_review():
    from medic_learn.verification.services import review

    user = account()
    staff = User.objects.create_superuser("reviewer@example.com", "secret")
    control = Control.objects.create(
        user=user,
        issued_at=[timezone.now().timestamp()] * 5,
        blocks=[(timezone.now() - timedelta(minutes=30)).timestamp()],
    )
    with pytest.raises(AccountError):
        issue(user)
    control.refresh_from_db()
    assert control.review_required
    until = control.blocked_until
    review(staff, user.pk, True)
    control.refresh_from_db()
    assert not control.review_required
    assert control.blocked_until == until
    with pytest.raises(AccountError):
        issue(user)
