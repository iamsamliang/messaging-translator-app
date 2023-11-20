import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_by_email():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}
