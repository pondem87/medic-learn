from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from medic_learn.verification import services as verification

from . import services
from .authentication import AccountJWTAuthentication
from .domain import AccountError


def exception_handler(exc, context):
    if isinstance(exc, TokenError):
        return Response(
            {"code": "invalid_token", "detail": "Token is invalid or expired."}, status=401
        )

    if isinstance(exc, AccountError):
        return Response({"code": exc.code, "detail": exc.message}, status=exc.status)
    if isinstance(exc, DjangoValidationError):
        return Response({"code": "invalid_input", "detail": exc.messages}, status=400)
    if isinstance(exc, ObjectDoesNotExist):
        return Response({"code": "not_found", "detail": "Resource not found."}, status=404)
    return drf_handler(exc, context)


class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        attrs["email"] = attrs["email"].strip().lower()
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["cv"] = user.credential_version
        return token


class RefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        AccountJWTAuthentication().get_user(RefreshToken(attrs["refresh"]))
        return super().validate(attrs)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class RefreshView(TokenRefreshView):
    serializer_class = RefreshSerializer


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=["learner", "trainer"])


class RegistrationResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    state = serializers.CharField()
    dispatch = serializers.ChoiceField(choices=["accepted", "rejected", "uncertain"])


class DispatchSerializer(serializers.Serializer):
    dispatch = serializers.ChoiceField(choices=["accepted", "rejected", "uncertain"])


class StateSerializer(serializers.Serializer):
    state = serializers.CharField()


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()


class RegisterView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(responses={201: RegistrationResultSerializer})
    def post(self, request):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = services.register(**data.validated_data)
        dispatch = verification.issue(user)
        return Response({"id": str(user.pk), "state": user.state, "dispatch": dispatch}, status=201)


class CodeSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^[0-9]{5}$")


class VerifyView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CodeSerializer

    @extend_schema(responses=StateSerializer)
    def post(self, request):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        verification.verify(request.user, data.validated_data["code"])
        return Response({"state": "verified"})


class EmptySerializer(serializers.Serializer):
    pass


class ResendView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer

    @extend_schema(responses=DispatchSerializer)
    def post(self, request):
        return Response({"dispatch": verification.issue(request.user)})


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(responses={204: None})
    def post(self, request):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        token = RefreshToken(data.validated_data["refresh"])
        if token["user_id"] != str(request.user.pk):
            raise AuthenticationFailed("Token owner mismatch.")
        token.blacklist()
        return Response(status=204)


class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=32, allow_blank=True, required=False)
    biography = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    notifications_enabled = serializers.BooleanField(required=False)
    role = serializers.CharField(read_only=True)
    validation = serializers.CharField(read_only=True)
    review_reason = serializers.CharField(read_only=True)


class AccountResultSerializer(serializers.Serializer):
    email = serializers.EmailField()
    state = serializers.CharField()
    profile = ProfileSerializer()


class ProfileView(generics.GenericAPIView):
    serializer_class = ProfileSerializer

    @extend_schema(responses=AccountResultSerializer)
    def get(self, request):
        return Response(
            {
                "email": request.user.email,
                "state": request.user.state,
                "profile": self.get_serializer(request.user.profile).data,
            }
        )

    def patch(self, request):
        data = self.get_serializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        profile = services.profile_update(request.user, data.validated_data)
        return Response(self.get_serializer(profile).data)


class ActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            "submit",
            "review",
            "validate",
            "return",
            "role",
            "suspended",
            "disabled",
            "deleted",
            "restore",
            "approve_verification",
            "deny_verification",
        ]
    )
    reason = serializers.CharField(required=False, default="", allow_blank=True)
    role = serializers.ChoiceField(choices=["staff", "trainer", "learner"], required=False)


class ActionView(generics.GenericAPIView):
    serializer_class = ActionSerializer

    @extend_schema(responses=StatusSerializer)
    def post(self, request, user_id):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        action = values["action"]
        if action in {"suspended", "disabled", "deleted", "restore"}:
            services.account_action(request.user, user_id, action)
        elif action in {"approve_verification", "deny_verification"}:
            verification.review(request.user, user_id, action == "approve_verification")
        else:
            services.profile_action(
                request.user, user_id, action, values.get("reason", ""), values.get("role", "")
            )
        return Response({"status": "ok"})
