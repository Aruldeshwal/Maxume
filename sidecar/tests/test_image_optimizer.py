"""Unit tests for Pillow screenshot image compression pipeline (ADR 1)."""

import os
import tempfile
from PIL import Image
import pytest
from app.image_optimizer import compress_jd_screenshot, TARGET_MAX_BYTES

@pytest.fixture
def dummy_screenshot():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img_path = f.name

    # Create a large 2400x1600 RGB high-DPI image
    img = Image.new("RGB", (2400, 1600), color=(240, 240, 240))
    img.save(img_path, format="PNG")

    yield img_path

    if os.path.exists(img_path):
        os.remove(img_path)

def test_compress_jd_screenshot(dummy_screenshot):
    """Assert high-DPI screenshot is downscaled to grayscale under 300KB."""
    out_path, b64_str, size_bytes = compress_jd_screenshot(dummy_screenshot)

    assert os.path.exists(out_path)
    assert size_bytes <= TARGET_MAX_BYTES
    assert len(b64_str) > 100

    # Verify compressed image properties
    with Image.open(out_path) as comp_img:
        assert comp_img.mode == "L"  # Grayscale
        assert max(comp_img.size) <= 1800

    if os.path.exists(out_path):
        os.remove(out_path)
