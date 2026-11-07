import io
import time
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.db import DatabaseError, transaction
from django.test import Client
from PIL import Image
from rest_framework.test import APIClient

from medic_learn.accounts import cognito, services
from medic_learn.accounts.authentication import AccountBackend, VerifiedRole
from medic_learn.accounts.domain import AccountError
from medic_learn.accounts.models import Activity, Council, Evidence, Operation, User
from medic_learn.accounts.operations import run_pending

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def config(settings, tmp_path):
    settings.COGNITO_ISSUER = "https://cognito-idp.af-south-1.amazonaws.com/test"
    settings.COGNITO_POOL_ID = "test"
    settings.COGNITO_WEB_CLIENT_ID = "web"
    settings.COGNITO_WEB_CLIENT_SECRET = "test-secret"
    settings.COGNITO_MOBILE_CLIENT_ID = "mobile"
    settings.COGNITO_SESSION_KEY = Fernet.generate_key().decode()
    settings.EVIDENCE_ROOT = tmp_path
    settings.EVIDENCE_BUCKET = ""


def account(email="user@example.com", category="professional"):
    user = User.objects.create_user(
        email,
        "unused-password",
        state="verified",
        cognito_subject=email,
        cognito_issuer="https://cognito-idp.af-south-1.amazonaws.com/test",
    )
    user.profile.category, user.profile.name = category, "Person"
    user.profile.save()
    return user


def staff():
    user = account("staff@example.com")
    user.is_staff = True
    user.save()
    return user


def card():
    from django.core.files.uploadedfile import SimpleUploadedFile

    data = io.BytesIO()
    Image.new("RGB", (10, 10)).save(data, "PNG")
    return SimpleUploadedFile("card.png", data.getvalue(), content_type="image/png")


def professional_submission(user):
    council, _ = Council.objects.get_or_create(name="Test Botswana council")
    return services.submit(user, "professional", council.pk, "REG123")


def approve(user, actor):
    p = user.profile
    p.refresh_from_db()
    services.review(actor, user.pk, "review", p.version, "Registry/card review started")
    p.refresh_from_db()
    values = (
        {"registered_name": "Verified Name", "profession": "Nurse"}
        if p.category == "professional"
        else {"registered_name": "Student Name", "programme": "Medicine", "school": "University"}
    )
    return services.review(actor, user.pk, "approve", p.version, "Source checked", values)


def test_registration_cognito_and_no_local_password():
    with patch.object(cognito, "signup", return_value={"UserSub": "subject"}) as signup:
        user = services.register("TEST@Example.com", "Password", "Name", "student")
    signup.assert_called_once_with("test@example.com", "Password", "Name")
    assert not user.has_usable_password()
    assert user.profile.category == "student"
    assert user.state == "registered"
    assert AccountBackend().authenticate(None, username=user.email, password="Password") is None
    with pytest.raises(AccountError):
        services.provision("another-subject", user.email)


def test_first_login_reconciles_interrupted_signup(settings):
    user = services.provision("remote-subject", "new@example.com", "Name")
    assert user.state == "verified"
    assert user.profile.category == ""
    assert services.provision("remote-subject", "new@example.com").pk == user.pk
    assert Activity.objects.filter(action="email.confirmed").count() == 1


def test_review_permissions_concurrency_and_bio_editing():
    user, reviewer = account(), staff()
    profile = professional_submission(user)
    assert services.allowed_roles(user) == []
    with pytest.raises(AccountError):
        services.review(user, user.pk, "review", profile.version, "self")
    approve(user, reviewer)
    user.profile.refresh_from_db()
    assert services.allowed_roles(user) == ["learner", "trainer"]
    services.profile_update(user, {"biography": "My unverified bio", "profession": "Forged"})
    user.profile.refresh_from_db()
    assert user.profile.profession == "Nurse"
    assert user.profile.biography == "My unverified bio"
    with pytest.raises(AccountError, match="changed"):
        services.review(reviewer, user.pk, "update", 1, "stale", {"profession": "Doctor"})
    services.review(
        reviewer, user.pk, "revoke", user.profile.version, "Registration no longer valid"
    )
    user.profile.refresh_from_db()
    assert services.allowed_roles(user) == []
    assert Activity.objects.filter(action="verification.approve", actor=reviewer).exists()


