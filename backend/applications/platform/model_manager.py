from __future__ import annotations

from applications.platform.platform_result import ModelConfig
from applications.platform.platform_result import ModelProvider
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class ModelManager:
    """
    统一模型管理：OpenAI / Claude / Gemini / Local，支持路由与策略。
    """

    STORE_KEY = "models"

    _DEFAULT_MODELS: list[tuple[str, ModelProvider, str, int]] = [
        ("OpenAI GPT-4o Mini", ModelProvider.OPENAI, "gpt-4o-mini", 10),
        ("OpenAI GPT-4o", ModelProvider.OPENAI, "gpt-4o", 20),
        ("Claude Sonnet", ModelProvider.CLAUDE, "claude-3-5-sonnet-20241022", 30),
        ("Gemini Pro", ModelProvider.GEMINI, "gemini-1.5-pro", 40),
        ("Local LLM", ModelProvider.LOCAL, "local/default", 100),
    ]

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)

    def initialize_defaults(self) -> list[ModelConfig]:

        if self._store.load(self.STORE_KEY):

            return self.list_models()

        models: list[ModelConfig] = []

        for name, provider, model_id, priority in self._DEFAULT_MODELS:

            models.append(
                self.register(name=name, provider=provider, model_id=model_id, priority=priority)
            )

        return models

    def register(
        self,
        *,
        name: str,
        provider: ModelProvider,
        model_id: str,
        priority: int = 100,
    ) -> ModelConfig:

        model = ModelConfig.create(
            name=name,
            provider=provider,
            model_id=model_id,
            priority=priority,
        )

        self._store.append(self.STORE_KEY, self._to_dict(model))

        return model

    def get(self, model_id: str) -> ModelConfig | None:

        data = self._store.find(self.STORE_KEY, model_id)

        if data is None:

            return None

        return self._from_dict(data)

    def list_models(self, *, enabled_only: bool = True) -> list[ModelConfig]:

        models = [self._from_dict(item) for item in self._store.load(self.STORE_KEY)]

        if enabled_only:

            models = [m for m in models if m.enabled]

        return sorted(models, key=lambda m: m.priority)

    def route(
        self,
        *,
        provider: ModelProvider | None = None,
        task_type: str = "",
    ) -> ModelConfig | None:

        models = self.list_models()

        if provider is not None:

            matched = [m for m in models if m.provider == provider]

            if matched:

                return matched[0]

        if task_type == "local":

            local = [m for m in models if m.provider == ModelProvider.LOCAL]

            if local:

                return local[0]

        default_provider = ModelProvider(self._settings.default_model_provider)

        for model in models:

            if model.provider == default_provider:

                return model

        return models[0] if models else None

    @staticmethod
    def summarize(models: list[ModelConfig]) -> str:

        if not models:

            return "No models configured"

        lines = [f"Models: {len(models)}"]

        for model in models[:5]:

            lines.append(
                f"- [{model.provider.value}] {model.name} ({model.model_id})"
            )

        return "\n".join(lines)

    @staticmethod
    def _to_dict(model: ModelConfig) -> dict:

        return {
            "id": model.id,
            "name": model.name,
            "provider": model.provider.value,
            "model_id": model.model_id,
            "enabled": model.enabled,
            "priority": model.priority,
            "metadata": model.metadata,
        }

    @staticmethod
    def _from_dict(data: dict) -> ModelConfig:

        return ModelConfig(
            id=data["id"],
            name=data["name"],
            provider=ModelProvider(data["provider"]),
            model_id=data["model_id"],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 100),
            metadata=data.get("metadata", {}),
        )
