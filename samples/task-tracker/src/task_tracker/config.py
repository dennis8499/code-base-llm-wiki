"""Validated JSON settings for the Task Tracker sample."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskTrackerSettings:
    """Limits and defaults used by TaskTrackerService."""

    max_open_tasks: int
    default_due_days: int

    def __post_init__(self) -> None:
        if self.max_open_tasks <= 0:
            raise ValueError("max_open_tasks must be greater than zero")
        if self.default_due_days < 0:
            raise ValueError("default_due_days must not be negative")

    @classmethod
    def from_json(cls, path: str | Path) -> TaskTrackerSettings:
        """Load settings from a UTF-8 JSON object."""

        payload: Any = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("settings root must be a JSON object")
        try:
            max_open_tasks = payload["max_open_tasks"]
            default_due_days = payload["default_due_days"]
        except KeyError as error:
            raise ValueError(f"missing setting: {error.args[0]}") from error
        if type(max_open_tasks) is not int or type(default_due_days) is not int:
            raise ValueError("settings values must be integers")
        return cls(
            max_open_tasks=max_open_tasks,
            default_due_days=default_due_days,
        )