def test_student_evidence_permissions_deletion_and_retry(client):
    user, reviewer = account(category="student"), staff()
    services.submit(user, "student", evidence=card())
    item = Evidence.objects.get()
    client.force_login(user)
    assert client.get(f"/staff/evidence/{item.pk}/").status_code == 403
    client.force_login(reviewer)
    assert client.get(f"/staff/evidence/{item.pk}/").status_code == 200
    approve(user, reviewer)
    user.profile.refresh_from_db()
    assert services.allowed_roles(user) == ["learner"]
    assert client.get(f"/staff/evidence/{item.pk}/").status_code == 404
    with patch("medic_learn.accounts.evidence.delete", side_effect=OSError):
        run_pending()
    assert Operation.objects.get().attempts == 1
    assert Operation.objects.get().completed_at is None
    run_pending()
    item.refresh_from_db()
    assert item.deleted_at


def test_invalid_upload_and_category_change():
    from django.core.files.uploadedfile import SimpleUploadedFile

    user, reviewer = account(), staff()
    with pytest.raises(AccountError):
        services.submit(user, "student", evidence=SimpleUploadedFile("bad.jpg", b"not an image"))
    professional_submission(user)
    approve(user, reviewer)
    services.submit(user, "student", evidence=card())
    user.profile.refresh_from_db()
    assert services.allowed_roles(user) == []
    assert user.profile.profession == ""
    assert user.profile.category == "student"


def test_audit_is_append_only_and_atomic():
    user = account()
    activity = services.audit(user, user, "test")
    with pytest.raises(DatabaseError), transaction.atomic():
        Activity.objects.filter(pk=activity.pk).update(action="tampered")
    with pytest.raises(DatabaseError), transaction.atomic():
        Activity.objects.filter(pk=activity.pk).delete()
    with patch.object(services, "audit", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            services.profile_update(user, {"biography": "Should roll back"})
    user.profile.refresh_from_db()
    assert user.profile.biography == ""


def test_session_invalidation_and_csrf(client):
    user, reviewer = account(), staff()
    client.force_login(user)
    assert client.get("/profile/").status_code == 200
    services.account_action(reviewer, user.pk, "suspended", "Policy")
    services.account_action(reviewer, user.pk, "restore", "Resolved")
    assert client.get("/profile/").status_code == 302
    assert Client(enforce_csrf_checks=True).post("/register/", {}).status_code == 403


def test_mobile_bearer_scope_and_restrictions(settings):
    user, reviewer = account(), staff()
    claims = {
        "iss": settings.COGNITO_ISSUER,
        "sub": user.cognito_subject,
        "auth_time": time.time() - 10,
        "scope": "medic-api/access",
    }
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION="Bearer access-token")
    with patch.object(cognito, "verify_access", return_value=claims):
        assert api.get("/api/v1/me/").status_code == 200
        assert api.patch("/api/v1/me/", {"profession": "Forged"}).status_code == 400
        assert api.patch("/api/v1/me/", {"biography": "Bio"}).status_code == 200
        services.account_action(reviewer, user.pk, "suspended", "Policy")
        services.account_action(reviewer, user.pk, "restore", "Resolved")
        assert api.get("/api/v1/me/").status_code == 401
    assert api.post("/api/v1/auth/token/", {}).status_code == 404


def test_web_login_challenge_and_reset(client, settings):
    user = account()
    claims = {"iss": settings.COGNITO_ISSUER, "sub": user.cognito_subject, "auth_time": time.time()}
    result = {
        "AuthenticationResult": {
            "AccessToken": "ACCESS",
            "RefreshToken": "REFRESH",
            "ExpiresIn": 300,
        }
    }
    with patch.object(
        cognito,
        "authenticate",
        return_value={"ChallengeName": "SOFTWARE_TOKEN_MFA", "Session": "challenge"},
    ):
        response = client.post("/login/", {"email": user.email, "password": "Password"})
    assert response.url == "/mfa/challenge/"
    assert "_auth_user_id" not in client.session
    assert "challenge" != client.session["challenge"]
    with (
        patch.object(cognito, "challenge", return_value=result),
        patch.object(cognito, "verify_access", return_value=claims),
    ):
        response = client.post("/mfa/challenge/", {"code": "123456"})
    assert response.url == "/profile/"
    assert client.session["cognito_access"] != "ACCESS"
    with patch.object(cognito, "call", return_value={}):
        response = client.post(
            "/password/reset/",
            {"email": user.email, "code": "123456", "password": "NewPassword123!"},
        )
    assert response.url == "/login/"
    user.refresh_from_db()
    assert user.credentials_valid_after


