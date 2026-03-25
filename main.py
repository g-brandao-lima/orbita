import sys

sys.stdout.reconfigure(encoding="utf-8")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.scheduler import init_scheduler, shutdown_scheduler

    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Flight Monitor", lifespan=lifespan)

from app.routes.route_groups import router as route_groups_router
from app.routes.alerts import router as alerts_router
from app.routes.dashboard import router as dashboard_router

app.include_router(route_groups_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(dashboard_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
