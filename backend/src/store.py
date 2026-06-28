"""In-memory, single-user transaction store.

Holds the most recently uploaded set of normalized transactions so the
analytics endpoints have something to read without a database.

**Single-user semantics:** a new upload *replaces* the current set
(:meth:`TransactionStore.replace`). Accumulating across multiple uploads is a
syncing-era concern and is deferred until persistence lands.

The store is the **identity authority**: it assigns stable ids on ``replace``
and hands back :class:`StoredTransaction` records. The query surface
(filter / sort / paginate) is intentionally narrow so a future database-backed
DAO can implement the same contract and be swapped in behind it.
"""

from dataclasses import dataclass
from typing import Literal

from src.domain import Transaction, TransactionKind, TransactionType

SortField = Literal["date", "amount", "merchant", "category"]
SortOrder = Literal["asc", "desc"]


@dataclass(frozen=True)
class StoredTransaction:
    """A canonical :class:`~src.domain.Transaction` plus its store-assigned id."""

    id: int
    transaction: Transaction


@dataclass(frozen=True)
class QueryResult:
    """A page of results plus the total number of matches before pagination."""

    items: list[StoredTransaction]
    total: int


# Sort key extractors. String keys fold case so sorting is human-friendly.
_SORT_KEYS = {
    "date": lambda s: s.transaction.transaction_date,
    "amount": lambda s: s.transaction.amount,
    "merchant": lambda s: s.transaction.merchant.casefold(),
    "category": lambda s: s.transaction.category.casefold(),
}


class TransactionStore:
    """A single-user, in-memory store of normalized transactions."""

    def __init__(self) -> None:
        self._items: list[StoredTransaction] = []

    def replace(self, transactions: list[Transaction]) -> None:
        """Replace the entire set, assigning fresh 1-based ids in order."""
        self._items = [
            StoredTransaction(id=index, transaction=txn)
            for index, txn in enumerate(transactions, start=1)
        ]

    def clear(self) -> None:
        """Remove all transactions."""
        self._items = []

    def all(self) -> list[StoredTransaction]:
        """Return every stored transaction in insertion order."""
        return list(self._items)

    def count(self) -> int:
        """Return the number of stored transactions."""
        return len(self._items)

    def query(
        self,
        *,
        category: str | None = None,
        txn_type: TransactionType | None = None,
        kind: TransactionKind | None = None,
        account: str | None = None,
        search: str | None = None,
        sort_by: SortField = "date",
        order: SortOrder = "desc",
        limit: int | None = None,
        offset: int = 0,
    ) -> QueryResult:
        """Filter, sort, and paginate the stored transactions.

        ``total`` in the result is the number of matches *after* filtering but
        *before* pagination, so callers can render page counts.
        """
        matches = [
            s for s in self._items if self._matches(s, category, txn_type, kind, account, search)
        ]

        matches.sort(key=_SORT_KEYS[sort_by], reverse=(order == "desc"))

        total = len(matches)
        page = matches[offset:] if limit is None else matches[offset : offset + limit]
        return QueryResult(items=page, total=total)

    @staticmethod
    def _matches(
        stored: StoredTransaction,
        category: str | None,
        txn_type: TransactionType | None,
        kind: TransactionKind | None,
        account: str | None,
        search: str | None,
    ) -> bool:
        txn = stored.transaction
        if category is not None and txn.category.casefold() != category.casefold():
            return False
        if txn_type is not None and txn.type != txn_type:
            return False
        if kind is not None and txn.kind != kind:
            return False
        if account is not None and txn.account.casefold() != account.casefold():
            return False
        return not (search is not None and search.casefold() not in txn.description.casefold())


# Module-level singleton used by the API layer (single-user app).
store = TransactionStore()
