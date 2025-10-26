"""Main FastAPI application."""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.services.csv_parser import CSVParser
import io

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


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "clariFi API",
        "version": "0.1.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/transactions/upload")
async def upload_transactions(file: UploadFile = File(...)):
    """Upload and parse CSV transactions."""
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        parser = CSVParser()
        transactions = parser.parse(csv_content)
        
        # Calculate summary
        total_spent = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)
        total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
        net_amount = total_income - total_spent
        transaction_count = len(transactions)
        avg_transaction = (total_income + total_spent) / transaction_count if transaction_count > 0 else 0
        
        summary = {
            "totalSpent": total_spent,
            "totalIncome": total_income,
            "netAmount": net_amount,
            "transactionCount": transaction_count,
            "avgTransactionAmount": avg_transaction
        }
        
        # Convert transactions to dict format
        transactions_data = [
            {
                "id": str(hash(f"{t.transaction_date}{t.description}{t.amount}")),  # Generate ID from data
                "date": t.transaction_date,  # Use transaction_date field
                "description": t.description,
                "amount": float(t.amount),
                "category": t.category,
                "type": "debit" if float(t.amount) < 0 else "credit"
            }
            for t in transactions
        ]
        
        return {
            "success": True,
            "message": f"Successfully parsed {len(transactions)} transactions",
            "transactions": transactions_data,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")


@app.get("/api/transactions")
async def get_transactions():
    """Get all transactions (placeholder for now)."""
    return {"transactions": [], "total": 0}


@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary (placeholder for now)."""
    return {
        "totalSpent": 0,
        "totalIncome": 0,
        "netAmount": 0,
        "transactionCount": 0,
        "avgTransactionAmount": 0
    }
