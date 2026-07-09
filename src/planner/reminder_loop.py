import asyncio
import json
import logging

from src.integrations.notifier import notify
from src.tools.tasks.task_service import TaskService

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 60  # seconds


async def _fire_reminder(task: dict) -> None:
    task_id = task["id"]
    notify_via = json.loads(task.get("notify_via") or '["telegram"]')
    await notify(f"Reminder: {task['title']}", notify_via)
    TaskService.advance_reminder(task_id, task.get("recurrence"))


async def start_reminder_loop() -> None:
    logger.info("Reminder loop started")
    while True:
        await asyncio.sleep(_POLL_INTERVAL)
        try:
            due = TaskService.get_due_reminders()
            for task in due:
                asyncio.create_task(_fire_reminder(task))
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")
