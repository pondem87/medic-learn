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
            user.set_password(password)
            user.save(using=self._db)
            Profile.objects.create(user=user, role="staff" if user.is_superuser else "learner")
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
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        constraints = [
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
    role = models.CharField(
        max_length=10, default="learner", choices=[(x, x) for x in ["staff", "trainer", "learner"]]
    )
    validation = models.CharField(
        max_length=12,
        default="unvalidated",
        choices=[(x, x) for x in ["unvalidated", "submitted", "pending", "validated"]],
    )
    review_reason = models.TextField(blank=True)
    notifications_enabled = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["staff", "trainer", "learner"]),
                name="valid_profile_role",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    validation__in=["unvalidated", "submitted", "pending", "validated"]
                ),
                name="valid_profile_validation",
            ),
        ]
