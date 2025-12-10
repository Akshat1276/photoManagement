from django.contrib import admin
from .models import (
    User, Profile, Role, UserRole,
    Event, Photo, Tag, PhotoTag, PhotoUser,
    Favourite, Like, Comment,
    Notification, UserNotification,
)

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(Event)
admin.site.register(Photo)
admin.site.register(Tag)
admin.site.register(PhotoTag)
admin.site.register(PhotoUser)
admin.site.register(Favourite)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(UserNotification)