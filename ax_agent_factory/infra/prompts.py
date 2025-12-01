"""Prompt loader utility for AX Agent Factory."""

from __future__ import annotations

import importlib.resources as pkg_resources
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load a prompt template from ax_agent_factory.prompts by file stem.

    Example: name="ivc_task_extractor" -> prompts/ivc_task_extractor.txt
    """

    package = "ax_agent_factory.prompts"
    filename = f"{name}.txt"
    try:
        with pkg_resources.files(package).joinpath(filename).open("r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(f"Prompt file not found: {package}/{filename}") from exc
