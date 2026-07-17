from functools import lru_cache

from .client import LLMClient


@lru_cache
def get_llm_client():

    return LLMClient()


def reset_llm_client_cache() -> None:
    """
    清除 LLMClient 单例缓存。

    修改 .env 或 LLMClient 实现后，若未重启 uvicorn，可主动调用。
    """

    get_llm_client.cache_clear()