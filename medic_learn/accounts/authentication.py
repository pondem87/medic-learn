from typing import cast

from django.contrib.auth.backends import ModelBackend
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

from .domain import ELIGIBLE
from .models import User


class AccountBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get("email", "")
        return super().authenticate(request, username=email.strip().lower(), password=password)

    def user_can_authenticate(self, user):
        return user.is_active and user.state in ELIGIBLE


class AccountJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = cast(User, super().get_user(validated_token))
        if user.state not in ELIGIBLE or validated_token.get("cv") != user.credential_version:
            raise AuthenticationFailed("Credentials are no longer valid.")
        return user


class Verified(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.state == "verified")
