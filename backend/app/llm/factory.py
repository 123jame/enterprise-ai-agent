from functools import lru_cache

from .client import LLMClient


@lru_cache
def get_llm_client():

    return LLMClient()