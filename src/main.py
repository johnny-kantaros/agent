import uvicorn
from fastapi import FastAPI

from src.api.routes import router
from src.db.database import init_db

app = FastAPI(title="Agent API")
app.include_router(router)


def main():
    """Start the app"""
    init_db()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="debug")


if __name__ == "__main__":
    main()
