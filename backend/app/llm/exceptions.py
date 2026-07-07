class LLMException(Exception):
    """LLM 基础异常"""
    pass


class LLMAuthenticationError(LLMException):
    """认证失败"""
    pass


class LLMConnectionError(LLMException):
    """连接失败"""
    pass


class LLMTimeoutError(LLMException):
    """请求超时"""
    pass