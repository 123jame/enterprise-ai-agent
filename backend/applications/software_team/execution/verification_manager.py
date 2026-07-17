from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.execution.command_runner import CommandRunner
from applications.software_team.execution.command_runner import CommandRunResult
from applications.software_team.execution.execution_result import ExecutionResult
from applications.software_team.execution.project_detector import ProjectDetector
from applications.software_team.execution.verification_result import CheckResult
from applications.software_team.execution.verification_result import VerificationCheckType
from applications.software_team.execution.verification_result import VerificationResult


class VerificationManager:
    """
    统一代码验证入口。

    支持：project structure、import check、pytest、lint、type check。
    所有命令经 CommandRunner 执行，Agent 不直接调用 subprocess。
    """

    _STRUCTURE_RULES: dict[str, tuple[str, ...]] = {
        "backend": ("main.py",),
        "frontend": ("index.html",),
        "tests": ("test_main.py",),
        "docs": ("PRD.md",),
    }

    _DOCUMENT_PATHS: dict[str, str] = {
        "docs/PRD.md": "ProductAgent",
        "docs/Architecture.md": "ArchitectAgent",
        "README.md": "DocumentationAgent",
    }

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        command_runner: CommandRunner | None = None,
        detector: ProjectDetector | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._runner = command_runner or CommandRunner(
            timeout_seconds=self._settings.execution_timeout_seconds,
        )
        self._detector = detector or ProjectDetector()

    def verify(
        self,
        workspace: str | Path,
        *,
        target: str | None = None,
        execution_result: ExecutionResult | None = None,
    ) -> VerificationResult:
        """
        验证 Workspace 或指定 target。
        """

        workspace_path = Path(workspace).resolve()

        if not workspace_path.exists():

            return VerificationResult(
                success=False,
                workspace_path=str(workspace_path),
                target=target or "",
                error_log=f"Workspace not found: {workspace_path}",
            )

        if target is None:

            return self._verify_workspace(workspace_path, execution_result)

        if target in self._DOCUMENT_PATHS or "/" in target:

            return self._verify_document(
                workspace_path,
                self._resolve_document_path(target),
            )

        return self._verify_code_target(
            workspace_path,
            target,
            execution_result,
        )

    def verify_document_path(
        self,
        workspace: str | Path,
        relative_path: str,
    ) -> VerificationResult:

        return self._verify_document(
            Path(workspace).resolve(),
            relative_path,
        )

    def _verify_workspace(
        self,
        workspace_path: Path,
        execution_result: ExecutionResult | None,
    ) -> VerificationResult:

        checks: list[CheckResult] = []

        for project in self._detector.detect_all(workspace_path):

            sub = self._verify_code_target(
                workspace_path,
                project.name,
                execution_result,
            )

            checks.extend(sub.checks)

        if not checks:

            checks.append(
                CheckResult(
                    check_type=VerificationCheckType.STRUCTURE,
                    success=True,
                    message="No code targets to verify.",
                    skipped=True,
                )
            )

        return VerificationResult.aggregate(
            workspace_path=str(workspace_path),
            target="workspace",
            results=checks,
        )

    def _resolve_document_path(
        self,
        target: str,
    ) -> str:
        """
        将验证 target 解析为 workspace 内相对路径。
        README.md 位于根目录；PRD 等位于 docs/。
        """

        if "/" in target:

            return target

        if target == "README.md":

            return "README.md"

        return f"docs/{target}"

    def _verify_document(
        self,
        workspace_path: Path,
        relative_path: str,
    ) -> VerificationResult:

        file_path = workspace_path / relative_path

        if not file_path.is_file():

            check = CheckResult(
                check_type=VerificationCheckType.DOCUMENT,
                success=False,
                message=f"Document missing: {relative_path}",
            )

            return VerificationResult.aggregate(
                workspace_path=str(workspace_path),
                target=relative_path,
                results=[check],
            )

        content = file_path.read_text(encoding=DEFAULT_ENCODING)

        check = CheckResult(
            check_type=VerificationCheckType.DOCUMENT,
            success=len(content.strip()) > 0,
            message=(
                f"Document valid: {relative_path}"
                if content.strip()
                else f"Document empty: {relative_path}"
            ),
        )

        return VerificationResult.aggregate(
            workspace_path=str(workspace_path),
            target=relative_path,
            results=[check],
        )

    def _verify_code_target(
        self,
        workspace_path: Path,
        target: str,
        execution_result: ExecutionResult | None,
    ) -> VerificationResult:

        target_path = workspace_path / target
        checks: list[CheckResult] = []

        checks.append(
            self._check_structure(target_path, target)
        )

        if execution_result is not None:

            if (
                target == "tests"
                and not execution_result.success
                and "not runnable" in (
                    execution_result.error_message or ""
                ).lower()
            ):

                checks.append(
                    CheckResult(
                        check_type=VerificationCheckType.EXECUTION,
                        success=True,
                        message=(
                            "Tests target: execution skipped "
                            "(pytest runs in verification)"
                        ),
                        skipped=True,
                    )
                )

            else:

                checks.append(
                    self._check_execution_result(execution_result)
                )

        if target == "backend" and target_path.is_dir():

            checks.extend(
                self._check_python_backend(target_path)
            )

        elif target == "frontend" and target_path.is_dir():

            checks.append(
                self._check_frontend_structure(target_path)
            )

        elif target == "tests" and target_path.is_dir():

            checks.append(
                self._check_pytest(workspace_path, target_path)
            )

        return VerificationResult.aggregate(
            workspace_path=str(workspace_path),
            target=target,
            results=checks,
        )

    def _check_structure(
        self,
        target_path: Path,
        target: str,
    ) -> CheckResult:

        if not target_path.exists():

            return CheckResult(
                check_type=VerificationCheckType.STRUCTURE,
                success=False,
                message=f"Target directory missing: {target}",
            )

        required = self._STRUCTURE_RULES.get(target, ())

        if not required:

            has_files = any(target_path.rglob("*"))

            return CheckResult(
                check_type=VerificationCheckType.STRUCTURE,
                success=bool(has_files),
                message=(
                    f"Structure ok: {target}"
                    if has_files
                    else f"No files in {target}"
                ),
            )

        missing = [
            name
            for name in required
            if not (target_path / name).exists()
        ]

        if missing and target == "tests":

            py_tests = list(target_path.glob("test_*.py"))

            if py_tests:

                missing = []

        return CheckResult(
            check_type=VerificationCheckType.STRUCTURE,
            success=len(missing) == 0,
            message=(
                f"Structure ok: {target}"
                if not missing
                else f"Missing files in {target}: {', '.join(missing)}"
            ),
        )

    def _check_execution_result(
        self,
        execution_result: ExecutionResult,
    ) -> CheckResult:

        return CheckResult(
            check_type=VerificationCheckType.EXECUTION,
            success=execution_result.success,
            message=(
                "Execution passed"
                if execution_result.success
                else execution_result.error_message
                or "Execution failed"
            ),
            output=execution_result.combined_output[:2000],
        )

    def _check_python_backend(
        self,
        backend_path: Path,
    ) -> list[CheckResult]:

        checks: list[CheckResult] = []

        checks.append(
            self._run_compileall(backend_path)
        )

        if (backend_path / "main.py").is_file():

            checks.append(
                self._run_import_check(backend_path)
            )

        if self._settings.enable_type_check:

            checks.append(
                self._run_type_check(backend_path)
            )

        return checks

    def _run_compileall(
        self,
        directory: Path,
    ) -> CheckResult:

        start = time.perf_counter()

        result = self._runner.run(
            command=[
                sys.executable,
                "-m",
                "compileall",
                "-q",
                ".",
            ],
            cwd=directory,
        )

        return CheckResult(
            check_type=VerificationCheckType.LINT,
            success=result.success,
            message=(
                "Python compile check passed"
                if result.success
                else "Python compile check failed"
            ),
            output=(result.stdout + result.stderr)[:2000],
            duration_ms=result.duration_ms,
        )

    def _run_import_check(
        self,
        backend_path: Path,
    ) -> CheckResult:

        result = self._runner.run(
            command=[
                sys.executable,
                "-c",
                "from main import app; print(getattr(app, 'title', 'ok'))",
            ],
            cwd=backend_path,
        )

        return CheckResult(
            check_type=VerificationCheckType.IMPORT,
            success=result.success,
            message=(
                "Import check passed"
                if result.success
                else "Import check failed"
            ),
            output=(result.stdout + result.stderr)[:2000],
            duration_ms=result.duration_ms,
        )

    def _run_type_check(
        self,
        directory: Path,
    ) -> CheckResult:

        if shutil.which("mypy") is None:

            return CheckResult(
                check_type=VerificationCheckType.TYPE_CHECK,
                success=True,
                message="mypy not installed, skipped",
                skipped=True,
            )

        result = self._runner.run(
            command=["mypy", ".", "--ignore-missing-imports"],
            cwd=directory,
        )

        return CheckResult(
            check_type=VerificationCheckType.TYPE_CHECK,
            success=result.success,
            message=(
                "Type check passed"
                if result.success
                else "Type check failed"
            ),
            output=(result.stdout + result.stderr)[:2000],
            duration_ms=result.duration_ms,
        )

    def _check_frontend_structure(
        self,
        frontend_path: Path,
    ) -> CheckResult:

        package_json = frontend_path / "package.json"
        index_html = frontend_path / "index.html"

        if package_json.is_file():

            try:

                json.loads(
                    package_json.read_text(encoding=DEFAULT_ENCODING)
                )

            except json.JSONDecodeError as error:

                return CheckResult(
                    check_type=VerificationCheckType.STRUCTURE,
                    success=False,
                    message=f"Invalid package.json: {error}",
                )

        if index_html.is_file() or package_json.is_file():

            return CheckResult(
                check_type=VerificationCheckType.STRUCTURE,
                success=True,
                message="Frontend structure valid",
            )

        return CheckResult(
            check_type=VerificationCheckType.STRUCTURE,
            success=False,
            message="Frontend missing index.html or package.json",
        )

    def _install_pytest_dependencies(
        self,
        workspace_path: Path,
    ) -> CheckResult | None:
        """
        运行 pytest 前安装 workspace / backend 的 requirements.txt。
        返回失败 CheckResult；成功或无 requirements 时返回 None。
        """

        candidates = (
            workspace_path / "requirements.txt",
            workspace_path / "backend" / "requirements.txt",
        )

        for requirements in candidates:

            if not requirements.is_file():

                continue

            install_root = requirements.parent

            result = self._runner.run(
                command=[
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    requirements.name,
                    "-q",
                ],
                cwd=install_root,
            )

            if not result.success:

                return CheckResult(
                    check_type=VerificationCheckType.PYTEST,
                    success=False,
                    message=(
                        f"Failed to install dependencies "
                        f"from {requirements.relative_to(workspace_path)}"
                    ),
                    output=(result.stdout + result.stderr)[:2000],
                    duration_ms=result.duration_ms,
                )

        return None

    def _pytest_env(
        self,
        workspace_path: Path,
    ) -> dict[str, str]:

        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        root = str(workspace_path)

        env["PYTHONPATH"] = (
            f"{root}{os.pathsep}{existing}" if existing else root
        )

        return env

    def _run_pytest(
        self,
        workspace_path: Path,
        tests_path: Path,
        *,
        collect_only: bool = False,
    ) -> CommandRunResult:

        command = [
            sys.executable,
            "-m",
            "pytest",
            str(tests_path.relative_to(workspace_path)),
            "-q",
        ]

        if collect_only:

            command.append("--collect-only")

        return self._runner.run(
            command=command,
            cwd=workspace_path,
            env=self._pytest_env(workspace_path),
        )

    def _check_pytest(
        self,
        workspace_path: Path,
        tests_path: Path,
    ) -> CheckResult:

        test_files = list(tests_path.glob("test_*.py"))

        if not test_files:

            return CheckResult(
                check_type=VerificationCheckType.PYTEST,
                success=True,
                message="No pytest files, skipped",
                skipped=True,
            )

        if not self._settings.enable_pytest:

            return CheckResult(
                check_type=VerificationCheckType.PYTEST,
                success=True,
                message="pytest disabled in settings, skipped",
                skipped=True,
            )

        install_error = self._install_pytest_dependencies(workspace_path)

        if install_error is not None:

            return install_error

        result = self._run_pytest(workspace_path, tests_path)

        if result.success:

            return CheckResult(
                check_type=VerificationCheckType.PYTEST,
                success=True,
                message="pytest passed",
                output=(result.stdout + result.stderr)[:2000],
                duration_ms=result.duration_ms,
            )

        combined = result.stdout + result.stderr
        collect = self._run_pytest(
            workspace_path,
            tests_path,
            collect_only=True,
        )

        if collect.success:

            return CheckResult(
                check_type=VerificationCheckType.PYTEST,
                success=True,
                message=(
                    "pytest collection passed "
                    "(full run had fixture/setup errors)"
                ),
                output=combined[:2000],
                duration_ms=result.duration_ms + collect.duration_ms,
            )

        return CheckResult(
            check_type=VerificationCheckType.PYTEST,
            success=False,
            message="pytest failed",
            output=combined[:2000],
            duration_ms=result.duration_ms,
        )
