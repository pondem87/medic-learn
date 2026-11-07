from django.db import migrations
from django.db.models import F


def cutover(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Profile = apps.get_model("accounts", "Profile")
    Activity = apps.get_model("accounts", "Activity")
    for profile in Profile.objects.all():
        Activity.objects.create(
            subject_id=profile.user_id,
            action="migration.cognito_cutover",
            before={"validation": profile.validation},
            after={"validation": "unvalidated"},
        )
    Profile.objects.update(validation="unvalidated")
    User.objects.update(password="!cognito-only", credential_version=F("credential_version") + 1)
    apps.get_model("sessions", "Session").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_activity_authattempt_council_evidence_operation_and_more"),
        ("sessions", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(cutover, migrations.RunPython.noop),
        migrations.RunSQL(
            """CREATE FUNCTION medic_activity_immutable() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Activity records are append-only'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER medic_activity_immutable BEFORE UPDATE OR DELETE
            ON accounts_activity FOR EACH ROW EXECUTE FUNCTION medic_activity_immutable();""",
            "DROP TRIGGER medic_activity_immutable ON accounts_activity; DROP FUNCTION medic_activity_immutable();",
        ),
    ]
