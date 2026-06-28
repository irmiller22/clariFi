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
    # A refund (credit-card "Return") models income; "Payment" would be a
    # card-payment and excluded from spend/income analytics (see LAT-94).
    "01/15/2025,01/16/2025,AMAZON REFUND,Shopping,Return,2000.00,",
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
        files={"files": (filename, csv_text.encode(), "text/csv")},
    )


async def _upload_many(client: AsyncClient, items: list[tuple[str, str]]):
    payload = [("files", (name, text.encode(), "text/csv")) for name, text in items]
    return await client.post("/api/transactions/upload", files=payload)


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

    async def test_multiple_files_are_combined(self, client: AsyncClient) -> None:
        second = "\n".join([CSV_HEADER, "02/01/2025,02/02/2025,RENT,Housing,Sale,-1000.00,"]) + "\n"
        response = await _upload_many(client, [("a.csv", _csv()), ("b.csv", second)])
        assert response.status_code == 200
        body = response.json()
        # 3 rows from a.csv + 1 from b.csv, with contiguous ids across the union.
        assert [t["id"] for t in body["transactions"]] == ["1", "2", "3", "4"]
        assert store.count() == 4
        # Combined spend: 50 + 40 (a) + 1000 (b).
        assert body["summary"]["totalSpent"] == 1090.00

    async def test_batch_with_one_malformed_file_fails_naming_it(self, client: AsyncClient) -> None:
        response = await _upload_many(
            client, [("good.csv", _csv()), ("bad.csv", "not,the,right,columns\n1,2,3,4\n")]
        )
        assert response.status_code == 400
        assert "bad.csv" in response.json()["detail"]
        assert store.count() == 0  # nothing stored when the batch fails

    async def test_mixed_credit_card_and_checking_formats(self, client: AsyncClient) -> None:
        checking = (
            "Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #\n"
            "DEBIT,06/01/2026,RENT WIRE,-1000.00,WIRE_OUTGOING,5000.00,,\n"
        )
        response = await _upload_many(client, [("card.csv", _csv()), ("bank.csv", checking)])
        assert response.status_code == 200
        body = response.json()
        assert store.count() == 4  # 3 credit-card rows + 1 checking row
        assert body["summary"]["totalSpent"] == 1090.00  # 90 (card) + 1000 (checking)


