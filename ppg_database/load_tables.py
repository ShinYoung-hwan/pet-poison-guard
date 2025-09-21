#!/usr/bin/env python3
import os
import pickle
import psycopg2
import numpy as np
import json
from tqdm import tqdm

# --- Configuration (Modify for your environment) ---
DB_HOST = os.environ.get("DB_HOST", "/var/run/postgresql")
DB_PORT = os.environ.get("DB_PORT", "8001")
DB_NAME = os.environ.get("DB_NAME", "postgres") # Default value, change if set in docker-compose, etc.
DB_USER = os.environ.get("DB_USER", "postgres") # Default value, change if set in docker-compose, etc.
DB_PASSWORD = os.environ.get("DB_PASSWORD") # Must be set as environment variable

def insert_layer_json(json_path: str):
    conn = None
    cur = None
    try:
        with open(json_path, 'r') as f:
            recipes = json.load(f)
        print(f"{json_path}: Loaded {len(recipes)} recipes.")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        for entry in tqdm(recipes):
            rid = entry.get('id')
            cur.execute(
                "INSERT INTO recipe_data (id, data) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                (rid, json.dumps(entry))
            )
        conn.commit()
        print(f"{json_path}: Recipe data inserted into DB.")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def insert_petpoison_data_json(json_path: str):
    conn = None
    cur = None
    try:
        with open(json_path, 'r') as f:
            poisons = json.load(f)
        print(f"{json_path}: Loaded {len(poisons)} pet poison entries.")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        for entry in tqdm(poisons):
            name = entry.get('name')
            alt_names = entry.get('alternate_names') or []
            poison_desc = entry.get('poison_description', '')
            desktop_thumb = entry.get('desktop_thumb', '')
            cur.execute(
                "INSERT INTO pet_poisons (name, alternate_names, poison_description, desktop_thumb) VALUES (%s, %s, %s, %s)",
                (name, alt_names, poison_desc, desktop_thumb)
            )
        conn.commit()
        print(f"{json_path}: Pet poison data inserted into DB.")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def insert_recipe_pkl(rec_embeds_path: str, rec_ids_path: str):
    conn = None
    cur = None
    try:
        with open(rec_embeds_path, 'rb') as f:
            rec_embeds = pickle.load(f)
        print(f"{rec_embeds_path}: Embedding shape={rec_embeds.shape}")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        # Load rec_ids first to ensure indices match
        with open(rec_ids_path, 'rb') as f:
            rec_ids = pickle.load(f)
        for idx, rid in enumerate(tqdm(rec_ids)):
            emb = rec_embeds[idx]
            emb_list = emb.tolist() if isinstance(emb, np.ndarray) else emb
            cur.execute(
                "INSERT INTO rec_embeds (id, embedding) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                (rid, emb_list)
            )
        conn.commit()
        print(f"{rec_embeds_path}: Embedding data inserted into DB.")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    
    insert_layer_json('/app/layer1.json')
    insert_recipe_pkl('/app/rec_embeds.pkl', '/app/rec_ids.pkl')
    insert_petpoison_data_json('/app/petpoison_data.json')
