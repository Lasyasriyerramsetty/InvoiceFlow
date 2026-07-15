# Developer Guide

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16+

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-org/ap-invoice-agent.git
cd ap-invoice-agent
cp .env.example .env
```

### 2. Start Infrastructure Services

```bash
docker-compose up -d postgres redis minio chromadb
```

### 3. Install Dependencies

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. Run Development Servers

```bash
# Backend (Terminal 1)
cd backend
uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd frontend
npm run dev
```

## Project Structure

### Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── api/
│   │   ├── dependencies.py     # Auth dependencies, RBAC
│   │   └── v1/
│   │       ├── auth.py         # Authentication routes
│   │       └── invoices.py     # Invoice endpoints
│   ├── application/
│   │   └── services/
│   │       └── invoice_service.py  # Business logic services
│   ├── core/
│   │   ├── config.py           # Pydantic settings
│   │   └── security.py         # JWT, password hashing
│   └── infrastructure/
│       ├── database/
│       │   ├── models.py       # SQLAlchemy models
│       │   ├── repositories.py # Repository pattern
│       │   └── session.py      # DB session factory
│       └── storage/
│           └── minio_storage.py # MinIO/S3 client
├── requirements.txt            # Python dependencies
└── Dockerfile
```

### Frontend Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Dashboard
│   │   ├── providers.tsx       # React Query provider
│   │   ├── invoices/
│   │   │   ├── page.tsx        # Invoice list
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Invoice detail
│   │   ├── upload/
│   │   │   └── page.tsx        # Upload center
│   │   └── vendors/
│   │       └── page.tsx        # Vendor analytics
│   └── components/
│       ├── Sidebar.tsx           # Navigation
│       └── CopilotPanel.tsx      # AI assistant panel
├── package.json
└── Dockerfile
```

## AI Agent Development

### Creating a New Agent

```python
# agents/my_new_agent/agent.py
from typing import Any
from agents.base import BaseAgent

class MyNewAgent(BaseAgent):
    name = "MyNewAgent"
    description = "Description of what this agent does"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        # Your agent logic here
        
        insight = self._create_insight(
            reasoning="Why this agent made this decision",
            confidence=0.95,
            evidence=["Evidence 1", "Evidence 2"],
            suggested_resolution="Recommended action",
            business_impact="Business impact description",
            financial_impact=amount_impact,
            next_action="Next step",
        )

        return {"result": data, "insight": insight}
```

### Registering in Pipeline

```python
# agents/orchestrator/pipeline.py
from agents.my_new_agent.agent import MyNewAgent

self.agents = {
    ...
    "my_new_agent": MyNewAgent(),
}

stages = [
    ...
    ("my_new_agent", self._run_my_new_agent),
]
```

## RAG Integration

The system uses hybrid retrieval combining:

1. **Vector Search**: Sentence transformers embeddings
2. **BM25 Search**: Keyword-based ranking
3. **Reciprocal Rank Fusion**: Merging results

```python
# Indexing documents
await retriever.index_document(text, doc_id, doc_type, metadata)

# Searching
results = await retriever.search(
    query="price revision limit contract",
    filters={"document_type": "contract", "vendor": "Acme Corp"},
    top_k=5
)
```

## Testing

```bash
# Backend tests
pytest tests/

# Frontend tests
npm run test
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login, get tokens |
| GET | /api/v1/auth/me | Current user profile |
| GET | /api/v1/invoices | List all invoices |
| GET | /api/v1/invoices/{id} | Get invoice details |
| POST | /api/v1/invoices/upload | Upload invoice file |
| GET | /api/v1/exceptions | List open exceptions |
| POST | /api/v1/copilot/ask | Ask AI copilot |
| GET | /api/v1/dashboard/kpis | Dashboard metrics |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| APP_ENV | Environment (dev/staging/prod) | development |
| DATABASE_URL | PostgreSQL async URL | - |
| REDIS_URL | Redis connection | redis://localhost:6379/0 |
| JWT_SECRET_KEY | Secret for signing tokens | - |
| OPENAI_API_KEY | OpenAI API key | - |
| MINIO_ENDPOINT | MinIO server | localhost:9000 |
| AZURE_DOCUMENT_INTELLIGENCE_KEY | Azure OCR key | - |