def test_staff_mfa_reset_and_provider_outage():
    user, reviewer = account(), staff()
    with pytest.raises(AccountError):
        services.request_mfa_reset(reviewer, reviewer.pk, "self")
    services.request_mfa_reset(reviewer, user.pk, "Identity checked against registry")
    with patch.object(cognito, "call", side_effect=AccountError("outage", "Unavailable", 503)):
        run_pending()
    assert Operation.objects.get().completed_at is None
    with patch.object(cognito, "call", return_value={}) as remote:
        run_pending()
    assert remote.call_count == 2
    assert Operation.objects.get().completed_at


def test_rate_limit():
    for _ in range(10):
        services.rate_limit("person", "login")
    with pytest.raises(AccountError) as error:
        services.rate_limit("person", "login")
    assert error.value.status == 429


def test_role_switch_is_per_session(client):
    user, reviewer = account(), staff()
    professional_submission(user)
    approve(user, reviewer)
    a, b = client, Client()
    a.force_login(user)
    b.force_login(user)
    assert a.post("/profile/role/", {"role": "trainer"}).status_code == 302
    assert a.session["active_role"] == "trainer"
    assert b.session.get("active_role", "learner") == "learner"
    assert a.post("/profile/role/", {"role": "staff"}).status_code == 302
    assert a.session["active_role"] == "trainer"


