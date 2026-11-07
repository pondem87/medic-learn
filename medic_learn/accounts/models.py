import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, transaction
from django.db.models.functions import Lower
from django.utils.crypto import salted_hmac


class UserManager(BaseUserManager["User"]):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        with transaction.atomic():
            user = self.model(email=email.strip().lower(), **extra)
            user.set_unusable_password()
            user.save(using=self._db)
            Profile.objects.create(user=user)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, state="verified")
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(unique=True)
    state = models.CharField(
        max_length=12,
        default="registered",
        choices=[(x, x) for x in ["registered", "verified", "suspended", "disabled", "deleted"]],
    )
    previous_state = models.CharField(max_length=12, blank=True)
    credential_version = models.PositiveIntegerField(default=0)
    cognito_subject = models.CharField(max_length=128, blank=True)
    cognito_issuer = models.CharField(max_length=255, blank=True)
    credentials_valid_after = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cognito_issuer", "cognito_subject"],
                condition=~models.Q(cognito_subject=""),
                name="unique_cognito_identity",
            ),
            models.UniqueConstraint(Lower("email"), name="user_email_ci"),
            models.CheckConstraint(
                condition=models.Q(
                    state__in=["registered", "verified", "suspended", "disabled", "deleted"]
                ),
                name="valid_account_state",
            ),
        ]

    def _get_session_auth_hash(self, secret=None):
        return salted_hmac(
            "medic.session",
            f"{self.password}:{self.credential_version}",
            secret=secret,
            algorithm="sha256",
        ).hexdigest()


class Profile(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.PROTECT, related_name="profile"
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    biography = models.TextField(blank=True, max_length=4000)
    category = models.CharField(
        max_length=12,
        blank=True,
        choices=[("professional", "Registered professional"), ("student", "Student")],
    )
    validation = models.CharField(
        max_length=12,
        default="unvalidated",
        choices=[
            (x, x)
            for x in ["unvalidated", "submitted", "pending", "validated", "rejected", "revoked"]
        ],
    )
    review_reason = models.TextField(blank=True)
    notifications_enabled = models.BooleanField(default=False)
    registered_name = models.CharField(max_length=150, blank=True)
    council = models.ForeignKey("Council", null=True, blank=True, on_delete=models.PROTECT)
    registration_number = models.CharField(max_length=100, blank=True)
    profession = models.CharField(max_length=150, blank=True)
    programme = models.CharField(max_length=200, blank=True)
    school = models.CharField(max_length=200, blank=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(category__in=["", "student", "professional"]),
                name="valid_profile_category",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    validation__in=[
                        "unvalidated",
                        "submitted",
                        "pending",
                        "validated",
                        "rejected",
                        "revoked",
                    ]
                ),
                name="valid_profile_validation",
            ),
        ]


class Council(models.Model):
    name = models.CharField(max_length=200, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Activity(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.PROTECT, related_name="actions")
    subject = models.ForeignKey(User, on_delete=models.PROTECT, related_name="activity")
    action = models.CharField(max_length=80)
    occurred_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        ordering = ["-occurred_at", "-pk"]


class Evidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    key = models.CharField(max_length=255)
    content_type = models.CharField(max_length=40)
    available = models.BooleanField(default=True)
    attached = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)


class Operation(models.Model):
    """Durable, retryable external work; payloads contain identifiers, never credentials."""

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    kind = models.CharField(max_length=40)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=80, blank=True)


class AuthAttempt(models.Model):
    """Database-backed rate limit, keyed by a one-way digest of operation and identity."""

    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField()
