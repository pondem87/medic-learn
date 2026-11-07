"""Custom web authentication screens backed by Cognito and database sessions."""

import time

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as session_login
from django.contrib.auth import logout as session_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from . import cognito, services
from .authentication import resolve_identity
from .domain import AccountError
from .forms import CodeForm, ConfirmationForm, EmailForm, LoginForm, RegistrationForm, ResetForm
from .models import User


def cipher():
    try:
        return Fernet(settings.COGNITO_SESSION_KEY.encode())
    except (ValueError, TypeError) as exc:
        raise AccountError(
            "identity_unavailable", "Authentication is not configured.", 503
        ) from exc


def encrypt(value):
    return cipher().encrypt(value.encode()).decode()


def decrypt(value):
    try:
        return cipher().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise AccountError("session_expired", "Sign in again to continue.", 401) from exc


def screen(request, form, title, template="accounts/auth.html", **context):
    return render(request, template, {"form": form, "title": title, **context})


def finish(request, result):
    if "AuthenticationResult" not in result:
        challenge = result.get("ChallengeName")
        if challenge != "SOFTWARE_TOKEN_MFA":
            raise AccountError("unsupported_challenge", "Contact support to complete sign-in.")
        request.session["challenge"] = encrypt(result["Session"])
        request.session["challenge_until"] = time.time() + 180
        request.session["challenge_username"] = result.get("ChallengeParameters", {}).get(
            "USER_ID_FOR_SRP", request.session["login_email"]
        )
        return redirect("mfa-challenge")
    tokens = result["AuthenticationResult"]
    claims = cognito.verify_access(tokens["AccessToken"], settings.COGNITO_WEB_CLIENT_ID)
    user = resolve_identity(tokens["AccessToken"], claims)
    destination = request.session.get("login_next", "/profile/")
    request.session.flush()
    session_login(request, user, backend="medic_learn.accounts.authentication.AccountBackend")
    request.session["cognito_access"] = encrypt(tokens["AccessToken"])
    request.session["cognito_refresh"] = encrypt(tokens.get("RefreshToken", ""))
    request.session["cognito_expiry"] = time.time() + tokens.get("ExpiresIn", 300)
    request.session["authenticated_at"] = claims["auth_time"]
    request.session["active_role"] = "learner"
    with transaction.atomic():
        services.audit(user, user, "session.login")
    return redirect(destination)


@sensitive_post_parameters("password")
def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.rate_limit(request.META.get("REMOTE_ADDR", ""), "signup_ip")
            services.register(**form.cleaned_data)
            request.session["confirmation_email"] = form.cleaned_data["email"].lower()
            return redirect("verify")
        except AccountError as exc:
            form.add_error(None, exc.message)
    return screen(request, form, "Create account")


@sensitive_post_parameters("password")
def login(request):
    form = LoginForm(request.POST or None)
    destination = request.POST.get("next", request.GET.get("next", "/profile/"))
    if not url_has_allowed_host_and_scheme(
        destination, {request.get_host()}, require_https=request.is_secure()
    ):
        destination = "/profile/"
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        try:
            cipher()  # Fail before contacting Cognito if secret storage is unavailable.
            services.rate_limit(email, "login")
            services.rate_limit(request.META.get("REMOTE_ADDR", ""), "login_ip")
            request.session["login_email"], request.session["login_next"] = email, destination
            return finish(request, cognito.authenticate(email, form.cleaned_data["password"]))
        except AccountError as exc:
            if exc.code == "confirmation_required":
                request.session["confirmation_email"] = email
                return redirect("verify")
            form.add_error(None, exc.message)
    return screen(request, form, "Sign in", next=destination)


@sensitive_post_parameters("code")
def verify(request):
    form = ConfirmationForm(
        request.POST or None, initial={"email": request.session.get("confirmation_email", "")}
    )
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        try:
            services.rate_limit(email, "confirm")
            cognito.call(
                "confirm_sign_up",
                **cognito.public_args(email),
                ConfirmationCode=form.cleaned_data["code"],
            )
            messages.success(request, "Email confirmed. Sign in to complete your profile.")
            return redirect("login")
        except AccountError as exc:
            form.add_error(None, exc.message)
    return screen(request, form, "Confirm email", template="accounts/confirm.html")


@require_POST
def resend(request):
    form = EmailForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"].lower()
        try:
            services.rate_limit(email, "resend")
            cognito.call("resend_confirmation_code", **cognito.public_args(email))
        except AccountError:
            pass  # Identical response prevents account enumeration.
    messages.info(request, "If confirmation is available, a new code will be sent.")
    return redirect("verify")


