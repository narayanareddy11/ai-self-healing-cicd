from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient


def load_app():
    service_root = Path(__file__).resolve().parents[1]
    spec = spec_from_file_location("order_service_app", service_root / "app" / "main.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load order-service app")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


client = TestClient(load_app())


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_list_orders() -> None:
    response = client.get("/orders")

    assert response.status_code == 200
    assert response.json()[0]["quantity"] == 1
