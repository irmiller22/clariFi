"""Performance benchmarks for the hot paths (~10k transactions).

Run with `make bench` (writes benchmarks/current.json) or `make bench-check`
(also gates against benchmarks/baseline.json). Not collected by the unit-test
run — pytest.ini's testpaths is `tests`, this lives under `benchmarks/`.
"""

from src.domain import Transaction
from src.schemas import TransactionCreate
from src.services.analytics import (
    cashflow,
    detect_anomalies,
    recurring_charges,
    rolling_average,
    spending_by_category,
    spending_timeline,
    summarize,
    top_merchants,
    trends,
)
from src.services.csv_parser import CSVParser
from src.services.normalizer import normalize_many
from src.store import TransactionStore


def test_parse(benchmark, csv_text: str) -> None:
    benchmark(CSVParser().parse, csv_text)


def test_normalize(benchmark, rows: list[TransactionCreate]) -> None:
    benchmark(normalize_many, rows)


def test_store_query(benchmark, transactions: list[Transaction]) -> None:
    store = TransactionStore()
    store.replace(transactions)
    benchmark(store.query, category="Groceries", sort_by="amount", order="desc", limit=50)


def test_summarize(benchmark, transactions: list[Transaction]) -> None:
    benchmark(summarize, transactions)


def test_spending_by_category(benchmark, transactions: list[Transaction]) -> None:
    benchmark(spending_by_category, transactions)


def test_spending_timeline(benchmark, transactions: list[Transaction]) -> None:
    benchmark(spending_timeline, transactions)


def test_trends(benchmark, transactions: list[Transaction]) -> None:
    benchmark(trends, transactions)


def test_top_merchants(benchmark, transactions: list[Transaction]) -> None:
    benchmark(top_merchants, transactions)


def test_recurring_charges(benchmark, transactions: list[Transaction]) -> None:
    benchmark(recurring_charges, transactions)


def test_detect_anomalies(benchmark, transactions: list[Transaction]) -> None:
    benchmark(detect_anomalies, transactions)


def test_rolling_average(benchmark, transactions: list[Transaction]) -> None:
    benchmark(rolling_average, transactions)


def test_cashflow(benchmark, transactions: list[Transaction]) -> None:
    benchmark(cashflow, transactions)


def test_upload_pipeline(benchmark, csv_text: str) -> None:
    """End-to-end compute path of an upload (parse -> normalize -> store ->
    summary), minus the HTTP layer. Tracks the PRD's < 500ms headline number."""

    def pipeline() -> None:
        parsed = CSVParser().parse(csv_text)
        normalized = normalize_many(parsed)
        store = TransactionStore()
        store.replace(normalized)
        summarize([s.transaction for s in store.all()])

    benchmark(pipeline)
