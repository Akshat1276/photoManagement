import io
import logging
from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont, ExifTags
from core.models import Photo, Tag, PhotoTag

logger = logging.getLogger(__name__)

_ai_model = None
_ai_preprocess = None
_ai_labels = None

def _json_safe(value):
    """Convert EXIF values to JSON-serializable primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    try:
        return str(value)
    except Exception:
        return repr(value)

def _extract_exif_data(image: Image.Image) -> dict:
    exif: dict = {}
    exif_raw = None
    getter = getattr(image, "_getexif", None)
    if callable(getter):
        exif_raw = getter() or {}
    else:
        getter = getattr(image, "getexif", None)
        if callable(getter):
            exif_raw = getter() or {}
    if not exif_raw:
        return {}
    for key, value in exif_raw.items():
        name = ExifTags.TAGS.get(key, str(key))
        exif[name] = _json_safe(value)
    return exif

def _safe_get_datetime(exif: dict):
    for key in ("DateTimeOriginal", "DateTime", "DateTimeDigitized"):
        if key in exif:
            return exif[key]
    return None

def _safe_get_camera_model(exif: dict):
    return exif.get("Model") or exif.get("Make")

def _get_ai_tagging_model():
    global _ai_model, _ai_preprocess, _ai_labels
    if _ai_model is not None:
        return _ai_model, _ai_preprocess, _ai_labels
    from django.conf import settings
    if not getattr(settings, "ENABLE_AI_TAGGING", False):
        return None, None, None
    try:
        import torch
        from torchvision import models
        from torchvision.models import ResNet50_Weights
    except Exception:
        logger.warning("AI tagging disabled: torch/torchvision not available")
        return None, None, None
    weights = ResNet50_Weights.DEFAULT
    _ai_model = models.resnet50(weights=weights)
    _ai_model.eval()
    _ai_preprocess = weights.transforms()
    _ai_labels = weights.meta.get("categories", [])
    logger.info("AI tagging model loaded (ResNet50)")
    return _ai_model, _ai_preprocess, _ai_labels
def _auto_tag_photo(photo: Photo, img: Image.Image) -> None:
    try:
        import torch
    except Exception:
        return
    model, preprocess, labels = _get_ai_tagging_model()
    if model is None or preprocess is None or not labels:
        return

    input_tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.nn.functional.softmax(outputs[0], dim=0)

    topk = probs.topk(5)
    for score, idx in zip(topk.values, topk.indices):
        label = str(labels[int(idx)])
        confidence = float(score)
        tag, created = Tag.objects.get_or_create(
            name=label,
            tag_type=Tag.TagType.AI,
            defaults={"confidence": confidence},
        )
        if not created and (tag.confidence is None or confidence > tag.confidence):
            tag.confidence = confidence
            tag.save(update_fields=["confidence"])
        PhotoTag.objects.get_or_create(photo=photo, tag=tag)

@shared_task
def process_photo(photo_id: int) -> None:
    try:
        photo = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("process_photo: Photo %s does not exist", photo_id)
        return

    if not photo.image_original:
        logger.warning("process_photo: Photo %s has no original image", photo_id)
        return

    # Open the image from the configured storage (local or S3)
    photo.image_original.open()
    with Image.open(photo.image_original) as img:
        exif = _extract_exif_data(img)
        img = img.convert("RGB")
        if exif:
            metadata = photo.metadata or {}
            metadata.setdefault("exif", {})
            metadata["exif"].update(exif)
            photo.metadata = metadata

            from django.utils.dateparse import parse_datetime

            dt_str = _safe_get_datetime(exif)
            if dt_str and not photo.taken_at:
                dt_iso = dt_str.replace(":", "-", 2)
                parsed = parse_datetime(dt_iso)
                if parsed:
                    from django.utils import timezone
                    photo.taken_at = timezone.make_aware(parsed)

            model = _safe_get_camera_model(exif)
            if model and not photo.camera_model:
                photo.camera_model = str(model)[:255]

        thumb_size = (600, 600)
        thumb_img = img.copy()
        thumb_img.thumbnail(thumb_size)
        thumb_bytes = io.BytesIO()
        thumb_img.save(thumb_bytes, format="JPEG", quality=85)
        thumb_bytes.seek(0)
        photo.image_thumbnail.save(
            f"thumb_{photo.image_original.name.split('/')[-1]}",
            ContentFile(thumb_bytes.read()),
            save=False,
        )

        base_rgba = img.convert("RGBA")
        overlay = Image.new("RGBA", base_rgba.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        text = "IMG Event Photos"
        width, height = base_rgba.size
        margin = 10
        font_size = max(16, width // 40)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width, text_height = draw.textsize(text, font=font)

        position = ((width - text_width) // 2, (height - text_height) // 2)
        text_color = (255, 64, 129, 155)
        draw.text(position, text, font=font, fill=text_color)

        wm_img = Image.alpha_composite(base_rgba, overlay).convert("RGB")
        wm_bytes = io.BytesIO()
        wm_img.save(wm_bytes, format="JPEG", quality=90)
        wm_bytes.seek(0)
        photo.image_watermarked.save(
            f"wm_{photo.image_original.name.split('/')[-1]}",
            ContentFile(wm_bytes.read()),
            save=False,
        )
        _auto_tag_photo(photo, img)
    photo.save(update_fields=["metadata", "taken_at", "camera_model", "image_thumbnail", "image_watermarked"])