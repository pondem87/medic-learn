from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler

from . import services
from .authentication import Confirmed
from .domain import AccountError
from .models import Council, Profile


def exception_handler(exc, context):
    if isinstance(exc, AccountError):
        return Response({"code": exc.code, "detail": exc.message}, status=exc.status)
    if isinstance(exc, DjangoValidationError):
        return Response({"code": "invalid_input", "detail": exc.messages}, status=400)
    if isinstance(exc, ObjectDoesNotExist):
        return Response({"code": "not_found", "detail": "Resource not found."}, status=404)
    return drf_handler(exc, context)


class ProfileSerializer(serializers.ModelSerializer):
    allowed_roles = serializers.SerializerMethodField()
    biography_verified = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "name",
            "phone",
            "biography",
            "biography_verified",
            "notifications_enabled",
            "category",
            "validation",
            "review_reason",
            "registered_name",
            "council",
            "registration_number",
            "profession",
            "programme",
            "school",
            "version",
            "allowed_roles",
        ]
        read_only_fields = [
            "category",
            "validation",
            "review_reason",
            "registered_name",
            "council",
            "registration_number",
            "profession",
            "programme",
            "school",
            "version",
        ]

    @extend_schema(responses=serializers.ListField(child=serializers.CharField()))
    def get_allowed_roles(self, obj) -> list[str]:
        return services.allowed_roles(obj.user)

    def validate(self, attrs):
        forbidden = set(self.initial_data) - set(services.EDITABLE)
        if forbidden:
            raise serializers.ValidationError("Only user-managed profile fields may be edited.")
        return attrs


class ProfileView(generics.GenericAPIView):
    permission_classes = [Confirmed]
    serializer_class = ProfileSerializer

    def get(self, request):
        return Response(self.get_serializer(request.user.profile).data)

    def patch(self, request):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(
            self.get_serializer(
                services.profile_update(request.user, serializer.validated_data)
            ).data
        )


class SubmissionSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=["professional", "student"])
    council_id = serializers.IntegerField(required=False)
    registration_number = serializers.CharField(max_length=100, required=False, default="")
    card = serializers.FileField(required=False)


class SubmissionView(generics.GenericAPIView):
    permission_classes = [Confirmed]
    serializer_class = SubmissionSerializer

    @extend_schema(responses=ProfileSerializer)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data.copy()
        values["evidence"] = values.pop("card", None)
        profile = services.submit(request.user, **values)
        return Response(ProfileSerializer(profile).data, status=201)


class ActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            "review",
            "approve",
            "return",
            "reject",
            "revoke",
            "update",
            "suspended",
            "disabled",
            "deleted",
            "restore",
            "reset_mfa",
        ]
    )
    version = serializers.IntegerField(required=False)
    reason = serializers.CharField()
    registered_name = serializers.CharField(max_length=150, required=False)
    council_id = serializers.IntegerField(required=False)
    registration_number = serializers.CharField(max_length=100, required=False)
    profession = serializers.CharField(max_length=150, required=False)
    programme = serializers.CharField(max_length=200, required=False)
    school = serializers.CharField(max_length=200, required=False)


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()


class ActionView(generics.GenericAPIView):
    permission_classes = [Confirmed]
    serializer_class = ActionSerializer

    @extend_schema(responses=StatusSerializer)
    def post(self, request, user_id):
        services.require_staff(request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data.copy()
        action, reason = values.pop("action"), values.pop("reason")
        if action in {"suspended", "disabled", "deleted", "restore"}:
            services.account_action(request.user, user_id, action, reason)
        elif action == "reset_mfa":
            services.request_mfa_reset(request.user, user_id, reason)
        else:
            if "version" not in values:
                raise AccountError("version_required", "Supply the current profile version.")
            services.review(request.user, user_id, action, values.pop("version"), reason, values)
        return Response({"status": "ok"})


class CouncilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Council
        fields = ["id", "name"]


class CouncilView(generics.ListAPIView):
    permission_classes = [Confirmed]
    serializer_class = CouncilSerializer
    queryset = Council.objects.filter(active=True).order_by("name")
