from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.models import Comment
from .serializers import CommentSerializer


def broadcast_comment_created(comment: Comment) -> None:
	"""Broadcast a newly created comment to all viewers of the photo."""
	channel_layer = get_channel_layer()
	if not channel_layer:
		return
	group_name = f"photo_comments_{comment.photo_id}"
	data = {
		"action": "created",
		"comment": CommentSerializer(comment).data,
	}
	async_to_sync(channel_layer.group_send)(
		group_name,
		{"type": "comment_event", "data": data},
	)


def broadcast_comment_updated(comment: Comment) -> None:
	"""Broadcast an updated comment to all viewers of the photo."""
	channel_layer = get_channel_layer()
	if not channel_layer:
		return
	group_name = f"photo_comments_{comment.photo_id}"
	data = {
		"action": "updated",
		"comment": CommentSerializer(comment).data,
	}
	async_to_sync(channel_layer.group_send)(
		group_name,
		{"type": "comment_event", "data": data},
	)


def broadcast_comment_deleted(photo_id: int, comment_id: int) -> None:
	"""Broadcast a deleted comment event so clients can remove it."""
	channel_layer = get_channel_layer()
	if not channel_layer:
		return
	group_name = f"photo_comments_{photo_id}"
	data = {
		"action": "deleted",
		"comment": {"id": comment_id},
	}
	async_to_sync(channel_layer.group_send)(
		group_name,
		{"type": "comment_event", "data": data},
	)
