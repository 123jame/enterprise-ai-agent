from app.memory.base import BaseMemory
from app.memory.inmemory import InMemory


class MemoryRegistry:

    _registry: dict[
        str,
        type[BaseMemory]
    ] = {}

    @classmethod
    def register(

        cls,

        name: str,

        memory_cls: type[BaseMemory]

    ):

        cls._registry[name] = memory_cls

    @classmethod
    def get(

        cls,

        name: str

    ) -> type[BaseMemory]:

        if name not in cls._registry:

            raise ValueError(

                f"Unknown Memory: {name}"

            )

        return cls._registry[name]


MemoryRegistry.register(

    "inmemory",

    InMemory

)