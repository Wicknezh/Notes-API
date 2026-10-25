from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Notes API", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(notes.router)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}