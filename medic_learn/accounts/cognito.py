"""Cognito boundary. Secrets and raw provider errors never escape this adapter."""

import base64
import hashlib
import hmac
from functools import lru_cache

import boto3
import jwt
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.views.decorators.debug import sensitive_variables

from .domain import AccountError


@lru_cache
def client():
    if not settings.COGNITO_POOL_ID or not settings.COGNITO_WEB_CLIENT_ID:
        raise AccountError("identity_unavailable", "Authentication is not configured.", 503)
    from botocore.config import Config

    return boto3.client(
        "cognito-idp",
        region_name=settings.AWS_REGION,
        config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 1}),
    )


@sensitive_variables()
def call(operation, **kwargs):
    try:
        return getattr(client(), operation)(**kwargs)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        mapped = {
            "UserNotConfirmedException": (
                "confirmation_required",
                "Confirm your email before signing in.",
                400,
            ),
            "PasswordResetRequiredException": (
                "reset_required",
                "Reset your password before signing in.",
                400,
            ),
            "CodeMismatchException": ("invalid_code", "The code is invalid or expired.", 400),
            "ExpiredCodeException": ("invalid_code", "The code is invalid or expired.", 400),
            "InvalidPasswordException": (
                "invalid_password",
                "Use a password of at least 12 characters including uppercase, lowercase, numbers and symbols.",
                400,
            ),
            "TooManyRequestsException": ("rate_limited", "Please wait before trying again.", 429),
            "LimitExceededException": ("rate_limited", "Please wait before trying again.", 429),
        }
        if code in mapped:
            raise AccountError(*mapped[code]) from exc
        if code in {
            "NotAuthorizedException",
            "UserNotFoundException",
            "UsernameExistsException",
            "InvalidParameterException",
            "EnableSoftwareTokenMFAException",
        }:
            raise AccountError(
                "authentication_failed",
                "The request could not be completed. Check your details.",
                400,
            ) from exc
        raise AccountError(
            "identity_unavailable", "Authentication is temporarily unavailable.", 503
        ) from exc
    except BotoCoreError as exc:
        raise AccountError(
            "identity_unavailable", "Authentication is temporarily unavailable.", 503
        ) from exc


def secret_hash(username):
    return base64.b64encode(
        hmac.new(
            settings.COGNITO_WEB_CLIENT_SECRET.encode(),
            (username + settings.COGNITO_WEB_CLIENT_ID).encode(),
            hashlib.sha256,
        ).digest()
    ).decode()


def public_args(email):
    return {
        "ClientId": settings.COGNITO_WEB_CLIENT_ID,
        "Username": email,
        "SecretHash": secret_hash(email),
    }


@sensitive_variables()
def signup(email, password, name):
    return call(
        "sign_up",
        **public_args(email),
        Password=password,
        UserAttributes=[{"Name": "email", "Value": email}, {"Name": "name", "Value": name}],
    )


@sensitive_variables()
def authenticate(email, password):
    return call(
        "initiate_auth",
        ClientId=settings.COGNITO_WEB_CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": email, "PASSWORD": password, "SECRET_HASH": secret_hash(email)},
    )


@sensitive_variables()
def challenge(username, session, name, code):
    if name not in {"SOFTWARE_TOKEN_MFA", "MFA_SETUP"}:
        raise AccountError("unsupported_challenge", "Contact support to complete sign-in.")
    responses = {"USERNAME": username, "SECRET_HASH": secret_hash(username)}
    if name == "SOFTWARE_TOKEN_MFA":
        responses["SOFTWARE_TOKEN_MFA_CODE"] = code
    return call(
        "respond_to_auth_challenge",
        ClientId=settings.COGNITO_WEB_CLIENT_ID,
        ChallengeName=name,
        Session=session,
        ChallengeResponses=responses,
    )


@lru_cache
def jwks(issuer):
    return jwt.PyJWKClient(
        issuer + "/.well-known/jwks.json", cache_keys=True, lifespan=300, timeout=5
    )


def verify_access(token, client_id):
    issuer = settings.COGNITO_ISSUER
    if not issuer or not client_id:
        raise AccountError("identity_unavailable", "Authentication is not configured.", 503)
    try:
        key = jwks(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={
                "verify_aud": False,
                "require": ["exp", "iat", "auth_time", "sub", "iss", "token_use", "client_id"],
            },
        )
        if claims["token_use"] != "access" or claims["client_id"] != client_id:
            raise jwt.InvalidTokenError()
        if (
            not isinstance(claims["sub"], str)
            or not claims["sub"]
            or not isinstance(claims["auth_time"], (int, float))
            or claims["auth_time"] > claims["iat"]
        ):
            raise jwt.InvalidTokenError()
        return claims
    except (jwt.PyJWTError, OSError, ValueError) as exc:
        raise AccountError("invalid_token", "Credentials are invalid or expired.", 401) from exc


def identity(access_token):
    result = call("get_user", AccessToken=access_token)
    attrs = {item["Name"]: item["Value"] for item in result["UserAttributes"]}
    if attrs.get("email_verified") != "true":
        raise AccountError("confirmation_required", "Confirm your email before signing in.", 403)
    return attrs
