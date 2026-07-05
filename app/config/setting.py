from functools import lru_cache
import os
from app.core.logger import logger
from pathlib import Path

import yaml
from dotenv import load_dotenv
import re

load_dotenv()

_CONFIG_PATH = Path(__file__).parent/"agent.yaml"

_ENV_PATTERN = re.compile(r"\${([A-Z0-9_]+)\}")

def _resolve_env_vars(value):
    if isinstance(value, str):
        def replace(match):
            env_name = match.group(1)
            env_value = os.getenv(env_name)
            if env_value is None:
                logger.warning(f"Environment variable {env_name} is not set")
                return ""
            return env_value
        return _ENV_PATTERN.sub(replace, value)
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value

class Settings:
    def __init__(self, config_path:Path = _CONFIG_PATH):
        with open(config_path,"r",encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        self._config = _resolve_env_vars(raw)
        logger.info(f"Settings loaded from {config_path}")

    @property
    def guardrails(self)->dict:
        return self._config["guardrails"]

    @property
    def research(self):
        return self._config["research"]
    
    @property
    def pii_masking(self):
        return self._config["pii_masking"]
    
    @property
    def evaluation(self):
        return self._config["evaluation"]
    
    @property
    def postgres(self):
        return self._config["postgre"]
    
    @property
    def opensearch(self):
        return self._config["opensearch"]
    
    @property
    def bedrock(self):
        return self._config["bedrock"]
    
    def postgres_dsn(self) -> str:
        pg = self.postgres
        return (
            f"host={pg["host"]} port={pg["port"]} dbname={pg["database"]} "
            f"user={pg["user"]} password={pg["password"]}"
        )


@lru_cache(maxsize=1)
def get_settings()->Settings:
    return Settings()


settings = get_settings()