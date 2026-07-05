import yaml
from pathlib import Path
from functools import lru_cache

_CONFIG_PATH = Path(__file__).parent/"prompt.yaml"

class PromptSettings:
    def __init__(self):
        with open (_CONFIG_PATH , "r" , encoding="utf-8") as f:
            self._config = yaml.safe_load(f)
        
    @property
    def prompt(self):
        return self._config["prompt"]


@lru_cache(maxsize=2)
def get_prompt()->PromptSettings:
    return PromptSettings()

get_prompts = get_prompt()
