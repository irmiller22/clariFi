"""Main FastAPI application."""

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.domain import Transaction, TransactionType
from src.schemas import (
    AnalyticsSummary,
    AnomalyRead,
    CashflowRead,
    CategorySpendingRead,
    CategoryTrendRead,
    MerchantSpendingRead,
    MonthlyTrendRead,
    RecurringChargeRead,
    RollingAverageRead,
    SpendingTrendsRead,
    TimelinePointRead,
    TransactionList,
    TransactionRead,
    UploadResult,
)
from src.services.analytics import (
    Anomaly,
    CashflowPoint,
    CategorySpending,
    Granularity,
    MerchantSpending,
    MonthlyPoint,
    RankBy,
    RecurringCharge,
    RollingAveragePoint,
    SpendingSummary,
    SpendingTrends,
    TimelinePoint,
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


def _serialize(stored: StoredTransaction) -> TransactionRead:
    """Map a stored transaction to its client-facing representation."""
    txn = stored.transaction
    return TransactionRead(
        id=str(stored.id),
        date=txn.transaction_date.isoformat(),
        description=txn.description,
        amount=float(txn.amount),
        category=txn.category,
        type=txn.type,
    )


def _summary_dto(summary: SpendingSummary) -> AnalyticsSummary:
    """Convert the Decimal summary into the float-valued response DTO."""
    return AnalyticsSummary(
        total_spent=float(summary.total_spent),
        total_income=float(summary.total_income),
        net_amount=float(summary.net_amount),
        transaction_count=summary.transaction_count,
        avg_transaction_amount=float(summary.avg_transaction_amount),
    )


def _category_dto(category: CategorySpending) -> CategorySpendingRead:
    """Convert a Decimal category breakdown into the float-valued response DTO."""
    return CategorySpendingRead(
        category=category.category,
        amount=float(category.amount),
        count=category.count,
        percentage=float(category.percentage),
    )


def _timeline_dto(point: TimelinePoint) -> TimelinePointRead:
    """Convert a Decimal timeline point into the float-valued response DTO."""
    return TimelinePointRead(
        date=point.date.isoformat(),
        amount=float(point.amount),
        cumulative=float(point.cumulative),
    )


def _monthly_trend_dto(point: MonthlyPoint) -> MonthlyTrendRead:
    """Convert a Decimal monthly trend point into the float-valued response DTO."""
    return MonthlyTrendRead(
        month=point.month,
        amount=float(point.amount),
        delta=float(point.delta),
        pct_change=None if point.pct_change is None else float(point.pct_change),
        direction=point.direction,
    )


def _merchant_dto(merchant: MerchantSpending) -> MerchantSpendingRead:
    """Convert a Decimal merchant aggregate into the float-valued response DTO."""
    return MerchantSpendingRead(
        merchant=merchant.merchant,
        amount=float(merchant.amount),
        count=merchant.count,
    )


def _recurring_dto(charge: RecurringCharge) -> RecurringChargeRead:
    """Convert a Decimal recurring charge into the float-valued response DTO."""
    return RecurringChargeRead(
        merchant=charge.merchant,
        cadence=charge.cadence,
        typical_amount=float(charge.typical_amount),
        occurrences=charge.occurrences,
        last_date=charge.last_date.isoformat(),
        next_expected_date=charge.next_expected_date.isoformat(),
    )


def _anomaly_dto(anomaly: Anomaly) -> AnomalyRead:
    """Convert a Decimal anomaly into the float-valued response DTO."""
    return AnomalyRead(
        date=anomaly.transaction_date.isoformat(),
        description=anomaly.description,
        category=anomaly.category,
        amount=float(anomaly.amount),
        category_median=float(anomaly.category_median),
    )


def _rolling_dto(point: RollingAveragePoint) -> RollingAverageRead:
    """Convert a Decimal rolling-average point into the float-valued response DTO."""
    return RollingAverageRead(
        month=point.month,
        spend=float(point.spend),
        moving_average=float(point.moving_average),
    )


def _cashflow_dto(point: CashflowPoint) -> CashflowRead:
    """Convert a Decimal cashflow point into the float-valued response DTO."""
    return CashflowRead(
        month=point.month,
        income=float(point.income),
        spend=float(point.spend),
        net=float(point.net),
    )


def _trends_dto(result: SpendingTrends) -> SpendingTrendsRead:
    """Convert the Decimal trends result into the float-valued response DTO."""
    return SpendingTrendsRead(
        overall=[_monthly_trend_dto(p) for p in result.overall],
        by_category=[
            CategoryTrendRead(
                category=trend.category,
                points=[_monthly_trend_dto(p) for p in trend.points],
            )
            for trend in result.by_category
        ],
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
async def upload_transactions(files: list[UploadFile] = File(...)) -> UploadResult:
    """Upload one or more CSVs; parse, normalize, and store the combined set.

    All files in a single request become the current set (single-user replace);
    a malformed file fails the whole batch, naming the offending file.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    parser = CSVParser()
    transactions: list[Transaction] = []
    for upload in files:
        if not upload.filename or not upload.filename.lower().endswith(".csv"):
            name = upload.filename or "file"
            raise HTTPException(status_code=400, detail=f"{name} must be a CSV")
        content = await upload.read()
        try:
            rows = parser.parse(content.decode("utf-8"))
        except (UnicodeDecodeError, CSVParseError) as e:
            raise HTTPException(
                status_code=400, detail=f"Error parsing {upload.filename}: {e!s}"
            ) from e
        transactions.extend(normalize_many(rows))

    store.replace(transactions)
    stored = store.all()

    return UploadResult(
        success=True,
        message=f"Successfully parsed {len(stored)} transactions from {len(files)} file(s)",
        transactions=[_serialize(s) for s in stored],
        summary=_summary_dto(summarize(transactions)),
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
    return _summary_dto(summarize([s.transaction for s in store.all()]))


@app.get("/api/analytics/by-category")
async def get_category_analytics() -> list[CategorySpendingRead]:
    """Spend grouped by category for the current transaction set."""
    breakdown = spending_by_category([s.transaction for s in store.all()])
    return [_category_dto(c) for c in breakdown]


@app.get("/api/analytics/timeline")
async def get_timeline_analytics(
    granularity: Granularity = "month",
) -> list[TimelinePointRead]:
    """Spend over time (gap-filled) at the requested granularity."""
    timeline = spending_timeline([s.transaction for s in store.all()], granularity)
    return [_timeline_dto(p) for p in timeline]


@app.get("/api/analytics/trends")
async def get_trends_analytics(
    category: str | None = None,
    months: int | None = Query(default=None, ge=1),
) -> SpendingTrendsRead:
    """Month-over-month spend trends, overall and by category."""
    result = trends(
        [s.transaction for s in store.all()],
        category=category,
        months=months,
    )
    return _trends_dto(result)


@app.get("/api/analytics/top-merchants")
async def get_top_merchants(
    limit: int = Query(default=10, ge=1),
    by: RankBy = "spend",
) -> list[MerchantSpendingRead]:
    """Top merchants ranked by spend (default) or transaction count."""
    result = top_merchants([s.transaction for s in store.all()], limit=limit, by=by)
    return [_merchant_dto(m) for m in result]


@app.get("/api/analytics/recurring")
async def get_recurring_charges() -> list[RecurringChargeRead]:
    """Detected recurring charges / subscriptions for the current set."""
    result = recurring_charges([s.transaction for s in store.all()])
    return [_recurring_dto(c) for c in result]


@app.get("/api/analytics/anomalies")
async def get_anomalies() -> list[AnomalyRead]:
    """Transactions that are unusually large for their category."""
    result = detect_anomalies([s.transaction for s in store.all()])
    return [_anomaly_dto(a) for a in result]


@app.get("/api/analytics/rolling-average")
async def get_rolling_average(
    window: int = Query(default=3, ge=1),
) -> list[RollingAverageRead]:
    """Monthly spend with a trailing moving average over ``window`` months."""
    result = rolling_average([s.transaction for s in store.all()], window=window)
    return [_rolling_dto(p) for p in result]


@app.get("/api/analytics/cashflow")
async def get_cashflow() -> list[CashflowRead]:
    """Monthly income, spend, and net for the current transaction set."""
    result = cashflow([s.transaction for s in store.all()])
    return [_cashflow_dto(p) for p in result]
