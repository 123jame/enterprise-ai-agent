import json
from typing import Any

from app.embodied.types import Observation


def normalize_observation_input(
    observation: Observation | dict[str, Any] | str,
) -> dict[str, Any]:
    """
    将多种 Observation 输入统一为字典。

    支持 embodied.Observation、字典或 JSON 字符串。
    """

    if isinstance(observation, Observation):

        payload = observation.to_dict()

        if observation.raw:

            payload.update(
                {
                    key: value
                    for key, value in observation.raw.items()
                    if key not in payload
                }
            )

        return payload

    if isinstance(observation, dict):

        return dict(observation)

    text = str(observation).strip()

    if text.startswith("{"):

        try:

            parsed = json.loads(text)

        except json.JSONDecodeError as error:

            raise ValueError(
                "Observation JSON 解析失败",
            ) from error

        if isinstance(parsed, dict):

            return parsed

    return {
        "type": "generic",
        "content": text,
        "success": True,
    }
