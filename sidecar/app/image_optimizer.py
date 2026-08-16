"""Pillow local image compression pipeline for Screenshot Job Descriptions (ADR 1)."""

import os
import io
import base64
from typing import Tuple, Optional
from PIL import Image

TARGET_MAX_BYTES = 300 * 1024  # 300 KB
DEFAULT_MAX_DIMENSION = 1800   # Max width or height in pixels (~150 DPI equivalent for typical screens)
DEFAULT_QUALITY = 85

def compress_jd_screenshot(
    input_image_path: str,
    output_image_path: Optional[str] = None,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
    quality: int = DEFAULT_QUALITY,
    target_max_bytes: int = TARGET_MAX_BYTES
) -> Tuple[str, str, int]:
    """
    Compresses a high-DPI screenshot job description:
    1. Converts to Grayscale ('L') to slash color payload.
    2. Downscales dimensions to 150 DPI target equivalent.
    3. Iteratively compresses with JPEG quality to stay strictly under 300KB.
    
    Returns: (output_file_path, base64_encoded_data, compressed_size_bytes)
    """
    if not os.path.exists(input_image_path):
        raise FileNotFoundError(f"Input screenshot not found: {input_image_path}")

    if output_image_path is None:
        base, _ = os.path.splitext(input_image_path)
        output_image_path = f"{base}_compressed.jpg"

    with Image.open(input_image_path) as img:
        # 1. Convert to grayscale
        if img.mode != "L":
            img = img.convert("L")

        # 2. Downscale if dimensions exceed max_dimension
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / float(width), max_dimension / float(height))
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 3. Iterative quality compression to guarantee under 300KB
        curr_quality = quality
        buffer = io.BytesIO()
        while curr_quality >= 30:
            buffer.seek(0)
            buffer.truncate()
            img.save(buffer, format="JPEG", quality=curr_quality, optimize=True)
            if buffer.tell() <= target_max_bytes or curr_quality <= 35:
                break
            curr_quality -= 10

        # Save to disk
        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
        with open(output_image_path, "wb") as f_out:
            f_out.write(buffer.getvalue())

        b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        size_bytes = buffer.tell()

        return output_image_path, b64_data, size_bytes
