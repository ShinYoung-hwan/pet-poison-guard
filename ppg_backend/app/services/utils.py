import json
from types import SimpleNamespace
import os

def load_config_as_namespace(config_path=None):
    """
    Reads the config.json file and returns its contents as a namespace object.
    :param config_path: Optional path to the config.json file. If None, tries to find config.json in several common locations.
    :return: SimpleNamespace containing config values.
    """
    tried_paths = []
    if config_path is not None:
        tried_paths.append(config_path)
    else:
        # 1. 환경변수
        env_path = os.environ.get('PPG_CONFIG_PATH')
        if env_path:
            tried_paths.append(env_path)
        # 2. 현재 파일 기준 상대 경로
        tried_paths.append(os.path.join(os.path.dirname(__file__), 'snapshots/config.json'))
        # 3. 프로젝트 루트 기준
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
        tried_paths.append(os.path.join(base_dir, 'ppg_backend/app/services/snapshots/config.json'))
        # 4. Docker 컨테이너에서 /app 기준 경로 (FastAPI 컨테이너에서 흔히 사용)
        tried_paths.append('/app/ppg_backend/app/services/snapshots/config.json')
    for path in tried_paths:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return SimpleNamespace(**config_dict)
    raise FileNotFoundError(f"Config file not found. Tried paths: {tried_paths}")


# Application constants derived from config
def get_max_file_size(config=None) -> int:
    try:
        cfg = config or load_config_as_namespace()
        return int(getattr(cfg, "max_file_size", 5 * 1024 * 1024))
    except Exception:
        # Fallback default: 5MB
        return 5 * 1024 * 1024