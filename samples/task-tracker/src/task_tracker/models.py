"""Domain entities for the Task Tracker sample."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    """Supported TaskItem lifecycle states."""

    OPEN = "open"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class TaskItem:
    """An immutable task persisted through a TaskRepository."""

    task_id: str
    title: str
    status: TaskStatus
    created_at: datetime
    due_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        for field_name, value in (
            ("created_at", self.created_at),
            ("due_at", self.due_at),
            ("completed_at", self.completed_at),
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.status is TaskStatus.OPEN and self.completed_at is not None:
            raise ValueError("open tasks cannot have completed_at")
        if self.status is TaskStatus.COMPLETED and self.completed_at is None:
            raise ValueError("completed tasks require completed_at")

