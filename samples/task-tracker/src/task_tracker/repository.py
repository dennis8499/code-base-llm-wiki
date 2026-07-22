"""Persistence abstraction and in-memory adapter."""

from __future__ import annotations

from typing import Protocol

from .models import TaskItem


class TaskRepository(Protocol):
    """Storage contract consumed by TaskTrackerService."""

    def get(self, task_id: str) -> TaskItem | None:
        """Return one task or None when the identifier is unknown."""

    def list_all(self) -> tuple[TaskItem, ...]:
        """Return a stable snapshot of every task."""

    def save(self, task: TaskItem) -> None:
        """Create or replace a task by identifier."""


class InMemoryTaskRepository:
    """Dictionary-backed repository used by the sample and its tests."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskItem] = {}

    def get(self, task_id: str) -> TaskItem | None:
        return self._tasks.get(task_id)

    def list_all(self) -> tuple[TaskItem, ...]:
        return tuple(self._tasks.values())

    def save(self, task: TaskItem) -> None:
        self._tasks[task.task_id] = task

