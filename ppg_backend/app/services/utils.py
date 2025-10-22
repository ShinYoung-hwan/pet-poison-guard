import json
import logging
import os
from types import SimpleNamespace
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config_as_namespace(config_path: Optional[str] = None) -> SimpleNamespace:
    """Locate and load a JSON config file into a SimpleNamespace.

    The lookup order is:
    1. Explicit `config_path` argument
    2. Path from `PPG_CONFIG_PATH` environment variable
    3. A `snapshots/config.json` next to this module
    4. A project-relative path at `ppg_backend/app/services/snapshots/config.json`
    5. Container path `/app/ppg_backend/app/services/snapshots/config.json`

    Args:
        config_path: Optional explicit path to the config JSON file.

    Returns:
        SimpleNamespace built from the JSON object.

    Raises:
        FileNotFoundError: when no candidate file exists.
        json.JSONDecodeError: when the file contents are not valid JSON.
    """
    candidates: List[Path] = []
    if config_path:
        candidates.append(Path(config_path))
    else:
        env_path = os.environ.get("PPG_CONFIG_PATH")
        if env_path:
            candidates.append(Path(env_path))

        module_snap = Path(__file__).parent / "snapshots" / "config.json"
        candidates.append(module_snap)

        # project-root relative candidate (defensive)
        base_dir = Path(__file__).resolve().parents[3]
        candidates.append(base_dir / "ppg_backend" / "app" / "services" / "snapshots" / "config.json")

        # common container location
        candidates.append(Path("/app/ppg_backend/app/services/snapshots/config.json"))

    tried: List[str] = []
    for p in candidates:
        tried.append(str(p))
        if p.is_file():
            try:
                with p.open("r", encoding="utf-8") as fh:
                    config_dict = json.load(fh)
                return SimpleNamespace(**config_dict)
            except json.JSONDecodeError:
                logger.exception("Config file exists but contains invalid JSON: %s", p)
                raise

    raise FileNotFoundError(f"Config file not found. Tried paths: {tried}")


def get_max_file_size(config: Optional[SimpleNamespace] = None) -> int:
    """Return the configured max file size in bytes.

    If a config object is not provided the function will attempt to load the
    configuration using :func:`load_config_as_namespace`. On any recoverable
    error a safe default of 5 MiB is returned.
    """

    DEFAULT = 5 * 1024 * 1024

    # Load config 
    if config is None:
        try:
            cfg = load_config_as_namespace()
        except FileNotFoundError:
            logger.info("Config file not found; using default max file size %d", DEFAULT)
            return DEFAULT
        except json.JSONDecodeError:
            logger.warning("Config is invalid JSON; using default max file size %d", DEFAULT)
            return DEFAULT
        except Exception:
            logger.exception("Unexpected error loading config; using default max file size %d", DEFAULT)
            return DEFAULT
    else:
        cfg = config

    # Extract max_file_size
    try:
        return int(getattr(cfg, "max_file_size", DEFAULT))
    except (TypeError, ValueError):
        logger.warning("Invalid max_file_size value in config; using default %d", DEFAULT)
        return DEFAULT