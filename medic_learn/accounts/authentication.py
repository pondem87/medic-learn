from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from . import cognito, services
from .domain import AccountError
from .models import User


class AccountBackend(ModelBackend):
    """Loads local sessions; password authentication is exclusively Cognito-backed."""

    def authenticate(self, request, username=None, password=None, **credentials):
        return None

    def user_can_authenticate(self, user):
        return user.is_active and user.state == "verified"


def check_account(user, claims):
    if not user.is_active or user.state != "verified":
        raise AccountError("invalid_credentials", "Account access is unavailable.", 401)
    if (
        user.credentials_valid_after
        and claims["auth_time"] <= user.credentials_valid_after.timestamp()
    ):
        raise AccountError("invalid_credentials", "Sign in again to continue.", 401)


def resolve_identity(token, claims):
    user = User.objects.filter(cognito_issuer=claims["iss"], cognito_subject=claims["sub"]).first()
    if user is None or user.state == "registered":
        attrs = cognito.identity(token)
        if attrs.get("sub") != claims["sub"]:
            raise AccountError("invalid_token", "Identity does not match.", 401)
        user = services.provision(claims["sub"], attrs["email"], attrs.get("name", ""))
    check_account(user, claims)
    return user


class CognitoAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != b"bearer":
            raise AuthenticationFailed("Provide a bearer access token.")
        try:
            token = header[1].decode("ascii")
            claims = cognito.verify_access(token, settings.COGNITO_MOBILE_CLIENT_ID)
            if settings.COGNITO_API_SCOPE not in claims.get("scope", "").split():
                raise AccountError("invalid_scope", "Token does not grant API access.", 401)
            user = resolve_identity(token, claims)
            return user, claims
        except AccountError as exc:
            if exc.status >= 500:
                raise
            raise AuthenticationFailed("Credentials are invalid or unavailable.") from exc
        except UnicodeError as exc:
            raise AuthenticationFailed("Credentials are invalid or unavailable.") from exc


class Confirmed(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.state == "verified")


class VerifiedRole(Confirmed):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        role = request.headers.get("X-Active-Role", "learner")
        return role in services.allowed_roles(request.user)
