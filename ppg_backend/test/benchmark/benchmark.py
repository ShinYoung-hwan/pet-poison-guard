import argparse
import json
import pickle
import numpy as np
import logging
from tqdm import tqdm
import os
from typing import List


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
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_pickle(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(
    img_embeds_path: str,
    rec_embeds_path: str,
    img_ids_path: str,
    rec_ids_path: str,
    petpoison_path: str,
    layer1_path: str,
) -> None:
    """Run the recall@k benchmark using the provided file paths.

    The function preserves the original behaviour but accepts explicit file
    paths so it can be used in CI or from the command line with custom data.
    """
    logger.info("Loading data files...")
    img_embeds = load_pickle(img_embeds_path)
    rec_embeds = load_pickle(rec_embeds_path)
    _img_ids = load_pickle(img_ids_path)  # unused by this benchmark but kept for completeness
    rec_ids = load_pickle(rec_ids_path)

    logger.info("Loading poison database and recipes...")
    poison_db = load_json(petpoison_path)
    recipes = load_json(layer1_path)

    poison_keywords = set()
    for item in poison_db:
        if item.get("name"):
            poison_keywords.add(item["name"].lower())
        if item.get("scientific_name"):
            poison_keywords.add(item["scientific_name"].lower())
        for alt in item.get("alternate_names", []) or []:
            if alt:
                poison_keywords.add(alt.lower())

    danger_recipe_ids: List[str] = []
    for recipe in tqdm(recipes, desc="Scanning recipes"):
        text = (
            " ".join([ing.get("text", "") for ing in recipe.get("ingredients", [])])
            + " "
            + recipe.get("title", "")
            + " "
            + recipe.get("description", "")
        )
        text = text.lower()
        if any(keyword in text for keyword in poison_keywords):
            danger_recipe_ids.append(recipe["id"])

    top_k_list = [1, 5, 10]
    recall_at_k = {k: 0 for k in top_k_list}
    total = len(img_embeds)

    logger.info("Start recall@k evaluation for %d images.", total)
    for img_embed in tqdm(img_embeds, desc="Processing images"):
        sims = np.dot(rec_embeds, img_embed) / (
            np.linalg.norm(rec_embeds, axis=1) * np.linalg.norm(img_embed) + 1e-8
        )
        sorted_idx = np.argsort(sims)[::-1]
        for k in top_k_list:
            topk_rec_ids = [rec_ids[idx] for idx in sorted_idx[:k]]
            if any(rec_id in danger_recipe_ids for rec_id in topk_rec_ids):
                recall_at_k[k] += 1

    logger.info("Recall@k results:")
    for k in top_k_list:
        recall = recall_at_k[k] / total if total > 0 else 0
        logger.info("  Recall@%d: %.4f", k, recall)


def default_paths() -> dict:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ppg_database/data"))
    return {
        "img_embeds": os.path.join(base_dir, "img_embeds.pkl"),
        "rec_embeds": os.path.join(base_dir, "rec_embeds.pkl"),
        "img_ids": os.path.join(base_dir, "img_ids.pkl"),
        "rec_ids": os.path.join(base_dir, "rec_ids.pkl"),
        "petpoison": os.path.join(base_dir, "petpoison_data.json"),
        "layer1": os.path.join(base_dir, "layer1.json"),
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Run recall@k benchmark for Pet Poison Guard")
    defs = default_paths()
    parser.add_argument("--img-embeds", default=defs["img_embeds"], help="Path to img_embeds.pkl")
    parser.add_argument("--rec-embeds", default=defs["rec_embeds"], help="Path to rec_embeds.pkl")
    parser.add_argument("--img-ids", default=defs["img_ids"], help="Path to img_ids.pkl")
    parser.add_argument("--rec-ids", default=defs["rec_ids"], help="Path to rec_ids.pkl")
    parser.add_argument("--petpoison", default=defs["petpoison"], help="Path to petpoison_data.json")
    parser.add_argument("--layer1", default=defs["layer1"], help="Path to layer1.json")
    return parser.parse_args()


def main():
    args = _parse_args()
    run_benchmark(
        args.img_embeds,
        args.rec_embeds,
        args.img_ids,
        args.rec_ids,
        args.petpoison,
        args.layer1,
    )


if __name__ == "__main__":
    main()