def test_signed_access_tokens_reject_wrong_identity_and_expiry(settings):
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    claims = {
        "iss": settings.COGNITO_ISSUER,
        "sub": "sub",
        "auth_time": int(time.time()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
        "token_use": "access",
        "client_id": "mobile",
    }

    class SigningKey:
        pass

    signing_key = SigningKey()
    signing_key.key = key.public_key()
    with patch.object(cognito, "jwks") as keys:
        keys.return_value.get_signing_key_from_jwt.return_value = signing_key
        assert (
            cognito.verify_access(jwt.encode(claims, key, algorithm="RS256"), "mobile")["sub"]
            == "sub"
        )
        for change in [
            {"token_use": "id"},
            {"iss": "https://wrong"},
            {"client_id": "web"},
            {"exp": 1},
        ]:
            with pytest.raises(AccountError):
                cognito.verify_access(
                    jwt.encode({**claims, **change}, key, algorithm="RS256"), "mobile"
                )


def test_mfa_setup_requires_fresh_login_and_never_audits_secret(client):
    user = account()
    client.force_login(user)
    session = client.session
    session["authenticated_at"] = time.time()
    session.save()
    with (
        patch("medic_learn.accounts.web_auth.access_token", return_value="token"),
        patch.object(cognito, "call", return_value={"SecretCode": "PRIVATE-TOTP-SEED"}),
    ):
        response = client.post("/mfa/setup/", {"action": "begin"})
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert client.session["totp_secret"] != "PRIVATE-TOTP-SEED"
    with (
        patch("medic_learn.accounts.web_auth.access_token", return_value="token"),
        patch.object(cognito, "call", side_effect=[{"Status": "SUCCESS"}, {}]),
    ):
        assert client.post("/mfa/setup/", {"code": "123456"}).url == "/profile/"
    assert "totp_secret" not in client.session
    assert Activity.objects.filter(action="mfa.enabled").exists()
    assert "PRIVATE-TOTP-SEED" not in str(list(Activity.objects.values()))
    session = client.session
    session["authenticated_at"] = time.time() - 301
    session.save()
    with patch.object(cognito, "call") as remote:
        response = client.post("/mfa/setup/", {"action": "begin"})
    remote.assert_not_called()
    assert b"Sign in again" in response.content


def test_provider_errors_do_not_disclose_details():
    from botocore.exceptions import ClientError

    with patch.object(cognito, "client") as provider:
        provider.return_value.initiate_auth.side_effect = ClientError(
            {"Error": {"Code": "InternalErrorException", "Message": "sensitive detail"}},
            "InitiateAuth",
        )
        with pytest.raises(AccountError) as error:
            cognito.authenticate("person@example.com", "secret")
    assert error.value.status == 503
    assert "sensitive" not in error.value.message


def test_signup_confirmation_and_resend(client):
    with patch.object(cognito, "signup", return_value={"UserSub": "new-sub"}):
        response = client.post(
            "/register/",
            {
                "email": "new@example.com",
                "password": "Password123!",
                "name": "New",
                "category": "student",
            },
        )
    assert response.url == "/verify/"
    assert "_auth_user_id" not in client.session
    with patch.object(cognito, "call", return_value={}) as remote:
        response = client.post("/verify/", {"email": "new@example.com", "code": "123456"})
    assert response.url == "/login/"
    assert remote.call_args.args == ("confirm_sign_up",)
    with patch.object(cognito, "call", side_effect=AccountError("unavailable", "No such user")):
        response = client.post("/verify/resend/", {"email": "unknown@example.com"})
    assert response.url == "/verify/"


def test_failed_upload_attachment_is_cleanup_addressable():
    from datetime import timedelta

    from django.utils import timezone

    from medic_learn.accounts import evidence as storage

    user = account(category="student")
    item = storage.upload(user, card())
    Evidence.objects.filter(pk=item.pk).update(created_at=timezone.now() - timedelta(hours=2))
    run_pending()
    item.refresh_from_db()
    assert not item.available
    assert item.deleted_at


def test_mobile_role_permission_checks_current_status():
    from types import SimpleNamespace

    user, reviewer = account(category="student"), staff()
    request = SimpleNamespace(user=user, headers={"X-Active-Role": "learner"})
    assert not VerifiedRole().has_permission(request, None)
    services.submit(user, "student", evidence=card())
    approve(user, reviewer)
    user.profile.refresh_from_db()
    assert VerifiedRole().has_permission(request, None)
    request.headers["X-Active-Role"] = "trainer"
    assert not VerifiedRole().has_permission(request, None)


def test_bearer_missing_scope_and_malformed_header():
    user = account()
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION="Bearer token")
    with patch.object(cognito, "verify_access", return_value={"scope": "openid"}):
        assert api.get("/api/v1/me/").status_code == 401
    api.credentials(HTTP_AUTHORIZATION="Bearer token extra")
    assert api.get("/api/v1/me/").status_code == 401
    assert user.state == "verified"


def test_return_retains_card_rejection_deletes_and_resubmission_allowed():
    user, reviewer = account(category="student"), staff()
    p = services.submit(user, "student", evidence=card())
    services.review(reviewer, user.pk, "return", p.version, "Card unreadable")
    assert Evidence.objects.get().available
    p = services.submit(user, "student", evidence=card())
    assert Evidence.objects.filter(available=True).count() == 1
    services.review(reviewer, user.pk, "reject", p.version, "Card does not establish enrollment")
    assert not Evidence.objects.filter(available=True).exists()
    assert services.submit(user, "student", evidence=card()).validation == "submitted"


def test_restoring_unconfirmed_account_enables_cognito():
    user, reviewer = account(), staff()
    user.state = "registered"
    user.save()
    services.account_action(reviewer, user.pk, "suspended", "Pause signup")
    services.account_action(reviewer, user.pk, "restore", "Resume signup")

    def remote(operation, **kwargs):
        if operation == "admin_user_global_sign_out":
            raise AccountError("confirmation_required", "Confirm first")
        return {}

    with patch.object(cognito, "call", side_effect=remote) as provider:
        run_pending()
    assert any(call.args[0] == "admin_enable_user" for call in provider.call_args_list)
    assert not Operation.objects.filter(completed_at=None).exists()


def test_logout_clears_session_even_when_cognito_is_unavailable(client):
    from medic_learn.accounts.web_auth import encrypt

    user = account()
    client.force_login(user)
    session = client.session
    session["cognito_refresh"] = encrypt("refresh-token")
    session.save()
    with patch.object(cognito, "call", side_effect=AccountError("outage", "Unavailable", 503)):
        assert client.post("/logout/").url == "/"
    assert "_auth_user_id" not in client.session
