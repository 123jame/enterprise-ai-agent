"""
P6 验证与重试测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_verification
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from app.agents.types import AgentResult

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.execution.execution_result import ExecutionResult
from applications.software_team.execution.retry_policy import RetryPolicy
from applications.software_team.execution.verification_manager import (
    VerificationManager,
)
from applications.software_team.execution.verification_result import CheckResult
from applications.software_team.execution.verification_result import (
    VerificationCheckType,
)
from applications.software_team.execution.verification_result import VerificationResult


def _write_backend(root: Path) -> None:

    backend = root / "backend"
    backend.mkdir(parents=True, exist_ok=True)

    (backend / "main.py").write_text(
        '''
from fastapi import FastAPI
app = FastAPI(title="Test")
'''.strip()
        + "\n",
        encoding="utf-8",
    )

    (backend / "requirements.txt").write_text(
        "fastapi\n",
        encoding="utf-8",
    )


def test_verification_manager_backend_pass() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _write_backend(root)

        manager = VerificationManager(
            settings=SoftwareTeamSettings(enable_type_check=False),
        )

        result = manager.verify(root, target="backend")

        assert result.success is True
        assert any(
            check.check_type == VerificationCheckType.STRUCTURE
            for check in result.checks
        )


def test_verification_manager_document_missing() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        manager = VerificationManager()
        result = manager.verify_document_path(
            root,
            "docs/PRD.md",
        )

        assert result.success is False


def test_retry_policy_stops_at_max() -> None:

    policy = RetryPolicy(
        settings=SoftwareTeamSettings(max_verification_retries=3),
    )

    failed = VerificationResult(
        success=False,
        workspace_path="/tmp",
        error_log="test error",
    )

    decision = policy.evaluate(
        attempt=2,
        verification=failed,
    )

    assert decision.should_retry is True

    decision = policy.evaluate(
        attempt=3,
        verification=failed,
    )

    assert decision.should_retry is False


def test_retry_policy_build_fix_instruction() -> None:

    policy = RetryPolicy()

    feedback = policy.build_feedback(
        agent_name="BackendAgent",
        target="backend",
        attempt=1,
        verification=VerificationResult(
            success=False,
            workspace_path="/tmp",
            target="backend",
            error_log="import failed",
        ),
        execution=ExecutionResult(
            success=False,
            workspace_path="/tmp",
            stderr="ModuleNotFoundError",
        ),
    )

    instruction = policy.build_fix_instruction(feedback)

    assert "修复" in instruction
    assert "import failed" in instruction


def test_pipeline_verification_retry_logic() -> None:

    from applications.software_team.workflow.pipeline import SoftwareTeamPipeline
    from applications.software_team.project.models.project import Project
    from applications.software_team.project.models.project_status import (
        ProjectStatus,
    )
    from applications.software_team.project.artifacts.artifact_manager import (
        ArtifactManager,
    )
    from applications.software_team.project.services.project_service import (
        ProjectService,
    )
    from applications.software_team.project.workspace.workspace_manager import (
        WorkspaceManager,
    )

    with tempfile.TemporaryDirectory() as tmp:

        settings = SoftwareTeamSettings(
            enable_verification=True,
            max_verification_retries=2,
            enable_template_fallback=True,
        )

        ws = WorkspaceManager(workspace_root=tmp)
        am = ArtifactManager()
        ps = ProjectService(ws, am)

        project = Project(
            id="p1",
            name="test",
            requirement="test",
            workspace_path=str(ws.create_workspace("test")),
            status=ProjectStatus.PLANNING,
        )
        ps._project = project

        mock_exec = MagicMock()
        mock_exec.execute_target.return_value = ExecutionResult(
            success=False,
            workspace_path=project.workspace_path,
            target="backend",
            error_message="exec fail",
        )

        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=False,
            workspace_path=project.workspace_path,
            target="backend",
            error_log="verify fail",
        )

        pipeline = SoftwareTeamPipeline(
            project_service=ps,
            artifact_manager=am,
            workspace_manager=ws,
            settings=settings,
            execution_manager=mock_exec,
            verification_manager=mock_verify,
        )

        mock_agent = MagicMock()
        mock_agent.run.return_value = AgentResult(
            success=True,
            model="mock",
            content="done",
        )

        from applications.software_team.workflow.dependencies import PipelineStep

        log: list = []
        result = pipeline._run_step_with_verification(
            agent=mock_agent,
            step=PipelineStep(
                agent_name="BackendAgent",
                status=ProjectStatus.DEVELOPING,
            ),
            step_context=MagicMock(session_id="s1"),
            project=project,
            runtime=MagicMock(memory_manager=MagicMock()),
            verification_log=log,
        )

        assert result.success is False
        assert mock_agent.run.call_count >= 2


def main() -> None:

    test_verification_manager_backend_pass()
    test_verification_manager_document_missing()
    test_retry_policy_stops_at_max()
    test_retry_policy_build_fix_instruction()
    test_pipeline_verification_retry_logic()
    print("All P6 verification tests passed.")


if __name__ == "__main__":

    main()
