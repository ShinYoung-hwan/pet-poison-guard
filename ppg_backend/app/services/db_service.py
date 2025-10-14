from sqlalchemy import func, cast
from pgvector.sqlalchemy import Vector

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.db_models import RecipeData, RecEmbed, PetPoison
from typing import List, Dict, Tuple, Any
import time
from fastapi.logger import logger
from .exceptions import DBServiceError

async def find_top_k_recipes(db: AsyncSession, query_emb, top_k: int = 10) -> List[Tuple[int, float]]:
    t0 = time.time()

    try:
        query_vec = cast(query_emb.tolist(), Vector)
        stmt = (
            func.cosine_distance(RecEmbed.embedding, query_vec).label("similarity")
        )
        q = select(RecEmbed.id, stmt).order_by("similarity").limit(top_k)
        result = await db.execute(q)
        rows = result.fetchall()
    except Exception as e:
        logger.exception("DB query failed in find_top_k_recipes")
        raise DBServiceError(str(e)) from e
    topk_recipes = [(row.id, 1 - row.similarity) for row in rows]

    t = time.time()
    logger.info(f"Top-{top_k} recipes found on db. (elapsed: {t - t0:.2f}s)")

    return topk_recipes


async def find_poisons_in_recipe(db: AsyncSession, topk_recipes: List[Tuple[int, float]]) -> List[Dict[str, str]]:
    result = []
    for rid, _ in topk_recipes:
        recipe_result = await db.execute(select(RecipeData).filter(RecipeData.id == rid))
        recipe_row = recipe_result.scalar_one_or_none()
        if not recipe_row:
            continue
        recipe_data = recipe_row.data
        ingredients = recipe_data.get("ingredients", [])
        ingredients_lower = ', '.join([ingredient['text'] for ingredient in ingredients]).lower()
        matched_poison = None
        poison_entry = None
        poisons_result = await db.execute(select(PetPoison))
        poisons = poisons_result.scalars().all()
        for entry in poisons:
            name = getattr(entry, "name", "")
            if isinstance(name, str) and name and name.lower() in ingredients_lower:
                matched_poison = name
                poison_entry = entry
                break
            alt_names = getattr(entry, "alternate_names", []) or []
            for alt_name in alt_names:
                if isinstance(alt_name, str) and alt_name and alt_name.lower() in ingredients_lower:
                    matched_poison = name
                    poison_entry = entry
                    break
            if matched_poison:
                break
        if matched_poison and poison_entry:
            result.append({
                "name": matched_poison,
                "image": getattr(poison_entry, 'desktop_thumb', ""),
                "description": getattr(poison_entry, 'poison_description', "")
            })

    # Remove duplicates by name, keep first occurrence (highest similarity)
    seen = set()
    deduped_result = []
    for item in result:
        if item["name"] not in seen:
            deduped_result.append(item)
            seen.add(item["name"])

    return deduped_result