import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_reserva_stock_409():
    payload = {
        "producto_id": "00000000-0000-0000-0000-000000000000",
        "sede_id": "00000000-0000-0000-0000-000000000000",
        "cantidad": 999999
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/inventario/reservar", json=payload)
    
    assert response.status_code in [404, 409]
