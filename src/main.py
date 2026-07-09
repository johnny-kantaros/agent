import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api.server import router, session_store
from src.db.database import init_db
from src.planner.poller import start_job_poller
from src.planner.reminder_loop import start_reminder_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(start_job_poller(session_store))
    asyncio.create_task(start_reminder_loop())
    yield


app = FastAPI(title="Agent API", lifespan=lifespan)
app.include_router(router)


def main():
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    main()
