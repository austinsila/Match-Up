from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import connect_db, disconnect_db, setup_db
from routes.auth import router as auth_router
from security import require_jwt_secret


@asynccontextmanager
async def lifespan(app: FastAPI):
    require_jwt_secret()
    await connect_db()
    await setup_db()
    yield
    await disconnect_db()


app = FastAPI(title="Match Up API", lifespan=lifespan)
app.include_router(auth_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Match Up API"}
