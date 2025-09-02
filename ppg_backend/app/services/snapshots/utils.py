import json
from types import SimpleNamespace
import os

def load_config_as_namespace(config_path=None):
    """
    Reads the config.json file and returns its contents as a namespace object.
    :param config_path: Optional path to the config.json file. If None, tries to find config.json in project root.
    :return: SimpleNamespace containing config values.
    """
    if config_path is None:
        # Try to find config.json relative to this file's location
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
        config_path = os.path.join(base_dir, 'ppg_backend/app/services/snapshots/config.json')
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)
    return SimpleNamespace(**config_dict)