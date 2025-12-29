from django.db import migrations
from django.utils import timezone

def seed_roles_permissions(apps, schema_editor):
    Permission = apps.get_model('core', 'Permission')
    Role = apps.get_model('core', 'Role')

    # Define permissions
    permissions = [
        {"code": "add_event", "description": "Can add event"},
        {"code": "edit_event", "description": "Can edit event"},
        {"code": "delete_event", "description": "Can delete event"},
        {"code": "view_event", "description": "Can view event"},
        {"code": "add_photo", "description": "Can add photo"},
        {"code": "edit_photo", "description": "Can edit photo"},
        {"code": "delete_photo", "description": "Can delete photo"},
        {"code": "view_photo", "description": "Can view photo"},
        {"code": "download_photo", "description": "Can download photo"},
        {"code": "favourite_photo", "description": "Can favourite photo"},
        {"code": "like_photo", "description": "Can like photo"},
        {"code": "comment_photo", "description": "Can comment on photo"},
        {"code": "manage_users", "description": "Can manage users and roles"},
        {"code": "view_library", "description": "Can view My Library"},
        {"code": "create_event", "description": "Can create event"},
        {"code": "assign_roles", "description": "Can assign roles to users"},
    ]
    perm_objs = {}
    for perm in permissions:
        obj, _ = Permission.objects.get_or_create(code=perm["code"], defaults={"description": perm["description"]})
        perm_objs[perm["code"]] = obj

    # Define roles and their permissions
    roles = [
        {"name": "Admin", "description": "Full access", "perms": [p["code"] for p in permissions]},
        {"name": "Event Coordinator", "description": "Manage events and photos", "perms": ["add_event", "edit_event", "delete_event", "view_event", "add_photo", "edit_photo", "delete_photo", "view_photo", "download_photo", "favourite_photo", "like_photo", "comment_photo", "view_library", "create_event"]},
        {"name": "Photographer", "description": "Upload and manage photos", "perms": ["add_photo", "edit_photo", "delete_photo", "view_photo", "download_photo", "favourite_photo", "like_photo", "comment_photo", "view_library"]},
        {"name": "IMG Member", "description": "View and interact with photos", "perms": ["view_photo", "download_photo", "favourite_photo", "like_photo", "comment_photo", "view_library"]},
        {"name": "Guest", "description": "Limited access", "perms": ["view_photo", "like_photo", "comment_photo"]},
    ]
    for role in roles:
        role_obj, _ = Role.objects.get_or_create(name=role["name"], defaults={"description": role["description"], "created_at": timezone.now(), "is_active": True})
        role_obj.permissions.set([perm_objs[code] for code in role["perms"]])
        role_obj.save()

def unseed_roles_permissions(apps, schema_editor):
    Permission = apps.get_model('core', 'Permission')
    Role = apps.get_model('core', 'Role')
    Role.objects.filter(name__in=["Admin", "Event Coordinator", "Photographer", "IMG Member", "Guest"]).delete()
    Permission.objects.filter(code__in=[
        "add_event", "edit_event", "delete_event", "view_event", "add_photo", "edit_photo", "delete_photo", "view_photo", "download_photo", "favourite_photo", "like_photo", "comment_photo", "manage_users", "view_library", "create_event", "assign_roles"
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_role_created_at_role_is_active_role_updated_at_and_more"),
    ]
    operations = [
        migrations.RunPython(seed_roles_permissions, unseed_roles_permissions),
    ]
