from src.db.database import db_cursor


class TaskService:
    @staticmethod
    def create_task(task_data: dict):
        with db_cursor() as conn:
            conn.execute(
                """
                INSERT INTO tasks (task, details, due_date, reminder_cadence)
                VALUES (?, ?, ?, ?)
                """,
                (
                    task_data["task"],
                    task_data["details"],
                    task_data.get("due_date"),
                    task_data.get("reminder_cadence", "none"),
                ),
            )

    @staticmethod
    def list_tasks(include_completed: bool = False):
        with db_cursor() as conn:
            query = """
                SELECT id, task, details, due_date, reminder_cadence, completed
                FROM tasks
            """

            if not include_completed:
                query += " WHERE completed = 0"

            query += " ORDER BY due_date IS NULL, due_date ASC"

            rows = conn.execute(query).fetchall()

        return [dict(r) for r in rows]

    @staticmethod
    def complete_task(task_id: int):
        with db_cursor() as conn:
            conn.execute(
                "UPDATE tasks SET completed = 1 WHERE id = ?",
                (task_id,),
            )

    @staticmethod
    def search_tasks(query: str):
        """Not yet supported."""
        with db_cursor() as conn:
            rows = conn.execute(
                """
                SELECT id, task, details, due_date, reminder_cadence, completed
                FROM tasks
                WHERE completed = 0
                AND task LIKE '%' || ? || '%'
                ORDER BY created_at DESC
                """,
                (query,),
            ).fetchall()

        return [dict(r) for r in rows]

    @staticmethod
    def update_task(task_id: int, updates: dict):
        allowed = {"task", "details", "due_date", "reminder_cadence", "completed"}

        set_clause = []
        values = []

        for k, v in updates.items():
            if k in allowed:
                set_clause.append(f"{k} = ?")
                values.append(v)

        if not set_clause:
            return {"success": False, "error": "No valid fields"}

        values.append(task_id)

        with db_cursor() as conn:
            conn.execute(
                f"""
                UPDATE tasks
                SET {", ".join(set_clause)}
                WHERE id = ?
                """,
                values,
            )
