# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Range Finance is a personal finance application for analyzing credit card spending patterns via CSV uploads. The project serves as a learning platform for FastAPI (Python backend) and Next.js (React frontend), with future AI/LLM integration planned.

**Primary Purpose:** CSV-based transaction analysis and visualization
**Secondary Purpose:** Learning and practicing modern web development with TDD methodology

## Architecture

The application follows a standard client-server architecture:

```
Next.js Frontend (React) <--HTTP/REST--> FastAPI Backend (Python) <--> CSV Parser/Data Processor <--> Data Storage (In-memory/Future DB)
```

### Backend (FastAPI)
- Located in backend directory (to be created)
- Handles CSV parsing, data validation, and analytics computation
- Uses Pydantic for data validation and type safety
- Initially uses in-memory storage; future PostgreSQL/MongoDB integration planned

### Frontend (Next.js)
- Located in frontend directory (to be created)
- Provides CSV upload UI, transaction review table, and analytics dashboard
- Server-side rendering for performance
- Responsive design for desktop and mobile

### Key API Endpoints (Planned)
- `POST /api/transactions/upload` - CSV file upload
- `GET /api/transactions` - Paginated transaction list with filters
- `GET /api/analytics/summary` - Aggregated spending metrics
- `GET /api/analytics/by-category` - Category-based spending
- `GET /api/analytics/timeline` - Time-series spending data

## Test-Driven Development

**This project emphasizes TDD methodology.** Write tests before implementation code.

### Backend Testing
- Framework: pytest with pytest-asyncio
- Coverage target: 80%+
- Run tests: `pytest` (from backend directory)
- Run with coverage: `pytest --cov=. --cov-report=html`
- Test async endpoints using httpx

### Frontend Testing
- Framework: Jest + React Testing Library
- Coverage target: 70%+
- Run tests: `npm test` (from frontend directory)
- Run with coverage: `npm test -- --coverage`
- Mock API calls using MSW (Mock Service Worker)

### Testing Layers
- **Unit tests:** Individual functions and components
- **Integration tests:** API endpoints and component interactions
- **E2E tests (optional):** Complete user workflows using Playwright/Cypress

## Development Workflow

### Python Dependency Management
This project uses **uv** for Python dependency management (not pip/venv).
- Install dependencies: `uv pip install -r requirements.txt` or `uv sync`
- Add new dependency: `uv add <package>`
- Run Python scripts: `uv run <script>`

### Build and Runtime Commands
Use **Makefile** for all build, test, and runtime commands. Common targets (when implemented):
- `make install` - Install dependencies
- `make test` - Run tests
- `make test-backend` - Run backend tests
- `make test-frontend` - Run frontend tests
- `make run-backend` - Start the backend API
- `make run-frontend` - Start the frontend dev server
- `make lint` - Run linters
- `make format` - Format code

### Backend Setup (when implemented)
```bash
cd backend
uv sync  # Install dependencies with uv
```

### Frontend Setup (when implemented)
```bash
cd frontend
npm install
```

### Running the Application
- Use Makefile targets: `make run-backend` and `make run-frontend`
- Access API docs: http://localhost:8000/docs (FastAPI auto-generated Swagger UI)

### Docker and Kubernetes (Future)
The backend API will be containerized using Docker and deployed to minikube for local Kubernetes development:
- Build Docker image: `make docker-build` (planned)
- Run with minikube: `make k8s-deploy` (planned)
- This enables testing of production-like deployment locally

## CSV Format Requirements

The application must support multiple bank CSV formats with these standard fields:
- Date
- Description/Merchant
- Amount
- Category (if available)
- Transaction Type (debit/credit)

File size limit: 10MB
Performance target: Handle 10,000+ transactions smoothly

## Non-Functional Requirements

- API response time: <500ms
- Page load time: <2 seconds
- Input validation on all uploads
- CORS configuration for API
- Rate limiting on upload endpoint
- Graceful error handling with user-friendly messages

## Future Enhancements (Post-MVP)

- AI/LLM integration for spending insights and recommendations
- Multi-user support with authentication
- Budget management features
- Database persistence for historical data
- Natural language queries about spending

## References

- Full requirements: See PRD.md
- FastAPI docs: https://fastapi.tiangolo.com/
- Next.js docs: https://nextjs.org/docs
