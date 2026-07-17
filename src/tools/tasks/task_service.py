import json
from datetime import UTC, datetime

from croniter import croniter

from src.db.database import db_cursor
from src.utils.timezone import get_local_tz, local_to_utc_iso, utc_to_local_iso


def _localize(task: dict) -> dict:
    for field in ("due_date", "scheduled_at", "created_at"):
        task[field] = utc_to_local_iso(task.get(field))
    return task


class TaskService:
    @staticmethod
    def create_task(task_data: dict) -> dict:
        with db_cursor() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, status, priority, due_date, scheduled_at, recurrence, notify_via, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_data["title"],
                    task_data.get("description"),
                    task_data.get("status", "pending"),
                    task_data.get("priority"),
                    local_to_utc_iso(task_data.get("due_date")),
                    local_to_utc_iso(task_data.get("scheduled_at")),
                    task_data.get("recurrence"),
                    json.dumps(task_data["notify_via"]) if task_data.get("notify_via") else None,
                    datetime.now(UTC).isoformat(),
                ),
            )
        return {"task_id": cursor.lastrowid, "title": task_data["title"]}

    @staticmethod
    def list_tasks(include_completed: bool = False) -> list[dict]:
        with db_cursor() as conn:
            query = "SELECT * FROM tasks"
            if not include_completed:
                query += " WHERE status != 'completed'"
            query += " ORDER BY due_date IS NULL, due_date ASC"
            rows = conn.execute(query).fetchall()
        return [_localize(dict(r)) for r in rows]

    @staticmethod
    def complete_task(task_id: int) -> None:
        with db_cursor() as conn:
            conn.execute(
                "UPDATE tasks SET status = 'completed', scheduled_at = NULL WHERE id = ?",
                (task_id,),
            )

    @staticmethod
    def update_task(task_id: int, updates: dict) -> None:
        allowed = {
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "scheduled_at",
            "recurrence",
            "notify_via",
        }
        set_clause, values = [], []
        for k, v in updates.items():
            if k in allowed:
                if k in ("due_date", "scheduled_at"):
                    v = local_to_utc_iso(v)
                set_clause.append(f"{k} = ?")
                values.append(json.dumps(v) if k == "notify_via" and isinstance(v, list) else v)
        if not set_clause:
            return
        values.append(task_id)
        with db_cursor() as conn:
            conn.execute(
                f"UPDATE tasks SET {', '.join(set_clause)} WHERE id = ?",
                values,
            )

    @staticmethod
    def get_due_reminders() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        with db_cursor() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE scheduled_at IS NOT NULL
                  AND scheduled_at <= ?
                  AND status != 'completed'
                ORDER BY scheduled_at ASC
                """,
                (now,),
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def advance_reminder(task_id: int, recurrence: str | None) -> None:
        with db_cursor() as conn:
            if recurrence:
                next_run = croniter(recurrence, datetime.now(get_local_tz())).get_next(datetime)
                conn.execute(
                    "UPDATE tasks SET scheduled_at = ? WHERE id = ?",
                    (next_run.astimezone(UTC).isoformat(), task_id),
                )
            else:
                conn.execute(
                    "UPDATE tasks SET scheduled_at = NULL WHERE id = ?",
                    (task_id,),
                )

    @staticmethod
    def resync_recurring_reminders() -> None:
        """Recompute pending recurring reminders' next fire time against the current local timezone.

        Without this, a reminder already advanced under the old timezone stays pinned to that
        zone's wall-clock hour until it fires once — one silent wrong-time reminder after travel.
        """
        with db_cursor() as conn:
            rows = conn.execute(
                "SELECT id, recurrence FROM tasks WHERE recurrence IS NOT NULL AND status != 'completed'"
            ).fetchall()
            for row in rows:
                next_run = croniter(row["recurrence"], datetime.now(get_local_tz())).get_next(
                    datetime
                )
                conn.execute(
                    "UPDATE tasks SET scheduled_at = ? WHERE id = ?",
                    (next_run.astimezone(UTC).isoformat(), row["id"]),
                )

    @staticmethod
    def search_tasks(query: str) -> list[dict]:
        with db_cursor() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE status != 'completed'
                  AND title LIKE '%' || ? || '%'
                ORDER BY created_at DESC
                """,
                (query,),
            ).fetchall()
        return [_localize(dict(r)) for r in rows]
