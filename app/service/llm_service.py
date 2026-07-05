from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
import boto3

from app.config.setting import settings
from app.core.logger import logger

import os
from dotenv import load_dotenv
load_dotenv()

_cfg = settings.bedrock

@lru_cache(maxsize=1)
def get_openaillm()->ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

@lru_cache(maxsize=1)
def get_bedrockllm()->ChatBedrock:
    _client = boto3.client(
        service_name=_cfg["service"],
        region_name=_cfg["region"]
    )
    
    llm = ChatBedrock(
        model=_cfg["model_id"],
        client=_client,
        model_kwargs={
            "temperature": _cfg["temperature"],
            "max_tokens": _cfg["max_tokens"],
        }
    )
    logger.info(f"ChatBedrock initialised — model={_cfg['model_id']}")
    return llm