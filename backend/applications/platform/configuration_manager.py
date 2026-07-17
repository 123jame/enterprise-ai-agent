from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from applications.platform.settings import PlatformSettings


class ConfigurationManager:
    """
    统一配置中心：LLM / Memory / Embedding / Workflow / Prompt / Git / Deployment。
    """

    CONFIG_FILE = "platform_config.json"

    _DEFAULTS: dict[str, dict[str, Any]] = {
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "memory": {
            "enabled": True,
            "scope": "project",
        },
        "embedding": {
            "provider": "openai",
            "model": "text-embedding-3-small",
        },
        "workflow": {
            "max_iterations": 10,
            "enable_verification": True,
        },
        "prompt": {
            "enable_rag": False,
            "enable_mcp": False,
        },
        "git": {
            "enabled": True,
            "default_branch": "main",
            "develop_branch": "develop",
        },
        "deployment": {
            "enabled": True,
            "mode": "local",
        },
    }

    def __init__(
        self,
        settings: PlatformSettings | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._path = self._settings.platform_data_root / self.CONFIG_FILE
        self._settings.platform_data_root.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, dict[str, Any]]:

        if not self._path.is_file():

            config = {k: dict(v) for k, v in self._DEFAULTS.items()}
            self.save(config)

            return config

        return json.loads(self._path.read_text(encoding="utf-8"))

    def save(self, config: dict[str, dict[str, Any]]) -> None:

        self._path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_section(self, section: str) -> dict[str, Any]:

        config = self.load()

        return config.get(section, self._DEFAULTS.get(section, {}))

    def update_section(
        self,
        section: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:

        config = self.load()

        if section not in config:

            config[section] = dict(self._DEFAULTS.get(section, {}))

        config[section].update(values)
        self.save(config)

        return config[section]

    def apply_to_software_team_settings(self) -> dict[str, Any]:
        """
        导出 Software Team 可用配置映射（不修改 Framework）。
        """

        config = self.load()

        return {
            "enable_git": config.get("git", {}).get("enabled", True),
            "git_default_branch": config.get("git", {}).get("default_branch", "main"),
            "git_develop_branch": config.get("git", {}).get("develop_branch", "develop"),
            "enable_deployment": config.get("deployment", {}).get("enabled", True),
            "deployment_mode": config.get("deployment", {}).get("mode", "local"),
            "max_loop_iterations": config.get("workflow", {}).get("max_iterations", 10),
            "enable_verification": config.get("workflow", {}).get(
                "enable_verification",
                True,
            ),
            "enable_rag": config.get("prompt", {}).get("enable_rag", False),
            "enable_mcp_tools": config.get("prompt", {}).get("enable_mcp", False),
        }

    def summarize(self) -> str:

        config = self.load()
        lines = [f"Configuration sections: {len(config)}"]

        for section, values in config.items():

            lines.append(f"- {section}: {len(values)} key(s)")

        return "\n".join(lines)
