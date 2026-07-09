import asyncio
import json
import logging

from src.integrations.notifier import notify
from src.planner import agent
from src.planner.context import build_job_system_prompt
from src.planner.session import SessionStore
from src.tools.jobs.job_service import AgentJobService

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 60  # seconds


async def _run_job(job: dict, store: SessionStore) -> None:
    job_id = job["id"]
    recurrence = job.get("recurrence")
    notify_via = json.loads(job.get("notify_via", '["telegram"]'))

    AgentJobService.set_running(job_id)

    session_id, session = store.create()
    session.messages.append(build_job_system_prompt())
    result = ""

    try:
        async for event in agent.run_stream(job["instruction"], session):
            if event.type == "final":
                result = event.message
                break

        AgentJobService.set_done(job_id, result, recurrence)
        logger.info(f"Job {job_id} completed (session={session_id})")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        AgentJobService.set_failed(job_id, str(e), recurrence)
        result = f"Job failed: {e}"

    await notify(result, notify_via)


async def start_job_poller(store: SessionStore) -> None:
    logger.info("Job poller started")
    while True:
        await asyncio.sleep(_POLL_INTERVAL)
        try:
            due_jobs = AgentJobService.get_due_jobs()
            for job in due_jobs:
                asyncio.create_task(_run_job(job, store))
        except Exception as e:
            logger.error(f"Poller error: {e}")
