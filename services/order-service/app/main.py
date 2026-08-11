from fastapi import FastAPI
from pydantic import BaseModel


class Order(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int


app = FastAPI(title="order-service", version="0.1.0")

ORDERS = [
    Order(id=1, user_id=1, product_id=1, quantity=1),
    Order(id=2, user_id=2, product_id=2, quantity=2),
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/orders", response_model=list[Order])
def list_orders() -> list[Order]:
    return ORDERS
