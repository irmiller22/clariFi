"""Tests for the in-memory TransactionStore."""

from datetime import date
from decimal import Decimal

from src.domain import Transaction
from src.store import StoredTransaction, TransactionStore


def _tx(
    *,
    day: int = 1,
    description: str = "Coffee",
    merchant: str | None = None,
    category: str = "Food",
    amount: str = "-5.00",
    account: str = "",
) -> Transaction:
    """Build a Transaction for January 2025 with the given fields."""
    return Transaction(
        transaction_date=date(2025, 1, day),
        post_date=date(2025, 1, day),
        description=description,
        merchant=merchant if merchant is not None else description,
        category=category,
        source_type="Sale",
        amount=Decimal(amount),
        account=account,
    )


class TestReplaceAndRead:
    """replace/all/count basics and single-user replace semantics."""

    def test_empty_store_returns_nothing(self) -> None:
        store = TransactionStore()
        assert store.all() == []
        assert store.count() == 0

    def test_replace_assigns_sequential_ids_in_order(self) -> None:
        store = TransactionStore()
        store.replace([_tx(description="A"), _tx(description="B")])
        stored = store.all()
        assert all(isinstance(s, StoredTransaction) for s in stored)
        assert [s.id for s in stored] == [1, 2]
        assert [s.transaction.description for s in stored] == ["A", "B"]

    def test_replace_swaps_the_whole_set_and_resets_ids(self) -> None:
        store = TransactionStore()
        store.replace([_tx(description="old1"), _tx(description="old2")])
        store.replace([_tx(description="new")])
        assert store.count() == 1
        assert [s.id for s in store.all()] == [1]
        assert store.all()[0].transaction.description == "new"

    def test_clear_empties_the_store(self) -> None:
        store = TransactionStore()
        store.replace([_tx()])
        store.clear()
        assert store.count() == 0


class TestFilters:
    """query() filtering by category, type, and search."""

    def _store(self) -> TransactionStore:
        store = TransactionStore()
        store.replace(
            [
                _tx(description="Whole Foods", category="Groceries", amount="-50.00"),
                _tx(description="Shell Gas", category="Transport", amount="-40.00"),
                _tx(description="Payroll", category="Income", amount="2000.00"),
            ]
        )
        return store

    def test_filter_by_category_is_case_insensitive(self) -> None:
        result = self._store().query(category="groceries")
        assert result.total == 1
        assert result.items[0].transaction.description == "Whole Foods"

    def test_filter_by_type_debit(self) -> None:
        result = self._store().query(txn_type="debit")
        assert result.total == 2
        assert {i.transaction.category for i in result.items} == {"Groceries", "Transport"}

    def test_filter_by_type_credit(self) -> None:
        result = self._store().query(txn_type="credit")
        assert result.total == 1
        assert result.items[0].transaction.category == "Income"

    def test_search_matches_description_case_insensitively(self) -> None:
        result = self._store().query(search="foods")
        assert result.total == 1
        assert result.items[0].transaction.description == "Whole Foods"

    def test_filters_combine(self) -> None:
        result = self._store().query(txn_type="debit", search="gas")
        assert result.total == 1
        assert result.items[0].transaction.description == "Shell Gas"

    def test_filter_by_account(self) -> None:
        store = TransactionStore()
        store.replace(
            [
                _tx(description="Card buy", account="4796"),
                _tx(description="Bank buy", account="5168"),
                _tx(description="Card buy 2", account="4796"),
            ]
        )
        result = store.query(account="4796")
        assert result.total == 2
        assert all(i.transaction.account == "4796" for i in result.items)


class TestSorting:
    """query() sorting by each supported field and order."""

    def _store(self) -> TransactionStore:
        store = TransactionStore()
        store.replace(
            [
                _tx(day=3, description="Beta", category="B", amount="-30.00"),
                _tx(day=1, description="alpha", category="A", amount="-10.00"),
                _tx(day=2, description="Gamma", category="C", amount="-20.00"),
            ]
        )
        return store

    def test_default_sort_is_date_descending(self) -> None:
        result = self._store().query()
        assert [i.transaction.transaction_date.day for i in result.items] == [3, 2, 1]

    def test_sort_by_amount_ascending(self) -> None:
        result = self._store().query(sort_by="amount", order="asc")
        assert [i.transaction.amount for i in result.items] == [
            Decimal("-30.00"),
            Decimal("-20.00"),
            Decimal("-10.00"),
        ]

    def test_sort_by_merchant_is_case_insensitive(self) -> None:
        result = self._store().query(sort_by="merchant", order="asc")
        assert [i.transaction.description for i in result.items] == ["alpha", "Beta", "Gamma"]

    def test_sort_by_category_descending(self) -> None:
        result = self._store().query(sort_by="category", order="desc")
        assert [i.transaction.category for i in result.items] == ["C", "B", "A"]


class TestPagination:
    """query() pagination via limit/offset; total ignores the page window."""

    def _store(self) -> TransactionStore:
        store = TransactionStore()
        store.replace([_tx(day=d, amount=f"-{d}.00") for d in range(1, 6)])  # 5 txns
        return store

    def test_limit_caps_page_size_but_total_is_full_count(self) -> None:
        result = self._store().query(sort_by="amount", order="asc", limit=2)
        assert result.total == 5
        assert len(result.items) == 2

    def test_offset_skips(self) -> None:
        result = self._store().query(sort_by="date", order="asc", limit=2, offset=2)
        assert [i.transaction.transaction_date.day for i in result.items] == [3, 4]

    def test_filtered_total_reflects_filter_not_pagination(self) -> None:
        store = self._store()
        result = store.query(txn_type="debit", limit=1)
        assert result.total == 5
        assert len(result.items) == 1
