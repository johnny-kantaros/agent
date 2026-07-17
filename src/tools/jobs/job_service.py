import json
import uuid
from datetime import UTC, datetime

from croniter import croniter

from src.db.database import db_cursor
from src.utils.timezone import get_local_tz, local_to_utc_iso, utc_to_local_iso


def _localize(job: dict) -> dict:
    for field in ("scheduled_at", "created_at", "last_run_at"):
        job[field] = utc_to_local_iso(job.get(field))
    return job


class AgentJobService:
    @staticmethod
    def create_job(
        instruction: str,
        scheduled_at: str,
        recurrence: str | None = None,
        notify_via: list[str] | None = None,
    ) -> dict:
        job_id = str(uuid.uuid4())
        notify = json.dumps(notify_via or ["telegram"])
        with db_cursor() as conn:
            conn.execute(
                """
                INSERT INTO agent_jobs (id, instruction, scheduled_at, recurrence, notify_via, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    instruction,
                    local_to_utc_iso(scheduled_at),
                    recurrence,
                    notify,
                    datetime.now(UTC).isoformat(),
                ),
            )
        return {"job_id": job_id, "scheduled_at": scheduled_at}

    @staticmethod
    def list_jobs(status: str | None = None) -> list[dict]:
        with db_cursor() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM agent_jobs WHERE status = ? ORDER BY scheduled_at ASC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM agent_jobs ORDER BY scheduled_at ASC").fetchall()
        return [_localize(dict(r)) for r in rows]

    @staticmethod
    def get_due_jobs() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        with db_cursor() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_jobs
                WHERE status = 'pending' AND scheduled_at <= ?
                ORDER BY scheduled_at ASC
                """,
                (now,),
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def set_running(job_id: str) -> None:
        with db_cursor() as conn:
            conn.execute(
                "UPDATE agent_jobs SET status = 'running' WHERE id = ?",
                (job_id,),
            )

    @staticmethod
    def set_done(job_id: str, result: str, recurrence: str | None) -> None:
        now = datetime.now(UTC).isoformat()
        with db_cursor() as conn:
            if recurrence:
                next_run = croniter(recurrence, datetime.now(get_local_tz())).get_next(datetime)
                conn.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'pending', result = ?, last_run_at = ?, scheduled_at = ?, error = NULL
                    WHERE id = ?
                    """,
                    (result, now, next_run.astimezone(UTC).isoformat(), job_id),
                )
            else:
                conn.execute(
                    "UPDATE agent_jobs SET status = 'done', result = ?, last_run_at = ? WHERE id = ?",
                    (result, now, job_id),
                )

    @staticmethod
    def set_failed(job_id: str, error: str, recurrence: str | None) -> None:
        now = datetime.now(UTC).isoformat()
        with db_cursor() as conn:
            if recurrence:
                next_run = croniter(recurrence, datetime.now(get_local_tz())).get_next(datetime)
                conn.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'pending', error = ?, last_run_at = ?, scheduled_at = ?
                    WHERE id = ?
                    """,
                    (error, now, next_run.astimezone(UTC).isoformat(), job_id),
                )
            else:
                conn.execute(
                    "UPDATE agent_jobs SET status = 'failed', error = ?, last_run_at = ? WHERE id = ?",
                    (error, now, job_id),
                )

    @staticmethod
    def cancel_job(job_id: str) -> None:
        with db_cursor() as conn:
            conn.execute(
                "UPDATE agent_jobs SET status = 'cancelled' WHERE id = ? AND status = 'pending'",
                (job_id,),
            )

    @staticmethod
    def resync_recurring_jobs() -> None:
        """Recompute pending recurring jobs' next run time against the current local timezone.

        Without this, a job already advanced under the old timezone stays pinned to that
        zone's wall-clock hour until it runs once — one silent wrong-time run after travel.
        """
        with db_cursor() as conn:
            rows = conn.execute(
                "SELECT id, recurrence FROM agent_jobs WHERE recurrence IS NOT NULL AND status = 'pending'"
            ).fetchall()
            for row in rows:
                next_run = croniter(row["recurrence"], datetime.now(get_local_tz())).get_next(
                    datetime
                )
                conn.execute(
                    "UPDATE agent_jobs SET scheduled_at = ? WHERE id = ?",
                    (next_run.astimezone(UTC).isoformat(), row["id"]),
                )

    @staticmethod
    def update_job(job_id: str, updates: dict) -> None:
        allowed = {"instruction", "scheduled_at", "recurrence", "notify_via"}
        set_clause, values = [], []
        for k, v in updates.items():
            if k in allowed:
                if k == "scheduled_at":
                    v = local_to_utc_iso(v)
                set_clause.append(f"{k} = ?")
                values.append(json.dumps(v) if k == "notify_via" else v)
        if not set_clause:
            return
        values.append(job_id)
        with db_cursor() as conn:
            conn.execute(
                f"UPDATE agent_jobs SET {', '.join(set_clause)} WHERE id = ? AND status = 'pending'",
                values,
            )
