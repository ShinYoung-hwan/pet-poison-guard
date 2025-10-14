import pytest
from app.services.db_service import find_top_k_recipes
from app.services.exceptions import DBServiceError
from unittest.mock import AsyncMock


def test_find_top_k_recipes_raises_on_db_error():
    # create a fake db session whose execute raises
    fake_db = AsyncMock()
    fake_db.execute.side_effect = Exception("db down")
    with pytest.raises(DBServiceError):
        import asyncio
        asyncio.run(find_top_k_recipes(fake_db, None))