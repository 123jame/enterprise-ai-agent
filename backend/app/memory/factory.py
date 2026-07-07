import os

from app.memory.base import BaseMemory
from app.memory.registry import MemoryRegistry


_memory_instance: BaseMemory | None = None


def get_memory() -> BaseMemory:

    global _memory_instance

    if _memory_instance is not None:

        return _memory_instance

    provider = os.getenv(

        "MEMORY_PROVIDER",

        "inmemory"

    )

    memory_cls = MemoryRegistry.get(

        provider

    )

    _memory_instance = memory_cls()

    return _memory_instance