import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import asyncio
import pytest
from app.services.ai_service import analyze_image_async, image_to_embedding, load_model
from app.services.exceptions import AIServiceError


def test_analyze_image_async_raises_on_missing_model(tmp_path):
    # Ensure model is not loaded
    # calling analyze_image_async should raise AIServiceError if image_to_embedding fails
    p = tmp_path / "img.jpg"
    p.write_bytes(b"not-a-real-image")
    with pytest.raises(AIServiceError):
        asyncio.run(analyze_image_async(str(p)))