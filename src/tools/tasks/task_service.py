import json
from datetime import UTC, datetime

from croniter import croniter

from src.db.database import db_cursor


class TaskService:
    @staticmethod
    def create_task(task_data: dict) -> dict:
        with db_cursor() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, status, priority, due_date, scheduled_at, recurrence, notify_via)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_data["title"],
                    task_data.get("description"),
                    task_data.get("status", "pending"),
                    task_data.get("priority"),
                    task_data.get("due_date"),
                    task_data.get("scheduled_at"),
                    task_data.get("recurrence"),
                    json.dumps(task_data["notify_via"]) if task_data.get("notify_via") else None,
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
        return [dict(r) for r in rows]

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
                next_run = croniter(recurrence, datetime.now(UTC)).get_next(datetime).isoformat()
                conn.execute(
                    "UPDATE tasks SET scheduled_at = ? WHERE id = ?",
                    (next_run, task_id),
                )
            else:
                conn.execute(
                    "UPDATE tasks SET scheduled_at = NULL WHERE id = ?",
                    (task_id,),
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
        return [dict(r) for r in rows]
