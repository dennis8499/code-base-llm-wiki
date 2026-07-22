"""Application service and domain-specific failure modes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .config import TaskTrackerSettings
from .models import TaskItem, TaskStatus
from .repository import TaskRepository


class TaskNotFoundError(LookupError):
    """Raised when a task identifier does not exist."""


class InvalidTaskTransitionError(ValueError):
    """Raised when a requested lifecycle transition is not allowed."""


class OpenTaskLimitError(RuntimeError):
    """Raised when creating a task would exceed the configured limit."""


class TaskTrackerService:
    """Coordinates task lifecycle behavior over a TaskRepository."""

    def __init__(
        self,
        repository: TaskRepository,
        settings: TaskTrackerSettings,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._id_factory = id_factory or (lambda: str(uuid4()))

    def create_task(self, title: str, *, due_in_days: int | None = None) -> TaskItem:
        """Create an open task after validating title, limit, and due date."""

        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("title must not be empty")

        open_count = sum(
            task.status is TaskStatus.OPEN for task in self._repository.list_all()
        )
        if open_count >= self._settings.max_open_tasks:
            raise OpenTaskLimitError("maximum number of open tasks reached")

        days = self._settings.default_due_days if due_in_days is None else due_in_days
        if days < 0:
            raise ValueError("due_in_days must not be negative")

        now = self._now()
        task = TaskItem(
            task_id=self._id_factory(),
            title=normalized_title,
            status=TaskStatus.OPEN,
            created_at=now,
            due_at=now + timedelta(days=days),
        )
        self._repository.save(task)
        return task

    def complete_task(self, task_id: str) -> TaskItem:
        """Complete one open task and persist the immutable replacement."""

        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.status is TaskStatus.COMPLETED:
            raise InvalidTaskTransitionError("completed tasks cannot be completed again")

        completed = replace(
            task,
            status=TaskStatus.COMPLETED,
            completed_at=self._now(),
        )
        self._repository.save(completed)
        return completed

    def list_tasks(self, *, include_completed: bool = True) -> tuple[TaskItem, ...]:
        """Return all tasks or only tasks that remain open."""

        tasks = self._repository.list_all()
        if include_completed:
            return tasks
        return tuple(task for task in tasks if task.status is TaskStatus.OPEN)

    def list_overdue_tasks(self) -> tuple[TaskItem, ...]:
        """Return open tasks whose due time is strictly earlier than now."""

        now = self._now()
        return tuple(
            task
            for task in self._repository.list_all()
            if task.status is TaskStatus.OPEN
            and task.due_at is not None
            and task.due_at < now
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value

