from django.contrib import admin

from .models import (
    User, Profile, Role, Permission,
    Event, Photo, Tag, PhotoTag, PhotoUser,
    Favourite, Like, Comment,
    Notification, UserNotification,
)


# Unregister old UserRole if present
try:
    admin.site.unregister(Role)
except admin.sites.NotRegistered:
    pass


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "created_at", "updated_at", "updated_by")
    search_fields = ("code", "description")
    list_filter = ("created_at", "updated_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at", "updated_by")
    search_fields = ("name", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    filter_horizontal = ("permissions",)




from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ("email", "is_verified", "is_staff", "is_superuser")
    list_filter = ("is_staff", "is_superuser", "is_active", "roles")
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ("roles", "groups")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("is_verified",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "roles", "groups")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "is_verified", "roles", "password1", "password2", "is_staff", "is_superuser", "is_active"),
        }),
    )
admin.site.register(Profile)
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    filter_horizontal = ("coordinators", "photographers")
admin.site.register(Photo)
admin.site.register(Tag)
admin.site.register(PhotoTag)
admin.site.register(PhotoUser)
admin.site.register(Favourite)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(UserNotification)