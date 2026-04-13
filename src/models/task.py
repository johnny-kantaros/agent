from dataclasses import dataclass


@dataclass
class Task:
    task: str
    details: str
    due_date: str | None = None
    reminder_cadence: str | None = "none"
