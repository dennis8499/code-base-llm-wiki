from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest


SAMPLE_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(SAMPLE_ROOT / "src"))

from task_tracker import (  # noqa: E402
    InMemoryTaskRepository,
    InvalidTaskTransitionError,
    OpenTaskLimitError,
    TaskNotFoundError,
    TaskStatus,
    TaskTrackerService,
    TaskTrackerSettings,
)


class TaskTrackerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 22, 9, 0, tzinfo=timezone.utc)
        self.repository = InMemoryTaskRepository()
        self.settings = TaskTrackerSettings(max_open_tasks=2, default_due_days=7)
        identifiers = iter(("task-1", "task-2", "task-3"))
        self.service = TaskTrackerService(
            self.repository,
            self.settings,
            clock=lambda: self.now,
            id_factory=lambda: next(identifiers),
        )

    def test_create_and_complete_task(self) -> None:
        task = self.service.create_task("  Document workflow  ")
        completed = self.service.complete_task(task.task_id)

        self.assertEqual(task.title, "Document workflow")
        self.assertEqual(task.due_at, self.now + timedelta(days=7))
        self.assertEqual(completed.status, TaskStatus.COMPLETED)
        self.assertEqual(completed.completed_at, self.now)

    def test_unknown_and_duplicate_completion_are_rejected(self) -> None:
        with self.assertRaises(TaskNotFoundError):
            self.service.complete_task("missing")

        task = self.service.create_task("Review wiki")
        self.service.complete_task(task.task_id)
        with self.assertRaises(InvalidTaskTransitionError):
            self.service.complete_task(task.task_id)

    def test_open_task_limit_is_enforced(self) -> None:
        self.service.create_task("One")
        self.service.create_task("Two")

        with self.assertRaises(OpenTaskLimitError):
            self.service.create_task("Three")

    def test_only_open_tasks_past_due_are_overdue(self) -> None:
        overdue = self.service.create_task("Overdue", due_in_days=0)
        completed = self.service.create_task("Completed", due_in_days=0)
        self.service.complete_task(completed.task_id)
        self.now += timedelta(seconds=1)

        self.assertEqual(self.service.list_overdue_tasks(), (overdue,))

    def test_settings_load_from_json(self) -> None:
        settings = TaskTrackerSettings.from_json(
            SAMPLE_ROOT / "config" / "task-tracker.json"
        )

        self.assertEqual(settings.max_open_tasks, 3)
        self.assertEqual(settings.default_due_days, 7)


if __name__ == "__main__":
    unittest.main()

