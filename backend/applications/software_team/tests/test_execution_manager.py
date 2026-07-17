"""
P6 Step 1 — ExecutionManager 测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_execution_manager
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from applications.software_team.execution.execution_manager import ExecutionManager
from applications.software_team.execution.execution_result import ProjectType


def _write_backend_project(root: Path) -> None:

    backend = root / "backend"
    backend.mkdir(parents=True)

    (backend / "requirements.txt").write_text(
        "fastapi\n",
        encoding="utf-8",
    )

    (backend / "main.py").write_text(
        '''
from fastapi import FastAPI

app = FastAPI(title="Test API")


@app.get("/api/health")
def health():
    return {"status": "ok"}
'''.strip()
        + "\n",
        encoding="utf-8",
    )


def _write_frontend_project(root: Path) -> None:

    frontend = root / "frontend"
    frontend.mkdir(parents=True)

    (frontend / "index.html").write_text(
        "<html><body>Test</body></html>\n",
        encoding="utf-8",
    )


def test_detect_fastapi_backend() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _write_backend_project(root)

        manager = ExecutionManager()
        detected = manager.detect(root)

        assert len(detected) == 1
        assert detected[0].project_type == ProjectType.FASTAPI
        assert detected[0].name == "backend"


def test_execute_fastapi_backend_success() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _write_backend_project(root)

        manager = ExecutionManager()
        result = manager.execute(root)

        assert result.success is True
        assert len(result.sub_results) == 1
        assert result.sub_results[0].project_type == ProjectType.FASTAPI


def test_execute_target_backend() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _write_backend_project(root)
        _write_frontend_project(root)

        manager = ExecutionManager()
        result = manager.execute_target(root, "backend")

        assert result.success is True
        assert result.sub_results[0].target == "backend"


def test_execute_missing_workspace() -> None:

    manager = ExecutionManager()
    result = manager.execute("/path/does/not/exist")

    assert result.success is False
    assert "not found" in result.error_message.lower()


def main() -> None:

    test_detect_fastapi_backend()
    test_execute_fastapi_backend_success()
    test_execute_target_backend()
    test_execute_missing_workspace()
    print("All ExecutionManager tests passed.")


if __name__ == "__main__":

    main()