def forgot(request):
    form = EmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        try:
            services.rate_limit(email, "forgot")
            cognito.call("forgot_password", **cognito.public_args(email))
        except AccountError:
            pass
        request.session["confirmation_email"] = email
        messages.info(request, "If recovery is available, a reset code will be sent.")
        return redirect("reset-password")
    return screen(request, form, "Forgot password")


@sensitive_post_parameters("password", "code")
def reset(request):
    form = ResetForm(
        request.POST or None, initial={"email": request.session.get("confirmation_email", "")}
    )
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        try:
            services.rate_limit(email, "reset")
            cognito.call(
                "confirm_forgot_password",
                **cognito.public_args(email),
                ConfirmationCode=form.cleaned_data["code"],
                Password=form.cleaned_data["password"],
            )
            with transaction.atomic():
                user = User.objects.select_for_update().filter(email=email).first()
                if user:
                    user.credential_version += 1
                    user.credentials_valid_after = timezone.now()
                    user.save()
                    services.audit(None, user, "password.reset")
            session_logout(request)
            messages.success(request, "Password reset. Sign in with your new password.")
            return redirect("login")
        except AccountError as exc:
            form.add_error(None, exc.message)
    return screen(request, form, "Reset password")


@sensitive_post_parameters("code")
def mfa_challenge(request):
    form = CodeForm(request.POST or None)
    if time.time() > request.session.get("challenge_until", 0):
        return redirect("login")
    if request.method == "POST" and form.is_valid():
        try:
            username = request.session["challenge_username"]
            services.rate_limit(username, "mfa_challenge")
            return finish(
                request,
                cognito.challenge(
                    username,
                    decrypt(request.session["challenge"]),
                    "SOFTWARE_TOKEN_MFA",
                    form.cleaned_data["code"],
                ),
            )
        except AccountError as exc:
            form.add_error(None, exc.message)
    return screen(request, form, "Authenticator code")


def access_token(request):
    if not request.session.get("cognito_access"):
        raise AccountError("session_expired", "Sign in again to manage security settings.")
    if request.session.get("cognito_expiry", 0) <= time.time() + 15:
        result = cognito.call(
            "get_tokens_from_refresh_token",
            ClientId=settings.COGNITO_WEB_CLIENT_ID,
            ClientSecret=settings.COGNITO_WEB_CLIENT_SECRET,
            RefreshToken=decrypt(request.session["cognito_refresh"]),
        )["AuthenticationResult"]
        request.session["cognito_access"] = encrypt(result["AccessToken"])
        if "RefreshToken" in result:
            request.session["cognito_refresh"] = encrypt(result["RefreshToken"])
        request.session["cognito_expiry"] = time.time() + result["ExpiresIn"]
    return decrypt(request.session["cognito_access"])


@login_required
@sensitive_post_parameters("code")
def mfa_setup(request):
    form = CodeForm(request.POST or None)
    secret = ""
    try:
        if time.time() - request.session.get("authenticated_at", 0) > 300:
            raise AccountError("reauthenticate", "Sign in again before changing MFA settings.")
        if request.method == "POST":
            token = access_token(request)
            services.rate_limit(str(request.user.pk), "mfa_setup")
            if request.POST.get("action") == "begin":
                result = cognito.call("associate_software_token", AccessToken=token)
                request.session["totp_secret"] = encrypt(result["SecretCode"])
            elif form.is_valid() and request.session.get("totp_secret"):
                result = cognito.call(
                    "verify_software_token", AccessToken=token, UserCode=form.cleaned_data["code"]
                )
                if result["Status"] != "SUCCESS":
                    raise AccountError("invalid_code", "The authenticator code was not accepted.")
                cognito.call(
                    "set_user_mfa_preference",
                    AccessToken=token,
                    SoftwareTokenMfaSettings={"Enabled": True, "PreferredMfa": True},
                )
                request.session.pop("totp_secret", None)
                services.audit(request.user, request.user, "mfa.enabled")
                messages.success(request, "Authenticator MFA enabled.")
                return redirect("profile")
        if request.session.get("totp_secret"):
            secret = decrypt(request.session["totp_secret"])
    except AccountError as exc:
        form.add_error(None, exc.message)
    response = screen(
        request, form, "Set up authenticator", template="accounts/mfa.html", secret=secret
    )
    response["Cache-Control"] = "no-store"
    return response


@require_POST
def logout(request):
    token = request.session.get("cognito_refresh")
    if request.user.is_authenticated:
        services.audit(request.user, request.user, "session.logout")
    try:
        if token:
            cognito.call(
                "revoke_token",
                ClientId=settings.COGNITO_WEB_CLIENT_ID,
                ClientSecret=settings.COGNITO_WEB_CLIENT_SECRET,
                Token=decrypt(token),
            )
    except AccountError:
        pass  # Local session is always destroyed, including during AWS outages.
    finally:
        session_logout(request)
    return redirect("home")
