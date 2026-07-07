from abc import ABC
from abc import abstractmethod

from app.agents.types import AgentContext
from app.agents.types import AgentResult

from app.memory.manager import MemoryManager


class BaseAgent(ABC):
    """
    所有 Agent 的抽象基类
    """

    def __init__(self):

        self.memory = MemoryManager()

    def before_run(
        self,
        context: AgentContext
    ) -> None:
        """
        执行前钩子，子类可覆写。

        Memory 加载已由 PromptBuilder 负责（T7.3），
        Agent 无需在此访问 Memory。
        """

        pass

    @abstractmethod
    def execute(
        self,
        context: AgentContext
    ) -> AgentResult:
        """
        子类必须实现
        """
        pass

    def after_run(
        self,
        context: AgentContext,
        result: AgentResult
    ) -> None:
        """
        执行后：
        保存聊天记录
        """

        self.memory.save_user_message(

            context.session_id,

            context.user_message

        )

        self.memory.save_assistant_message(

            context.session_id,

            result.content

        )

    def run(
        self,
        context: AgentContext
    ) -> AgentResult:
        """
        Agent 生命周期
        """

        self.before_run(
            context
        )

        result = self.execute(
            context
        )

        self.after_run(
            context,
            result
        )

        return result