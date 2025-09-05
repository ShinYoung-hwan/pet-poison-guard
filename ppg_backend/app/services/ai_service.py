import os
import asyncio
from .snapshots.utils import load_config_as_namespace
from typing import List, Dict, Any

# Global variables for data and model
# TODO: global variables should be managed better, e.g., using database or cache
semaphore = asyncio.Semaphore(1)  # only one request at a time
model = None
rec_embeds = None
rec_ids = None
device = None
opts = load_config_as_namespace()

# Global variable for recipe data
recipe_data_by_id = None

# Global Variable for pet poison datas
pet_poisons: List[Dict] = None

is_globals_loaded = lambda : all(v is not None for v in [model, rec_embeds, rec_ids, device, opts, recipe_data_by_id, pet_poisons])

import torch
import torch.nn as nn
import torchvision.transforms as transforms
import numpy as np
import pickle
from PIL import Image
import logging
import tempfile
import time
import json
from .snapshots.trijoint import im2recipe

def load_globals():
    global model, rec_embeds, rec_ids, opts, device, recipe_data_by_id, pet_poisons
    if is_globals_loaded():
        logging.info("Globals already loaded.")
        return
    logging.info("Parsing arguments and loading model configuration...")
    torch.manual_seed(opts.seed)
    np.random.seed(opts.seed)
    if not(torch.cuda.device_count()):
        device = torch.device(*('cpu',0))
    else:
        torch.cuda.manual_seed(opts.seed)
        device = torch.device(*('cuda',0))
    logging.info(f"Loading model to {device}...")
    model = im2recipe()
    model.visionMLP = torch.nn.DataParallel(model.visionMLP)
    model.to(device)
    logging.info(f"Loading checkpoint from {opts.model_path} ...")
    t0 = time.time()
    if device.type=='cpu':
        checkpoint = torch.load(opts.model_path, encoding='latin1', weights_only=False, map_location='cpu')
    else:
        checkpoint = torch.load(opts.model_path, encoding='latin1', weights_only=False)
    model.load_state_dict(checkpoint['state_dict'], strict=False)
    model.eval()
    logging.info(f"Model loaded. (elapsed: {time.time()-t0:.2f}s)")
    # Load embeddings and ids
    logging.info("Loading image and recipe embeddings...")
    t0 = time.time()
    with open(os.path.join(opts.path_results, 'rec_embeds.pkl'), 'rb') as f:
        rec_embeds = pickle.load(f)
    with open(os.path.join(opts.path_results, 'rec_ids.pkl'), 'rb') as f:
        rec_ids = pickle.load(f)
    logging.info(f"Embeddings loaded. (elapsed: {time.time()-t0:.2f}s)")
    # Load recipe data
    logging.info(f"Loading recipe data from {opts.recipe_path} ...")
    t0 = time.time()
    with open(opts.recipe_path, 'r') as f:
        recipes = json.load(f)
    recipe_data_by_id = {entry['id']: entry for entry in recipes}
    elapsed = time.time() - t0
    logging.info(f"Loaded {len(recipe_data_by_id)} recipes into memory. (elapsed: {elapsed:.2f}s)")
    # Load pet poison data
    logging.info(f"Loading pet poison data from {opts.pet_poison_path} ...")
    t0 = time.time()
    with open(opts.pet_poison_path, 'r') as f:
        pet_poisons = json.load(f)
    for entry in pet_poisons:
        entry['name'] = entry['name'].lower()
        if 'alternate_names' in entry:
            if entry['alternate_names'] is None:
                entry['alternate_names'] = []
            else:
                entry['alternate_names'] = [name.lower() for name in entry['alternate_names'] if name]
    elapsed = time.time() - t0
    logging.info(f"Loaded {len(pet_poisons)} pet poison items into memory. (elapsed: {elapsed:.2f}s)")
    logging.info("All globals loaded.")

def image_to_embedding(image_path):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        normalize,
    ])
    logging.info(f"Loading and transforming image: {image_path}")
    t0 = time.time()
    img = Image.open(image_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0).to(device)
    logging.info(f"Image loaded and transformed. (elapsed: {time.time()-t0:.2f}s)")
    logging.info("Running model to extract vision embedding only...")
    t0 = time.time()
    with torch.no_grad():
        visual_emb = model(img_tensor)
    logging.info(f"Vision embedding extracted. (elapsed: {time.time()-t0:.2f}s)")
    return visual_emb.cpu().numpy()[0]  # (embedding vector)

def find_top_k_recipes(query_emb, top_k=5):
    # Cosine similarity
    sim = np.dot(rec_embeds, query_emb) / (np.linalg.norm(rec_embeds, axis=1) * np.linalg.norm(query_emb) + 1e-8)
    topk_idx = np.argsort(sim)[-top_k:][::-1]
    topk_recipes = [(rec_ids[i], float(sim[i])) for i in topk_idx]
    return topk_recipes

async def request_ai_analysis(file: tuple, timeout: float = 15.0, top_k: int = 10) -> dict:
    # TODO: top_k를 client로부터 입력받기
    """
    file: tuple (filename, fileobj, content_type)
    Returns: dict with top_k recipe ids and scores
    """
    global model, rec_embeds, rec_ids, opts, device
    async with semaphore:
        # Save uploaded file to a temporary file
        filename, fileobj, content_type = file
        with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(filename)[-1]) as tmp:
            tmp.write(fileobj)
            tmp.flush()
            # Compute embedding
            query_emb = image_to_embedding(tmp.name)
        # Find top-k recipes
        topk = find_top_k_recipes(query_emb, top_k=top_k)        

    # Collect all matched poison names from top-k recipes
    poison_names = set()
    for rid, score in topk:
        recipe_data = recipe_data_by_id.get(rid, None)
        if not recipe_data:
            continue
        ingredients = recipe_data.get("ingredients", [])
        ingredients_lower = ', '.join([ ingredient['text'] for ingredient in ingredients ]).lower()
        print(ingredients_lower)
        # check poison name vs ingredient names
        for entry in pet_poisons:
            if entry["name"] in ingredients_lower:
                poison_names.add(entry["name"])
            if 'alternate_names' in entry and entry['alternate_names']:
                for alt_name in entry['alternate_names']:
                    if alt_name in ingredients_lower:
                        poison_names.add(alt_name)

    # Return as dict in requested format
    return {"result": list(poison_names)}

