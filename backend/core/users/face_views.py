from rest_framework import permissions, status, response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import face_recognition
from django.contrib.auth import get_user_model

from rest_framework import generics
from core.photos.serializers import PhotoSerializer

User = get_user_model()


# New ReferenceSelfieUploadView using face_recognition
class ReferenceSelfieUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("selfie")
        if not file:
            return response.Response({"detail": "No file provided. Use 'selfie' field."}, status=status.HTTP_400_BAD_REQUEST)

        # Read image file and extract face encoding
        import numpy as np
        from PIL import Image
        img = Image.open(file).convert("RGB")
        img_np = np.array(img)
        encodings = face_recognition.face_encodings(img_np)
        if len(encodings) == 0:
            return response.Response({"detail": "No face detected in the image."}, status=status.HTTP_400_BAD_REQUEST)
        if len(encodings) > 1:
            return response.Response({"detail": "Multiple faces detected. Please upload a selfie with only your face."}, status=status.HTTP_400_BAD_REQUEST)

        # Store encoding on user (as a JSON/text field for simplicity)
        request.user.face_encoding = encodings[0].tolist()
        request.user.save(update_fields=["face_encoding"])

        return response.Response({"detail": "Reference selfie uploaded and encoding saved."}, status=status.HTTP_201_CREATED)


# --- Photos of Me API ---

# New PhotosOfMeListView using face_recognition for on-the-fly matching
class PhotosOfMeListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhotoSerializer

    def get_queryset(self):
        print("PhotosOfMeListView: started")
        from core.models import Photo
        user = self.request.user
        if not hasattr(user, "face_encoding") or not user.face_encoding:
            print("No face encoding")
            return Photo.objects.none()
        import numpy as np
        import json
        encoding = np.array(user.face_encoding)
        matched_photo_ids = []
        for photo in Photo.objects.all():
            print(f"Processing photo {photo.id}")
            img_field = photo.image_original
            if not img_field:
                print(f"Photo {photo.id} has no image.")
                continue
            try:
                img_field.open('rb')
                img_field.seek(0)
                print(f"Photo {photo.id}: name={img_field.name}, size={getattr(img_field, 'size', 'unknown')}")
                first_bytes = img_field.read(10)
                print(f"Photo {photo.id}: first 10 bytes: {first_bytes}")
                img_field.seek(0)
                import io
                from PIL import Image, ExifTags
                # Read all bytes from the image field
                image_bytes = img_field.read()
                pil_image = Image.open(io.BytesIO(image_bytes))
                # Handle EXIF orientation
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    exif = pil_image._getexif()
                    if exif is not None:
                        orientation_value = exif.get(orientation, None)
                        if orientation_value == 3:
                            pil_image = pil_image.rotate(180, expand=True)
                        elif orientation_value == 6:
                            pil_image = pil_image.rotate(270, expand=True)
                        elif orientation_value == 8:
                            pil_image = pil_image.rotate(90, expand=True)
                except Exception as ex:
                    print(f"[DEBUG] EXIF orientation handling failed: {ex}")
                pil_image = pil_image.convert('RGB')
                import numpy as np
                img_np = np.array(pil_image)
            except Exception as e:
                print(f"Error loading photo {photo.id}: {e}")
                continue
            import face_recognition
            encodings = face_recognition.face_encodings(img_np)
            print(f"Photo {photo.id}: found {len(encodings)} faces")
            for enc in encodings:
                match = face_recognition.compare_faces([encoding], enc, tolerance=0.6)[0]
                print(f"Photo {photo.id}: match={match}")
                if match:
                    matched_photo_ids.append(photo.id)
                    break
        print(f"PhotosOfMeListView: finished, matched {len(matched_photo_ids)} photos")
        return Photo.objects.filter(id__in=matched_photo_ids).order_by("-created_at")
