import time
import asyncio
from typing import Optional
from types import SimpleNamespace

from .utils import load_config_as_namespace

import numpy as np
import torch
from torch import nn

from fastapi.logger import logger
from .exceptions import AIServiceError

from PIL import Image, UnidentifiedImageError
import torchvision.transforms as transforms

from .encoders.trijoint import im2recipe

# Module-level state
model: Optional[nn.Module] = None
device: Optional[torch.device] = None
_opts: Optional[SimpleNamespace] = None


def _get_opts(config_path: Optional[str] = None) -> SimpleNamespace:
    """Lazily load and cache options from config file.

    This prevents import-time failures when the config is missing in some
    environments (tests, container build steps, etc.).
    """
    global _opts
    if _opts is None:
        _opts = load_config_as_namespace(config_path)
    return _opts


def load_model(config_path: Optional[str] = None) -> None:
    """Load the AI model and move it to the selected device.

    Args:
        config_path: Optional override path for the config file used to load
            model parameters (e.g. `model_path`, `seed`).

    Raises:
        AIServiceError: on any error during model creation or checkpoint load.
    """
    global model, device
    try:
        opts = _get_opts(config_path)
        seed = int(getattr(opts, "seed", 42))
        torch.manual_seed(seed)
        np.random.seed(seed)

        # Prefer CUDA when available
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")

        logger.info("Loading model to %s...", device)
        model = im2recipe()
        model.to(device)

        model_path = getattr(opts, "model_path", None)
        if not model_path:
            raise AIServiceError("Model path not configured in config.json")

        logger.info("Loading checkpoint from %s ...", model_path)
        t0 = time.time()
        # map_location ensures CPU-only environments don't error
        map_loc = "cpu" if device.type == "cpu" else None
        checkpoint = torch.load(model_path, encoding="latin1", weights_only=False, map_location=map_loc)
        model.load_state_dict(checkpoint["state_dict"], strict=False)
        model.eval()
        logger.info("Model loaded. (elapsed: %.2fs)", time.time() - t0)
    except AIServiceError:
        raise
    except Exception as e:  # pragma: no cover - hard to simulate all torch errors here
        logger.exception("Failed to load model: %s", e)
        raise AIServiceError(str(e)) from e


async def analyze_image_async(image_path: str, timeout: float = 15.0) -> np.ndarray:
    """Run image embedding extraction in a threadpool and return the vector.

    Args:
        image_path: Path to an image file on disk.
        timeout: Unused currently but kept for API compatibility.

    Returns:
        Numpy array embedding.

    Raises:
        AIServiceError: when image processing or model inference fails.
    """
    loop = asyncio.get_running_loop()
    try:
        emb = await loop.run_in_executor(None, image_to_embedding, image_path)
        return emb
    except AIServiceError:
        raise
    except Exception as e:
        logger.exception("AI inference failed: %s", e)
        raise AIServiceError(str(e)) from e


def image_to_embedding(image_path: str) -> np.ndarray:
    """Load an image, run model forward and return a 1-D numpy embedding.

    Raises AIServiceError for any domain-specific problems so callers can
    uniformly handle AI failures.
    """
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        normalize,
    ])
    logger.info("Loading and transforming image: %s", image_path)
    t0 = time.time()
    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError as e:
        logger.error("Image file not found: %s", image_path)
        raise AIServiceError(f"Image file not found: {image_path}") from e
    except UnidentifiedImageError as e:
        logger.error("Cannot identify image file: %s", image_path)
        raise AIServiceError(f"Cannot identify image file: {image_path}") from e
    except Exception as e:
        logger.exception("Unexpected error opening image %s", image_path)
        raise AIServiceError(str(e)) from e

    img_tensor = transform(img)
    if not isinstance(img_tensor, torch.Tensor):
        raise AIServiceError("Transform did not return a tensor")

    if device is None or model is None:
        raise AIServiceError("Model is not loaded. Call load_model() before inference.")

    img_tensor = img_tensor.unsqueeze(0).to(device)
    logger.info("Image loaded and transformed. (elapsed: %.2fs)", time.time() - t0)
    logger.info("Running model to extract vision embedding only...")
    t0 = time.time()
    try:
        with torch.no_grad():
            visual_emb = model(img_tensor)
    except Exception as e:
        logger.exception("Model inference failed: %s", e)
        raise AIServiceError(str(e)) from e

    logger.info("Vision embedding extracted. (elapsed: %.2fs)", time.time() - t0)
    return visual_emb.cpu().numpy()[0]
