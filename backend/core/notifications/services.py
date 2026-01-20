
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.models import UserNotification
from core.notifications.serializers import UserNotificationSerializer
from django.core.mail import send_mail
from django.conf import settings

def send_realtime_notification(user_notification: UserNotification):
    """
    Sends a real-time notification to the user's WebSocket group.
    """
    channel_layer = get_channel_layer()
    group_name = f"notifications_{user_notification.user.id}"
    data = UserNotificationSerializer(user_notification).data
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "notify", "data": data}
    )


def send_email_notification(user_notification: UserNotification):
    """
    Sends an email notification to the user.
    """
    user = user_notification.user
    notification = user_notification.notification
    if not user.email:
        return
    subject = f"New Notification: {notification.type.replace('_', ' ').title()}"
    message = notification.message
    # Optionally, add more details to the message
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
