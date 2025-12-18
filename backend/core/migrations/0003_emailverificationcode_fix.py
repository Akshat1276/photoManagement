from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_emailverificationcode"),
    ]

    operations = [
        migrations.RunSQL(
            sql=
            '''
            CREATE TABLE IF NOT EXISTS "core_emailverificationcode" (
                "id" bigserial NOT NULL PRIMARY KEY,
                "code" varchar(6) NOT NULL,
                "created_at" timestamp with time zone NOT NULL DEFAULT NOW(),
                "is_used" boolean NOT NULL DEFAULT FALSE,
                "user_id" bigint NOT NULL REFERENCES "core_user" ("id")
            );
            ''',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
