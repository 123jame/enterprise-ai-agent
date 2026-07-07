class MemoryError(Exception):
    """
    Memory基础异常
    """
    pass


class MemoryNotFoundError(MemoryError):
    """
    Memory不存在
    """
    pass