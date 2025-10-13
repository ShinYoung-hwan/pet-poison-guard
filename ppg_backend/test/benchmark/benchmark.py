import json
import pickle
import numpy as np
import logging
from tqdm import tqdm
import os

# TODO : Refactor : wrap this into function & load file paths from arguments
# --- IGNORE ---
"""
6 files are required to run this benchmark code:
* Running test.py im2recipe-Pytorch will generate following pkl files
    -  img_embeds.pkl
    -  rec_embeds.pkl
    -  img_ids.pkl
    -  rec_ids.pkl

* Download following json files from recipe1M
    -  layer1.json

* Generate your own petpoison_data.json
    -  petpoison_data.json
"""
# --- IGNORE ---

# 0. logger 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 1. 결과 파일 로드
logging.info("Loading data files...")
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../ppg_database/data'))
with open(os.path.join(base_dir, 'img_embeds.pkl'), 'rb') as f:
    img_embeds = pickle.load(f)
with open(os.path.join(base_dir, 'rec_embeds.pkl'), 'rb') as f:
    rec_embeds = pickle.load(f)
with open(os.path.join(base_dir, 'img_ids.pkl'), 'rb') as f:
    img_ids = pickle.load(f)
with open(os.path.join(base_dir, 'rec_ids.pkl'), 'rb') as f:
    rec_ids = pickle.load(f)

# 2. 위험 키워드 리스트 추출
logging.info("Loading poison database and extracting keywords...")
with open(os.path.join(base_dir,'petpoison_data.json'), 'r') as f:
    poison_db = json.load(f)
with open(os.path.join(base_dir,'layer1.json'), 'r') as f:
    recipes = json.load(f)

poison_keywords = set()
for item in poison_db:
    if 'name' in item and item['name']:
        poison_keywords.add(item['name'].lower())
    if 'scientific_name' in item and item['scientific_name']:
        poison_keywords.add(item['scientific_name'].lower())
    if 'alternate_names' in item and item['alternate_names']:
        for alt in item['alternate_names']:
            poison_keywords.add(alt.lower())

# 3. 레시피 데이터에서 위험 키워드 포함 여부 확인
# 예시: 레시피 데이터가 [{'id': ..., 'ingredients': [...], 'title': ..., ...}, ...] 형태라고 가정
danger_recipe_ids = []
for recipe in tqdm(recipes):  # recipes는 test partition의 레시피 리스트
    text =  ' '.join([ ing.get("text", "") for ing in recipe.get('ingredients', []) ]) \
            + ' ' + recipe.get('title', '') \
            + ' ' + recipe.get('description', '')
    text = text.lower()
    if any(keyword in text for keyword in poison_keywords):
        danger_recipe_ids.append(recipe['id'])

# 4. 이미지별 top-k 검색 (진행바)
top_k_list = [1, 5, 10]
recall_at_k = {k: 0 for k in top_k_list}
total = len(img_embeds)

logger.info(f"Start recall@k evaluation for {total} images.")
for i, img_embed in enumerate(tqdm(img_embeds, desc="Processing images")):
    sims = np.dot(rec_embeds, img_embed) / (np.linalg.norm(rec_embeds, axis=1) * np.linalg.norm(img_embed) + 1e-8)
    sorted_idx = np.argsort(sims)[::-1]
    for k in top_k_list:
        topk_rec_ids = [rec_ids[idx] for idx in sorted_idx[:k]]
        if any(rec_id in danger_recipe_ids for rec_id in topk_rec_ids):
            recall_at_k[k] += 1

logger.info("Recall@k results:")
for k in top_k_list:
    recall = recall_at_k[k] / total if total > 0 else 0
    logger.info(f"  Recall@{k}: {recall:.4f}")