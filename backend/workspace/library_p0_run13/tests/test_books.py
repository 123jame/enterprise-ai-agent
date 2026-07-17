"""
Tests for /api/books endpoints — CRUD operations and search.
"""

import pytest
from httpx import AsyncClient


# ── Helper payloads ──

SAMPLE_BOOK = {
    "title": "Python 编程：从入门到实践",
    "author": "Eric Matthes",
    "isbn": "978-7-115-54608-1",
    "publisher": "人民邮电出版社",
    "publish_year": 2023,
    "category": "计算机科学",
    "description": "零基础学 Python 经典入门教材",
    "total_stock": 3,
}

SAMPLE_BOOK_2 = {
    "title": "流畅的 Python",
    "author": "Luciano Ramalho",
    "isbn": "978-7-115-54609-8",
    "publisher": "人民邮电出版社",
    "publish_year": 2022,
    "category": "计算机科学",
    "description": "进阶 Python 编程技巧",
    "total_stock": 2,
}


# ═══════════════════════════════════════════════════════
#  Create
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_book(client: AsyncClient):
    """POST /api/books/ should create a book and return 201."""
    resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == SAMPLE_BOOK["title"]
    assert body["author"] == SAMPLE_BOOK["author"]
    assert body["isbn"] == SAMPLE_BOOK["isbn"]
    assert body["total_stock"] == 3
    assert body["available_stock"] == 3
    assert body["is_active"] is True
    assert "id" in body


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(client: AsyncClient):
    """Creating a book with an existing ISBN should return 409."""
    await client.post("/api/books/", json=SAMPLE_BOOK)
    resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert "ISBN" in detail


@pytest.mark.asyncio
async def test_create_book_missing_required_fields(client: AsyncClient):
    """Missing required fields should return 422."""
    resp = await client.post("/api/books/", json={"title": "No Author"})
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════
#  Read
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_book_by_id(client: AsyncClient):
    """GET /api/books/{id} should return the book."""
    create_resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    book_id = create_resp.json()["id"]

    resp = await client.get(f"/api/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == book_id
    assert resp.json()["title"] == SAMPLE_BOOK["title"]


@pytest.mark.asyncio
async def test_get_book_not_found(client: AsyncClient):
    """GET /api/books/{id} for non-existent id should return 404."""
    resp = await client.get("/api/books/99999")
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════
#  Update
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_update_book(client: AsyncClient):
    """PUT /api/books/{id} should update fields."""
    create_resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    book_id = create_resp.json()["id"]

    update_data = {"title": "Python 编程（第3版）", "total_stock": 5}
    resp = await client.put(f"/api/books/{book_id}", json=update_data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Python 编程（第3版）"
    assert body["total_stock"] == 5
    assert body["available_stock"] == 5  # increased by 2


@pytest.mark.asyncio
async def test_update_book_not_found(client: AsyncClient):
    """PUT on non-existent book should return 404."""
    resp = await client.put("/api/books/99999", json={"title": "Ghost"})
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════
#  Deactivate / Activate
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_deactivate_book(client: AsyncClient):
    """PATCH /api/books/{id}/deactivate should mark book as inactive."""
    create_resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    book_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/books/{book_id}/deactivate")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_deactivate_book_already_inactive(client: AsyncClient):
    """Deactivating an already inactive book should return 400."""
    create_resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    book_id = create_resp.json()["id"]
    await client.patch(f"/api/books/{book_id}/deactivate")

    resp = await client.patch(f"/api/books/{book_id}/deactivate")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_activate_book(client: AsyncClient):
    """PATCH /api/books/{id}/activate should mark book as active."""
    create_resp = await client.post("/api/books/", json=SAMPLE_BOOK)
    book_id = create_resp.json()["id"]
    await client.patch(f"/api/books/{book_id}/deactivate")

    resp = await client.patch(f"/api/books/{book_id}/activate")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


# ═══════════════════════════════════════════════════════
#  Search
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_search_books_by_keyword(client: AsyncClient):
    """GET /api/books/?keyword=... should filter by keyword."""
    await client.post("/api/books/", json=SAMPLE_BOOK)
    await client.post("/api/books/", json=SAMPLE_BOOK_2)

    resp = await client.get("/api/books/", params={"keyword": "流畅"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "流畅的 Python"


@pytest.mark.asyncio
async def test_search_books_by_category(client: AsyncClient):
    """GET /api/books/?category=... should filter by category."""
    await client.post("/api/books/", json=SAMPLE_BOOK)
    resp = await client.get("/api/books/", params={"category": "计算机科学"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_search_books_pagination(client: AsyncClient):
    """GET /api/books/ with page and page_size should paginate."""
    for i in range(5):
        book = {**SAMPLE_BOOK, "isbn": f"ISBN-{i:03d}", "title": f"Book {i}"}
        await client.post("/api/books/", json=book)

    resp = await client.get("/api/books/", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["page_size"] == 2
