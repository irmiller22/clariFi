"""Request-level tests for the transactions API (upload + list)."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.store import store

CSV_HEADER = "Transaction Date,Post Date,Description,Category,Type,Amount,Memo"
SAMPLE_ROWS = [
    "01/05/2025,01/06/2025,WHOLE FOODS,Groceries,Sale,-50.00,",
    "01/10/2025,01/11/2025,SHELL GAS,Gas,Sale,-40.00,",
    "01/15/2025,01/16/2025,PAYROLL,Income,Payment,2000.00,",
]


def _csv(rows: list[str] = SAMPLE_ROWS) -> str:
    return "\n".join([CSV_HEADER, *rows]) + "\n"


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    """The store is a module-level singleton; isolate each test."""
    store.clear()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _upload(client: AsyncClient, csv_text: str, filename: str = "test.csv"):
    return await client.post(
        "/api/transactions/upload",
        files={"file": (filename, csv_text.encode(), "text/csv")},
    )


class TestUpload:
    async def test_upload_stores_and_returns_transactions(self, client: AsyncClient) -> None:
        response = await _upload(client, _csv())
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert [t["id"] for t in body["transactions"]] == ["1", "2", "3"]
        assert store.count() == 3

    async def test_upload_computes_summary(self, client: AsyncClient) -> None:
        body = (await _upload(client, _csv())).json()
        summary = body["summary"]
        assert summary["totalSpent"] == 90.00
        assert summary["totalIncome"] == 2000.00
        assert summary["netAmount"] == 1910.00
        assert summary["transactionCount"] == 3
        assert summary["avgTransactionAmount"] == 696.67

    async def test_upload_rejects_non_csv_filename(self, client: AsyncClient) -> None:
        response = await _upload(client, _csv(), filename="data.txt")
        assert response.status_code == 400

    async def test_upload_rejects_malformed_csv(self, client: AsyncClient) -> None:
        response = await _upload(client, "not,the,right,columns\n1,2,3,4\n")
        assert response.status_code == 400

    async def test_replacing_upload_swaps_the_set(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        await _upload(client, _csv([SAMPLE_ROWS[0]]))
        assert store.count() == 1


class TestGetTransactions:
    async def test_empty_store_returns_empty_page(self, client: AsyncClient) -> None:
        body = (await client.get("/api/transactions")).json()
        assert body == {"transactions": [], "total": 0}

    async def test_returns_all_after_upload_sorted_date_desc(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/transactions")).json()
        assert body["total"] == 3
        # Default sort is date descending -> the Jan 15 payroll row first.
        assert body["transactions"][0]["description"] == "PAYROLL"

    async def test_filter_by_category(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/transactions", params={"category": "groceries"})).json()
        assert body["total"] == 1
        assert body["transactions"][0]["description"] == "WHOLE FOODS"

    async def test_filter_by_type_debit(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/transactions", params={"type": "debit"})).json()
        assert body["total"] == 2

    async def test_search_matches_description(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/transactions", params={"search": "shell"})).json()
        assert body["total"] == 1
        assert body["transactions"][0]["description"] == "SHELL GAS"

    async def test_pagination_limit_and_total(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/transactions", params={"limit": 1})).json()
        assert body["total"] == 3
        assert len(body["transactions"]) == 1

    async def test_sort_by_amount_ascending(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (
            await client.get("/api/transactions", params={"sort": "amount", "order": "asc"})
        ).json()
        amounts = [t["amount"] for t in body["transactions"]]
        assert amounts == sorted(amounts)
        assert amounts[0] == -50.00

    async def test_response_shape(self, client: AsyncClient) -> None:
        await _upload(client, _csv([SAMPLE_ROWS[0]]))
        txn = (await client.get("/api/transactions")).json()["transactions"][0]
        assert txn["date"] == "01/05/2025"  # MM/DD/YYYY preserved
        assert txn["amount"] == -50.00  # JSON number, sign preserved
        assert txn["type"] == "debit"


class TestAnalyticsSummaryEndpoint:
    async def test_summary_empty_is_zeroed(self, client: AsyncClient) -> None:
        body = (await client.get("/api/analytics/summary")).json()
        assert body["transactionCount"] == 0
        assert body["totalSpent"] == 0.0

    async def test_summary_reflects_uploaded_data(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/summary")).json()
        assert body["totalSpent"] == 90.00
        assert body["transactionCount"] == 3


class TestByCategoryEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        body = (await client.get("/api/analytics/by-category")).json()
        assert body == []

    async def test_returns_spend_breakdown(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/by-category")).json()
        # Income (a credit) is excluded; only the two debit categories remain.
        categories = {row["category"] for row in body}
        assert categories == {"Groceries", "Gas"}
        groceries = next(row for row in body if row["category"] == "Groceries")
        assert groceries["amount"] == 50.00
        assert groceries["count"] == 1
        assert groceries["percentage"] == round(50 / 90 * 100, 2)
