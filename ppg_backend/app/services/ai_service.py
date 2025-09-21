import os
import time
import asyncio
from .snapshots.utils import load_config_as_namespace

import numpy as np
import torch
from torch import nn
from typing import List, Dict, Any, Union
import logging
import tempfile
import time
from PIL import Image
import torchvision.transforms as transforms
from sqlalchemy.orm import Session

from .snapshots.trijoint import im2recipe
from ..models.db_models import RecipeData, RecEmbed, PetPoison

# Only keep model and device as globals
semaphore = asyncio.Semaphore(1)
model: Union[nn.Module, None] = None
device: Union[torch.device, None] = None
opts = load_config_as_namespace()

def load_model():
    global model, device, opts
    torch.manual_seed(opts.seed)
    np.random.seed(opts.seed)
    if not(torch.cuda.device_count()):
        device = torch.device(*('cpu',0))
    else:
        torch.cuda.manual_seed(opts.seed)
        device = torch.device(*('cuda',0))
    
    # Load model
    logging.info(f"Loading model to {device}...")
    model = im2recipe()
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
    img_tensor = transform(img)
    if not isinstance(img_tensor, torch.Tensor):
        raise TypeError("Transform did not return a tensor")
    img_tensor = img_tensor.unsqueeze(0).to(device)
    logging.info(f"Image loaded and transformed. (elapsed: {time.time()-t0:.2f}s)")
    logging.info("Running model to extract vision embedding only...")
    t0 = time.time()
    if model is None or device is None:
        raise ValueError("Model or device not initialized. Call load_model() first.")
    with torch.no_grad():
        visual_emb = model(img_tensor)
    logging.info(f"Vision embedding extracted. (elapsed: {time.time()-t0:.2f}s)")
    return visual_emb.cpu().numpy()[0]

def find_top_k_recipes(db: Session, query_emb, top_k=5):
    t0 = time.time()

    # Fetch embeddings and ids from DB
    embeds = db.query(RecEmbed).all()

    # Ensure each embedding is a numpy array of shape (1024,)
    rec_embeds = np.stack([np.array(e.embedding) for e in embeds])  # shape: (N, 1024)
    rec_ids = [e.id for e in embeds]

    sim = np.dot(rec_embeds, query_emb) / (np.linalg.norm(rec_embeds, axis=1) * np.linalg.norm(query_emb) + 1e-8)
    topk_idx = np.argsort(sim)[-top_k:][::-1]
    topk_recipes = [(rec_ids[i], float(sim[i])) for i in topk_idx]

    t = time.time()
    logging.info(f"Top-{top_k} recipes found on db. (elapsed: {t - t0:.2f}s)")

    return topk_recipes

async def request_ai_analysis(db: Session, file: tuple, timeout: float = 15.0, top_k: int = 1) -> List[Dict[str, str]]:
    """
    file: tuple (filename, fileobj, content_type)
    Returns: list of dicts [{"name": ..., "image": ..., "description": ...}], sorted by similarity descending
    """
    async with semaphore:
        filename, fileobj, content_type = file
        with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(filename)[-1]) as tmp:
            tmp.write(fileobj)
            tmp.flush()
            query_emb = image_to_embedding(tmp.name)
            topk = find_top_k_recipes(db, query_emb, top_k=top_k)

    result = []
    for rid, score in topk:
        recipe_row = db.query(RecipeData).filter(RecipeData.id == rid).first()
        if not recipe_row:
            continue
        recipe_data = recipe_row.data
        ingredients = recipe_data.get("ingredients", [])
        ingredients_lower = ', '.join([ingredient['text'] for ingredient in ingredients]).lower()
        matched_poison = None
        poison_entry = None
        poisons = db.query(PetPoison).all()
        for entry in poisons:
            entry_dict = entry.__dict__ if hasattr(entry, '__dict__') else entry
            name_val = entry_dict.get('name', None)
            name = name_val.lower() if name_val else ""
            if name and name in ingredients_lower:
                matched_poison = name
                poison_entry = entry
                break
            alt_names = entry_dict.get('alternate_names', []) or []
            for alt_name in alt_names:
                if alt_name and isinstance(alt_name, str) and alt_name.lower() in ingredients_lower:
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

