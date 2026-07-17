from __future__ import annotations

from pathlib import Path

MANAGEMENT_FILE_ALIASES: dict[str, str] = {
    "PROJECT_PLAN.md": "management/PROJECT_PLAN.md",
    "TASK_LIST.md": "management/TASK_LIST.md",
    "PROGRESS_REPORT.md": "management/PROGRESS_REPORT.md",
    "MILESTONE_REPORT.md": "management/MILESTONE_REPORT.md",
    "RISK_REPORT.md": "management/RISK_REPORT.md",
}

MANAGEMENT_DOC_HINTS: tuple[str, ...] = tuple(
    sorted(set(MANAGEMENT_FILE_ALIASES.values()))
)


def resolve_workspace_file(
    workspace: Path,
    relative_path: str,
) -> Path | None:
    """
    解析 Workspace 内可读文件路径。

    支持 management/ 下项目管理文档的短名 alias（如 PROJECT_PLAN.md）。
    """

    normalized = relative_path.replace("\\", "/").strip().lstrip("./")

    if not normalized:

        return None

    candidates: list[str] = [normalized]
    basename = Path(normalized).name

    alias = MANAGEMENT_FILE_ALIASES.get(basename)

    if alias and alias not in candidates:

        candidates.append(alias)

    if "/" not in normalized and not normalized.startswith("management/"):

        management_candidate = f"management/{basename}"

        if management_candidate not in candidates:

            candidates.append(management_candidate)

    workspace_resolved = workspace.resolve()

    for candidate in candidates:

        target = (workspace / candidate).resolve()

        if (
            target != workspace_resolved
            and workspace_resolved not in target.parents
        ):

            continue

        if target.is_file():

            return target

    return None


def build_not_found_message(relative_path: str) -> str:
    """
    构建更明确的文件未找到提示。
    """

    basename = Path(relative_path.replace("\\", "/")).name
    alias = MANAGEMENT_FILE_ALIASES.get(basename)

    if alias:

        return (
            f"File not found: {relative_path}. "
            f"Try read_file with path '{alias}'."
        )

    if "/" not in relative_path.replace("\\", "/"):

        return (
            f"File not found: {relative_path}. "
            f"If this is a management report, try 'management/{basename}'."
        )

    return f"File not found: {relative_path}"
