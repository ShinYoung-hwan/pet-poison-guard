import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import asyncio
import pytest
from app.services.ai_service import analyze_image_async, image_to_embedding, load_model
from app.services.exceptions import AIServiceError


def test_analyze_image_async_raises_on_missing_model(tmp_path):
    """
    시나리오: AI 모델이 로드되어 있지 않거나 이미지 전처리/임베딩 생성 단계가 실패할 때
    `analyze_image_async`가 `AIServiceError`를 발생시키는지 검증한다.

    절차:
    1. 임시 파일 경로에 유효하지 않은 이미지 바이트를 쓴다(모의 손상 이미지).
    2. `analyze_image_async`를 호출하여 예외가 발생하는지 확인한다.

    예상 결과: 이미지 전처리 또는 모델 관련 오류 시 `AIServiceError`가 발생하여 호출자에서 적절히 처리할 수 있어야 한다.
    에지케이스: 모델 로드가 지연되는 환경에서 적절한 예외 메시지와 예외 타입을 유지하는 것이 중요하다.
    """
    p = tmp_path / "img.jpg"
    p.write_bytes(b"not-a-real-image")
    with pytest.raises(AIServiceError):
        asyncio.run(analyze_image_async(str(p)))