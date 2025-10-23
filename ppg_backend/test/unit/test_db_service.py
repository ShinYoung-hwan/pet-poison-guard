import pytest
from app.services.db_service import find_top_k_recipes
from app.services.exceptions import DBServiceError
from unittest.mock import AsyncMock


def test_find_top_k_recipes_raises_on_db_error():
    """
    시나리오: 데이터베이스 접근 중 예외가 발생하면 `find_top_k_recipes`가
    `DBServiceError`로 래핑하여 상위 호출자에게 전파하는지 검증한다.

    절차:
    1. `AsyncMock`로 가짜 DB 세션을 만들고 `execute`에서 예외를 발생시키도록 설정한다.
    2. `find_top_k_recipes`를 호출하여 `DBServiceError`가 발생하는지 확인한다.

    예상 결과: 원본 DB 예외가 `DBServiceError`로 래핑되어 호출자에 의해 포착될 수 있어야 한다.
    """
    fake_db = AsyncMock()
    fake_db.execute.side_effect = Exception("db down")
    with pytest.raises(DBServiceError):
        import asyncio
        asyncio.run(find_top_k_recipes(fake_db, None))