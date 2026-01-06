from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_user_face_encoding"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS core_photoface CASCADE;",
            reverse_sql="",
        ),
    ]
