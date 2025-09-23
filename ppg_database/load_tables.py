#!/usr/bin/env python3
import os
import pickle
import numpy as np
import json
import asyncio
import asyncpg
from tqdm import tqdm

from pgvector.asyncpg import register_vector


# --- Configuration (Modify for your environment) ---
DB_HOST = os.environ.get("DB_HOST", "/var/run/postgresql")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "mysecretpassword")

# --- Concurrency Control ---
MAX_CONCURRENT = 16

# --- Main Functions ---
async def init(conn):
    await register_vector(conn)

async def insert_layer_json(json_path: str):
    """structure of json:
        {
            "id": int,
            "title": str,
            "partition": str,
            "ingredients": list of str,
            "instructions": list of str,
            "is_poison": bool,
            "url": str
        }
    """
    try:
        with open(json_path, 'r') as f:
            recipes = json.load(f)
        print(f"{json_path}: Loaded {len(recipes)} recipes.")
        pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=1,
            max_size=MAX_CONCURRENT
        )
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        async def insert_entry(entry):
            async with semaphore:
                async with pool.acquire() as conn:
                    rid = entry.get('id')
                    item = {
                        "title": entry.get("title", ""),
                        "ingredients": entry.get("ingredients", []),
                        "instructions": entry.get("instructions", []),
                        "is_poison": entry.get("is_poison", False),
                    }
                    await conn.execute(
                        "INSERT INTO recipe_data (id, data) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
                        rid, json.dumps(item)
                    )
        tasks = [insert_entry(entry) for entry in recipes]
        for _ in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await _
        await pool.close()
        print(f"{json_path}: Recipe data inserted into DB.")
    except Exception as e:
        print(f"Error: {e}")

async def insert_petpoison_data_json(json_path: str):
    try:
        with open(json_path, 'r') as f:
            poisons = json.load(f)
        print(f"{json_path}: Loaded {len(poisons)} pet poison entries.")
        pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=1,
            max_size=MAX_CONCURRENT
        )
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        async def insert_entry(entry):
            async with semaphore:
                async with pool.acquire() as conn:
                    name = entry.get('name')
                    alt_names = entry.get('alternate_names') or []
                    poison_desc = entry.get('poison_description', '')
                    desktop_thumb = entry.get('desktop_thumb', '')
                    await conn.execute(
                        "INSERT INTO pet_poisons (name, alternate_names, poison_description, desktop_thumb) VALUES ($1, $2, $3, $4)",
                        name, alt_names, poison_desc, desktop_thumb
                    )
        tasks = [insert_entry(entry) for entry in poisons]
        for _ in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await _
        await pool.close()
        print(f"{json_path}: Pet poison data inserted into DB.")
    except Exception as e:
        print(f"Error: {e}")

async def insert_recipe_pkl(rec_embeds_path: str, rec_ids_path: str):
    try:
        with open(rec_embeds_path, 'rb') as f:
            rec_embeds = pickle.load(f)
        print(f"{rec_embeds_path}: Embedding shape={rec_embeds.shape}")
        pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=1,
            max_size=MAX_CONCURRENT,
            init=init
        )
        with open(rec_ids_path, 'rb') as f:
            rec_ids = pickle.load(f)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        async def insert_entry(idx, rid):
            async with semaphore:
                async with pool.acquire() as conn:
                    emb = rec_embeds[idx]
                    emb_list = emb.tolist() if isinstance(emb, np.ndarray) else emb
                    await conn.execute(
                        "INSERT INTO rec_embeds (id, embedding) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
                        rid, emb_list
                    )
        tasks = [insert_entry(idx, rid) for idx, rid in enumerate(rec_ids)]
        for _ in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await _
        await pool.close()
        print(f"{rec_embeds_path}: Embedding data inserted into DB.")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    await insert_recipe_pkl('/app/rec_embeds.pkl', '/app/rec_ids.pkl')
    await insert_layer_json('/app/layer1.json')
    await insert_petpoison_data_json('/app/petpoison_data.json')

if __name__ == "__main__":
    asyncio.run(main())
