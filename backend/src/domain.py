"""Canonical, normalized transaction domain model.

Amount-sign convention
----------------------
``amount`` is a signed ``Decimal`` in the card's native convention (Chase):
negative means money out (a purchase / debit), positive means money in
(a payment, refund, or credit). Downstream analytics rely on this sign, so the
normalizer must preserve it exactly — never store an absolute value.

``type`` and ``month`` are *derived*, not stored:
- ``type`` is ``"debit"`` when ``amount < 0`` and ``"credit"`` otherwise.
- ``month`` is the ``"YYYY-MM"`` bucket key of ``transaction_date``.

Because they are computed from the underlying fields, they can never disagree
with them.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

TransactionType = Literal["debit", "credit"]


class Transaction(BaseModel):
    """A normalized transaction, ready for storage and analytics."""

    model_config = ConfigDict(frozen=True)

    transaction_date: date
    post_date: date
    description: str
    merchant: str
    category: str
    # Raw card "Type" value (e.g. Sale, Payment, Return) preserved from the CSV.
    source_type: str
    amount: Decimal
    memo: str = ""
    # Source account label (e.g. "5168"), from the uploaded file. Empty if unknown.
    account: str = ""

    # mypy refuses decorators stacked on @property; computed_field is the
    # idiomatic Pydantic v2 way to expose a derived value (incl. in model_dump).
    @computed_field  # type: ignore[prop-decorator]
    @property
    def type(self) -> TransactionType:
        """Direction of money flow, derived from the amount sign."""
        return "debit" if self.amount < 0 else "credit"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def month(self) -> str:
        """Month bucket key as ``YYYY-MM`` (from the transaction date)."""
        return f"{self.transaction_date.year:04d}-{self.transaction_date.month:02d}"
