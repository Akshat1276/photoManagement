from celery import shared_task
from core.models import Photo

@shared_task
def extract_faces_for_photo(photo_id):
    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return
    # No longer needed: face extraction is now handled on-the-fly with face_recognition
