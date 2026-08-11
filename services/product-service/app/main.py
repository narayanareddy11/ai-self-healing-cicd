from fastapi import FastAPI
from pydantic import BaseModel


class Product(BaseModel):
    id: int
    name: str
    price: float


app = FastAPI(title="product-service", version="0.1.0")

PRODUCTS = [
    Product(id=1, name="Keyboard", price=89.0),
    Product(id=2, name="Mouse", price=39.0),
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/products", response_model=list[Product])
def list_products() -> list[Product]:
    return PRODUCTS
