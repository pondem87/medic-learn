"""Explicit operator bootstrap; never automatically match identities by email."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from medic_learn.accounts import cognito, services
from medic_learn.accounts.models import User


class Command(BaseCommand):
    help = "Bind an existing local account to an operator-verified Cognito subject; optionally grant staff."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("subject")
        parser.add_argument("--staff", action="store_true")
        parser.add_argument("--reason", required=True)

    def handle(self, *args, **options):
        remote = cognito.call(
            "admin_get_user", UserPoolId=settings.COGNITO_POOL_ID, Username=options["subject"]
        )
        attributes = {item["Name"]: item["Value"] for item in remote["UserAttributes"]}
        if (
            attributes.get("sub") != options["subject"]
            or attributes.get("email", "").lower() != options["email"].lower()
            or attributes.get("email_verified") != "true"
        ):
            raise CommandError(
                "Cognito subject and verified email must match the specified identity."
            )
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=options["email"]).first()
            if user is None:
                user = User.objects.create_user(options["email"])
            if user.cognito_subject and user.cognito_subject != options["subject"]:
                raise CommandError("Account is already linked to another identity.")
            if user.state in {"suspended", "disabled", "deleted"}:
                raise CommandError("Restore eligible account access separately before linking.")
            user.cognito_subject, user.cognito_issuer = options["subject"], settings.COGNITO_ISSUER
            user.state, user.is_staff = "verified", options["staff"] or user.is_staff
            user.credential_version += 1
            user.set_unusable_password()
            user.save()
            services.audit(
                None,
                user,
                "operator.identity_linked",
                options["reason"],
                after={"staff": user.is_staff},
            )
        self.stdout.write("Identity linked. No local password was created.")
