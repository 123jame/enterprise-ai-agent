"""
单项目流水线验证脚本（无 Dashboard / 无 reload 依赖）。

用法:
    cd backend
    python scripts/run_single_project.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from applications.platform.enterprise_coordinator import EnterpriseCoordinator


def main() -> int:

    session_id = f"sess_p0_{uuid4().hex[:10]}"
    requirement = (
        "开发一个图书管理系统，包含图书借阅、归还、读者管理、查询统计"
    )
    project_name = "Library P0 Run13"

    print("START", json.dumps({
        "session_id": session_id,
        "project_name": project_name,
        "requirement": requirement,
    }, ensure_ascii=False))

    started = time.time()
    coordinator = EnterpriseCoordinator()
    result = coordinator.run(
        session_id=session_id,
        user_requirement=requirement,
        project_name=project_name,
        user_id="p0_test",
    )
    elapsed = time.time() - started

    workspace = ""
    if result.team_result is not None:
        workspace = result.team_result.project.workspace_path

    print("RESULT", json.dumps({
        "success": result.success,
        "elapsed_sec": round(elapsed, 1),
        "workspace": workspace,
        "failed_agent": result.team_result.metadata.get("failed_agent", "")
        if result.team_result
        else "",
        "content_head": (result.content or "")[:400],
    }, ensure_ascii=False))

    if workspace:
        root = Path(workspace)
        if not root.is_absolute():
            root = BACKEND_ROOT / workspace
        checks = {
            "PRD": (root / "docs" / "PRD.md").is_file(),
            "Architecture": (root / "docs" / "Architecture.md").is_file(),
            "backend": (root / "backend" / "main.py").is_file(),
            "frontend": (root / "frontend" / "index.html").is_file(),
            "tests": (root / "tests").is_dir(),
            "README": (root / "README.md").is_file(),
        }
        print("ARTIFACTS", json.dumps(checks, ensure_ascii=False))

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
