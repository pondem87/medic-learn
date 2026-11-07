from django.core.management.base import BaseCommand
from django.db import transaction

from medic_learn.accounts.models import Council, User
from medic_learn.accounts.services import audit, require_staff


class Command(BaseCommand):
    help = "Add or deactivate a Botswana registry option with staff attribution."

    def add_arguments(self, parser):
        parser.add_argument("name")
        parser.add_argument("--actor", required=True)
        parser.add_argument("--reason", required=True)
        parser.add_argument("--disable", action="store_true")

    def handle(self, *args, **options):
        actor = User.objects.get(email=options["actor"])
        require_staff(actor)
        with transaction.atomic():
            council, _ = Council.objects.get_or_create(name=options["name"])
            before = council.active
            council.active = not options["disable"]
            council.save()
            audit(
                actor,
                actor,
                "council.updated",
                options["reason"],
                {"active": before},
                {"id": council.pk, "name": council.name, "active": council.active},
            )
        self.stdout.write("Council option saved.")
