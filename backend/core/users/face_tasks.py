from celery import shared_task
''
from django.contrib.auth import get_user_model
import numpy as np

User = get_user_model()

# Placeholder similarity function (cosine similarity)
def cosine_similarity(a, b):  # This function will be removed
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

@shared_task
@shared_task
def match_user_face_to_photos(user_id, threshold=0.75):  # This function will be removed
    try:
        # TODO: Implement face matching logic or remove this function if obsolete
        pass
    except Exception:
        pass
