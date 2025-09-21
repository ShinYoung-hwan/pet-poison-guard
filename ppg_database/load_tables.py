#!/usr/bin/env python3
import pickle
import psycopg2
import numpy as np
import json
from tqdm import tqdm

# --- 설정 (본인의 환경에 맞게 수정) ---
DB_HOST = "/var/run/postgresql"
DB_PORT = "8001" # 이전에 설정한 포트
DB_NAME = "postgres" # 기본값, docker-compose 등에서 설정했다면 변경
DB_USER = "postgres" # 기본값, docker-compose 등에서 설정했다면 변경
DB_PASSWORD = "mysecretpassword" # docker run 실행 시 설정한 비밀번호

def insert_layer_json(json_path: str):
    conn = None
    cur = None
    try:
        with open(json_path, 'r') as f:
            recipes = json.load(f)
        print(f"{json_path}: {len(recipes)}개 레시피 로드.")
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
        print(f"{json_path}: DB에 레시피 데이터 삽입 완료.")
    except Exception as e:
        print(f"오류: {e}")
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
        print(f"{json_path}: {len(poisons)}개 pet poison 로드.")
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
        print(f"{json_path}: DB에 pet poison 데이터 삽입 완료.")
    except Exception as e:
        print(f"오류: {e}")
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
        print(f"{rec_embeds_path}: 임베딩 shape={rec_embeds.shape}")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        # rec_ids와 인덱스가 맞아야 하므로, rec_ids를 먼저 불러옴
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
        print(f"{rec_embeds_path}: DB에 임베딩 데이터 삽입 완료.")
    except Exception as e:
        print(f"오류: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    
    insert_layer_json('/app/layer1.json')
    insert_petpoison_data_json('/app/petpoison_data.json')
    insert_recipe_pkl('/app/rec_embeds.pkl', '/app/rec_ids.pkl')
