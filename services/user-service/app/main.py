from fastapi import FastAPI
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    email: str


app = FastAPI(title="user-service", version="0.1.0")

USERS = [
    User(id=1, name="Ada Lovelace", email="ada@example.com"),
    User(id=2, name="Grace Hopper", email="grace@example.com"),
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/users", response_model=list[User])
def list_users() -> list[User]:
    return USERS