class TestGetTransactions:
    async def test_empty_store_returns_empty_page(self, client: AsyncClient) -> None:
        body = (await client.get("/api/transactions")).json()
        assert body == {"transactions": [], "total": 0}

    async def test_returns_all_after_upload_sorted_date_desc(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/transactions")).json()
        assert body["total"] == 3
        # Default sort is date descending -> the Jan 15 refund row first.
        assert body["transactions"][0]["description"] == "AMAZON REFUND"

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
        assert txn["date"] == "2025-01-05"  # ISO-8601
        assert txn["amount"] == -50.00  # JSON number, sign preserved
        assert txn["type"] == "debit"
        assert txn["account"] == "test"  # derived from the "test.csv" filename

    async def test_account_is_derived_and_filterable(self, client: AsyncClient) -> None:
        await _upload_many(
            client,
            [
                ("Chase4796_Activity.csv", _csv()),
                ("Chase5168_Activity.csv", _csv([SAMPLE_ROWS[0]])),
            ],
        )
        all_txns = (await client.get("/api/transactions")).json()
        assert {t["account"] for t in all_txns["transactions"]} == {"4796", "5168"}

        filtered = (await client.get("/api/transactions", params={"account": "5168"})).json()
        assert filtered["total"] == 1
        assert filtered["transactions"][0]["account"] == "5168"


class TestClassificationExclusion:
    """Transfers and card payments are excluded from spend analytics (LAT-94)."""

    _CHECKING = (
        "Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #\n"
        "DEBIT,01/05/2025,WHOLE FOODS,-50.00,DEBIT_CARD,1000.00,,\n"
        "DEBIT,01/06/2025,Online Transfer to SAV ...5168,-500.00,ACH_DEBIT,500.00,,\n"
        "DEBIT,01/07/2025,Payment to Chase card 4796,-300.00,ACH_DEBIT,200.00,,\n"
    )

    async def test_money_movement_excluded_from_summary(self, client: AsyncClient) -> None:
        body = (await _upload(client, self._CHECKING)).json()
        # Only WHOLE FOODS counts; the transfer and card payment are excluded.
        assert body["summary"]["totalSpent"] == 50.00
        assert body["summary"]["transactionCount"] == 1

    async def test_all_kinds_appear_in_transactions_list(self, client: AsyncClient) -> None:
        await _upload(client, self._CHECKING)
        txns = (await client.get("/api/transactions")).json()["transactions"]
        kinds = {t["description"]: t["kind"] for t in txns}
        assert kinds["WHOLE FOODS"] == "spending"
        assert kinds["Online Transfer to SAV ...5168"] == "transfer"
        assert kinds["Payment to Chase card 4796"] == "card_payment"

    async def test_filter_by_kind(self, client: AsyncClient) -> None:
        await _upload(client, self._CHECKING)
        body = (await client.get("/api/transactions", params={"kind": "transfer"})).json()
        assert body["total"] == 1
        assert body["transactions"][0]["kind"] == "transfer"

    async def test_by_category_excludes_money_movement(self, client: AsyncClient) -> None:
        await _upload(client, self._CHECKING)
        cats = (await client.get("/api/analytics/by-category")).json()
        # Only the WHOLE FOODS spend remains after excluding movement.
        assert sum(c["amount"] for c in cats) == 50.00


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


class TestTimelineEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        body = (await client.get("/api/analytics/timeline")).json()
        assert body == []

    async def test_monthly_default_returns_points(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/timeline")).json()
        # All sample rows are in Jan 2025 -> one monthly bucket of the spend.
        assert len(body) == 1
        assert body[0]["date"] == "2025-01-01"
        assert body[0]["amount"] == 90.00
        assert body[0]["cumulative"] == 90.00

    async def test_daily_granularity(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/timeline", params={"granularity": "day"})).json()
        # Spend on Jan 5 and Jan 10; Jan 6-9 gap-filled -> 6 daily points.
        assert len(body) == 6
        assert body[0]["date"] == "2025-01-05"
        assert body[-1]["cumulative"] == 90.00

    async def test_rejects_invalid_granularity(self, client: AsyncClient) -> None:
        response = await client.get("/api/analytics/timeline", params={"granularity": "yearly"})
        assert response.status_code == 422


class TestTrendsEndpoint:
    async def test_empty_store_returns_empty_series(self, client: AsyncClient) -> None:
        body = (await client.get("/api/analytics/trends")).json()
        assert body == {"overall": [], "byCategory": []}

    async def test_returns_camelcase_trend_shape(self, client: AsyncClient) -> None:
        # All sample rows are January -> a single overall month, flat (no prior).
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/trends")).json()
        assert len(body["overall"]) == 1
        point = body["overall"][0]
        assert point["month"] == "2025-01"
        assert point["amount"] == 90.00
        assert point["pctChange"] is None
        assert point["direction"] == "flat"

    async def test_rejects_non_positive_months(self, client: AsyncClient) -> None:
        response = await client.get("/api/analytics/trends", params={"months": 0})
        assert response.status_code == 422


class TestTopMerchantsEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        body = (await client.get("/api/analytics/top-merchants")).json()
        assert body == []

    async def test_ranks_by_spend_excluding_income(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/top-merchants")).json()
        # PAYROLL is a credit -> excluded; spend ranks WHOLE FOODS (50) over SHELL GAS (40).
        assert [m["merchant"] for m in body] == ["WHOLE FOODS", "SHELL GAS"]
        assert body[0]["amount"] == 50.00
        assert body[0]["count"] == 1

    async def test_limit_and_by_count_params(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (
            await client.get("/api/analytics/top-merchants", params={"limit": 1, "by": "count"})
        ).json()
        assert len(body) == 1

    async def test_rejects_invalid_by(self, client: AsyncClient) -> None:
        response = await client.get("/api/analytics/top-merchants", params={"by": "alphabetical"})
        assert response.status_code == 422


_RECURRING_CSV = [
    "01/01/2025,01/02/2025,NETFLIX,Entertainment,Sale,-15.99,",
    "02/01/2025,02/02/2025,NETFLIX,Entertainment,Sale,-15.99,",
    "03/01/2025,03/02/2025,NETFLIX,Entertainment,Sale,-15.99,",
]


class TestRecurringEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        body = (await client.get("/api/analytics/recurring")).json()
        assert body == []

    async def test_detects_monthly_subscription(self, client: AsyncClient) -> None:
        await _upload(client, _csv(_RECURRING_CSV))
        body = (await client.get("/api/analytics/recurring")).json()
        assert len(body) == 1
        charge = body[0]
        assert charge["merchant"] == "NETFLIX"
        assert charge["cadence"] == "monthly"
        assert charge["typicalAmount"] == 15.99
        assert charge["occurrences"] == 3
        assert charge["lastDate"] == "2025-03-01"
        assert charge["nextExpectedDate"] == "2025-04-01"


_ANOMALY_CSV = [
    "01/01/2025,01/02/2025,CAFE A,Food,Sale,-20.00,",
    "01/02/2025,01/03/2025,CAFE B,Food,Sale,-20.00,",
    "01/03/2025,01/04/2025,CAFE C,Food,Sale,-20.00,",
    "01/04/2025,01/05/2025,CAFE D,Food,Sale,-20.00,",
    "01/05/2025,01/06/2025,FANCY DINNER,Food,Sale,-200.00,",
]


class TestAnomaliesEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        assert (await client.get("/api/analytics/anomalies")).json() == []

    async def test_flags_large_outlier(self, client: AsyncClient) -> None:
        await _upload(client, _csv(_ANOMALY_CSV))
        body = (await client.get("/api/analytics/anomalies")).json()
        assert len(body) == 1
        assert body[0]["amount"] == 200.00
        assert body[0]["categoryMedian"] == 20.00


class TestRollingAverageEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        assert (await client.get("/api/analytics/rolling-average")).json() == []

    async def test_returns_monthly_points(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/rolling-average")).json()
        assert len(body) == 1
        assert body[0]["spend"] == 90.00
        assert body[0]["movingAverage"] == 90.00

    async def test_rejects_non_positive_window(self, client: AsyncClient) -> None:
        response = await client.get("/api/analytics/rolling-average", params={"window": 0})
        assert response.status_code == 422


class TestCashflowEndpoint:
    async def test_empty_store_returns_empty_list(self, client: AsyncClient) -> None:
        assert (await client.get("/api/analytics/cashflow")).json() == []

    async def test_income_spend_net(self, client: AsyncClient) -> None:
        await _upload(client, _csv())
        body = (await client.get("/api/analytics/cashflow")).json()
        assert len(body) == 1
        assert body[0]["income"] == 2000.00
        assert body[0]["spend"] == 90.00
        assert body[0]["net"] == 1910.00
