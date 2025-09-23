import os
import time
import asyncio
from .snapshots.utils import load_config_as_namespace

import numpy as np
import torch
from torch import nn
from typing import List, Dict, Union
import logging
import tempfile
import time
from PIL import Image
import torchvision.transforms as transforms

from .snapshots.trijoint import im2recipe
from .db_service import find_poisons_in_recipe, find_top_k_recipes
from ..models.db_session import AsyncSessionLocal

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

async def request_ai_analysis(file: tuple, timeout: float = 15.0, top_k: int = 10) -> List[Dict[str, str]]:
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
    
    # instead of using get_db()
    async with AsyncSessionLocal() as db:
        try:
            topk = await find_top_k_recipes(db, query_emb, top_k=top_k)
            poisons = await find_poisons_in_recipe(db, topk)
            return poisons
        finally:
            await db.close() # Actually, async with automatically close it.