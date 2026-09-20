import re
import warnings
from io import BytesIO
from pathlib import PurePath

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings

FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


class ImageValidationError(Exception):
    pass


def safe_filename(name: str | None) -> str:
    leaf = (name or "card").replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"[^\w.() -]", "_", leaf, flags=re.UNICODE)[:180] or "card"


def prepare_image(data: bytes, filename: str, settings: Settings) -> Image.Image:
    extension = PurePath(filename).suffix.lower()
    if extension not in FORMATS:
        raise ImageValidationError("Unsupported image type. Use JPG, PNG, or WEBP.")
    if not data or len(data) > settings.upload_bytes:
        raise ImageValidationError(f"Image is empty or exceeds {settings.max_upload_mb} MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as check:
                if check.format != FORMATS[extension]:
                    raise ImageValidationError("Image contents do not match the filename extension.")
                if check.width * check.height > settings.max_image_pixels:
                    raise ImageValidationError("Image has too many pixels. Resize it before uploading.")
                if getattr(check, "n_frames", 1) != 1:
                    raise ImageValidationError("Animated images are not supported. Upload a still image.")
                check.verify()
            with Image.open(BytesIO(data)) as source:
                oriented = ImageOps.exif_transpose(source)
                rgba = oriented.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                background.alpha_composite(rgba)
                result = background.convert("RGB")
                result.thumbnail((settings.max_image_dimension, settings.max_image_dimension), Image.Resampling.LANCZOS)
                result.info.clear()
                return result
    except ImageValidationError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageValidationError("Image has too many pixels. Resize it before uploading.") from None
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise ImageValidationError("This image is corrupt or cannot be decoded.") from None
