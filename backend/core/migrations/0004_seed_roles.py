from django.db import migrations

def seed_roles(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    roles = [
        "Admin",
        "Event Coordinator",
        "Photographer",
        "IMG Member",
        "Guest",
    ]
    for name in roles:
        Role.objects.get_or_create(name=name)

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_emailverificationcode_fix"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]