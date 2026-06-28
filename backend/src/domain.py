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

import re
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

TransactionType = Literal["debit", "credit"]

# What a transaction *is*, for analytics. ``transfer`` and ``card_payment`` are
# internal money movement (not spending or income) and are excluded from spend
# analytics; ``fee`` counts as spending.
TransactionKind = Literal["spending", "income", "transfer", "card_payment", "fee"]

# Heuristics over the description / source_type. Conservative on purpose: only
# clearly-internal movement is excluded, so real external payments (e.g. a wire
# to a third party) still count as spending.
_CARD_PAYMENT_RE = re.compile(r"payment to chase card|automatic payment|autopay", re.IGNORECASE)
_TRANSFER_RE = re.compile(
    r"online transfer (to|from)|transfer of funds|transfer (to|from) (sav|chk)", re.IGNORECASE
)
_FEE_RE = re.compile(r"\bfee\b|service charge|overdraft", re.IGNORECASE)


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def kind(self) -> TransactionKind:
        """Classify the transaction for analytics (see ``TransactionKind``).

        A credit-card "Payment" (the pay-your-card credit) and matching checking
        "Payment to Chase card" rows are both ``card_payment`` — excluding them
        avoids double-counting the same money across statement and account.
        """
        if self.source_type.upper() == "PAYMENT" or _CARD_PAYMENT_RE.search(self.description):
            return "card_payment"
        if _TRANSFER_RE.search(self.description):
            return "transfer"
        if self.source_type.upper() == "FEE_TRANSACTION" or _FEE_RE.search(self.description):
            return "fee"
        return "income" if self.amount > 0 else "spending"

    @property
    def is_money_movement(self) -> bool:
        """True for internal transfers / card payments — excluded from spend."""
        return self.kind in ("transfer", "card_payment")
