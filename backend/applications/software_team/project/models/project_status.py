from enum import Enum


class ProjectStatus(str, Enum):
    """
    软件开发项目生命周期。

    整个 AI Software Development Team 都围绕该状态流转，
    Coordinator 根据当前状态决定下一步应该调度哪个 Agent。
    """

    # 项目刚创建
    CREATED = "created"

    # 产品分析阶段
    PLANNING = "planning"

    # 系统设计阶段
    DESIGNING = "designing"

    # 软件开发阶段
    DEVELOPING = "developing"

    # 测试阶段
    TESTING = "testing"

    # Code Review 阶段
    REVIEWING = "reviewing"

    # 整理交付物
    DELIVERING = "delivering"

    # 项目完成
    FINISHED = "finished"

    # 项目失败
    FAILED = "failed"