"""Main FastAPI application."""

from decimal import ROUND_HALF_UP, Decimal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.domain import Transaction, TransactionType
from src.schemas import (
    AnalyticsSummary,
    TransactionList,
    TransactionRead,
    UploadResult,
)
from src.services.csv_parser import CSVParseError, CSVParser
from src.services.normalizer import normalize_many
from src.store import SortField, SortOrder, StoredTransaction, store

app = FastAPI(
    title="clariFi API",
    description="Personal finance application for analyzing credit card spending patterns",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_CENTS = Decimal("0.01")


def _serialize(stored: StoredTransaction) -> TransactionRead:
    """Map a stored transaction to its client-facing representation."""
    txn = stored.transaction
    d = txn.transaction_date
    return TransactionRead(
        id=str(stored.id),
        date=f"{d.month:02d}/{d.day:02d}/{d.year:04d}",
        description=txn.description,
        amount=float(txn.amount),
        category=txn.category,
        type=txn.type,
    )


def _summarize(transactions: list[Transaction]) -> AnalyticsSummary:
    """Compute aggregate spending metrics with exact Decimal arithmetic.

    Note: this lives inline for now. LAT-73 extracts it into a dedicated
    analytics service (and refines spend-vs-income semantics).
    """
    spent = -sum((t.amount for t in transactions if t.amount < 0), Decimal(0))
    income = sum((t.amount for t in transactions if t.amount > 0), Decimal(0))
    count = len(transactions)
    gross = spent + income
    avg = gross / count if count else Decimal(0)

    def cents(value: Decimal) -> float:
        return float(value.quantize(_CENTS, rounding=ROUND_HALF_UP))

    return AnalyticsSummary(
        total_spent=cents(spent),
        total_income=cents(income),
        net_amount=cents(income - spent),
        transaction_count=count,
        avg_transaction_amount=cents(avg),
    )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - API health check."""
    return {
        "message": "clariFi API",
        "version": "0.1.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/transactions/upload")
async def upload_transactions(file: UploadFile = File(...)) -> UploadResult:
    """Upload and parse a CSV; normalize and store the transactions."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    try:
        csv_content = content.decode("utf-8")
        rows = CSVParser().parse(csv_content)
    except (UnicodeDecodeError, CSVParseError) as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {e!s}") from e

    transactions = normalize_many(rows)
    store.replace(transactions)
    stored = store.all()

    return UploadResult(
        success=True,
        message=f"Successfully parsed {len(stored)} transactions",
        transactions=[_serialize(s) for s in stored],
        summary=_summarize(transactions),
    )


@app.get("/api/transactions")
async def get_transactions(
    limit: int | None = None,
    offset: int = 0,
    category: str | None = None,
    type: TransactionType | None = None,
    search: str | None = None,
    sort: SortField = "date",
    order: SortOrder = "desc",
) -> TransactionList:
    """Return stored transactions, filtered/sorted/paginated."""
    result = store.query(
        category=category,
        txn_type=type,
        search=search,
        sort_by=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return TransactionList(
        transactions=[_serialize(s) for s in result.items],
        total=result.total,
    )


@app.get("/api/analytics/summary")
async def get_analytics_summary() -> AnalyticsSummary:
    """Aggregate spending metrics for the current transaction set."""
    return _summarize([s.transaction for s in store.all()])
