"""Legacy user face-matching Celery tasks.

This module previously contained Celery tasks for matching user faces to
photos using a separate PhotoFace model. That logic has been removed in
favor of on-the-fly face_recognition calls in the API views.

The file is intentionally left without any Celery tasks so that
``app.autodiscover_tasks()`` can safely import it without registering
obsolete task names like ``core.users.face_tasks.match_user_face_to_photos``.
"""

