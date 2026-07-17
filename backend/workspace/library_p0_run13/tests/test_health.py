"""
Smoke tests — verify the backend boots and responds to basic endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """GET /api/health should return 200 with project name."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["project"] == "Library P0 Run13"


@pytest.mark.asyncio
async def test_items_endpoint(client: AsyncClient):
    """GET /api/items should return 200 with an empty list."""
    resp = await client.get("/api/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"items": []}


@pytest.mark.asyncio
async def test_root_not_found(client: AsyncClient):
    """A non-existent route should return 404."""
    resp = await client.get("/")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_books_list_empty(client: AsyncClient):
    """GET /api/books/ should return empty results."""
    resp = await client.get("/api/books/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["page_size"] == 20


@pytest.mark.asyncio
async def test_readers_list_empty(client: AsyncClient):
    """GET /api/readers/ should return empty results."""
    resp = await client.get("/api/readers/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
