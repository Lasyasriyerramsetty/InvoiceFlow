# InvoiceFlow AI

> Enterprise-grade AI-powered Accounts Payable automation platform with multi-agent orchestration, intelligent 3-way matching, and fraud detection.

## Overview

InvoiceFlow AI is a production-quality AI application that automates invoice processing workflows using a multi-agent architecture. Built with CrewAI-inspired orchestration and LangGraph patterns, it processes invoices through 9 specialized AI agents that extract data, validate contracts, detect exceptions, assess fraud risk, and recommend actions.

## Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation                        │
│  Next.js 14 (App Router) + TypeScript + TailwindCSS      │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                        API Layer                        │
│              FastAPI + WebSocket Streaming              │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                      │
│          Services, DTOs, Workflow Orchestration            │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                      Domain Layer                       │
│   Entities, Value Objects, Domain Services, Policies     │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                    │
│  SQLAlchemy, MinIO/S3, Redis, ChromaDB, Celery, OpenAI   │
└─────────────────────────────────────────────────────────┘
```

### Multi-Agent AI Architecture

| Agent | Responsibility |
|-------|---------------|
| **Document Intake Agent** | Classify documents, assess quality, run OCR (Azure/GCP/PaddleOCR) |
| **Invoice Understanding Agent** | Extract vendor, amounts, dates, line items with confidence scores |
| **Contract Intelligence Agent** | RAG-powered clause retrieval (pricing, terms, penalties) |
| **PO Matching Agent** | 3-way matching (Invoice → PO → Goods Receipt) with mismatch detection |
| **Finance Policy Agent** | Validate approval policies, GST compliance, currency rules |
| **Exception Detection Agent** | Detect 16+ exception types with risk scoring |
| **Fraud Intelligence Agent** | ML + AI fraud detection (duplicates, patterns, anomalies) |
| **Recommendation Agent** | Generate resolutions, business/financial impact analysis |
| **Workflow Agent** | Auto-route to approvers based on amount and risk |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, TailwindCSS, Shadcn UI |
| Backend | FastAPI, Python 3.11+, SQLAlchemy, Celery |
| Database | PostgreSQL |
| Vector Store | ChromaDB / FAISS |
| Cache/Queue | Redis |
| AI/ML | OpenAI GPT-4, LangChain, Sentence Transformers |
| OCR | Azure Document Intelligence, Google Document AI, PaddleOCR |
| Storage | MinIO / AWS S3 |
| Auth | JWT, OAuth 2.0, RBAC |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
# - OPENAI_API_KEY
# - AZURE_DOCUMENT_INTELLIGENCE_KEY
# - DATABASE_URL
# - JWT_SECRET_KEY
```

### Run with Docker

```bash
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# MinIO: http://localhost:9001
# Chroma: http://localhost:8001
```

### Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Documentation

### Authentication

```bash
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Invoices

```bash
GET    /api/v1/invoices              # List invoices
GET    /api/v1/invoices/{id}         # Get invoice details
POST   /api/v1/invoices/upload       # Upload and process invoice
GET    /api/v1/exceptions            # List open exceptions
POST   /api/v1/copilot/ask         # Ask AI copilot questions
GET    /api/v1/dashboard/kpis      # Get dashboard metrics
```

## Features

- 🔍 **Multi-Agent AI**: 9 specialized agents for end-to-end processing
- 📊 **3-Way Matching**: Invoice, PO, Goods Receipt validation
- ⚠️ **Exception Detection**: 16+ exception categories with reasoning
- 🛡️ **Fraud Intelligence**: ML + AI fraud detection patterns
- 🤖 **AI Copilot**: Natural language queries about invoices
- 📈 **Risk Heatmaps**: Department vs category risk visualization
- 🎯 **Auto-Routing**: Approval workflow based on amount/risk
- 📊 **Savings Tracking**: Financial impact of automation

## Project Structure

```
invoiceflow-ai/
├── agents/
│   ├── base.py                    # Base agent with insight generation
│   ├── orchestrator/
│   │   └── pipeline.py           # Multi-agent orchestration
│   ├── document_intake/
│   ├── invoice_understanding/
│   ├── contract_intelligence/
│   ├── po_matching/
│   ├── finance_policy/
│   ├── exception_detection/
│   ├── fraud_intelligence/
│   ├── recommendation/
│   ├── workflow/
│   └── copilot/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI application
│   │   ├── api/
│   │   ├── application/
│   │   ├── core/
│   │   └── infrastructure/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   └── components/
│   └── package.json
├── ml/
│   └── fraud_detector.py
├── ocr/
│   ├── base.py
│   └── service.py
├── rag/
│   ├── chunker.py
│   ├── embeddings.py
│   └── retriever.py
└── shared/
    └── schemas/
```

## License

MIT License - Enterprise Production Ready

---

## GitHub Description

InvoiceFlow AI is an enterprise-grade AI-powered Accounts Payable automation platform that streamlines invoice processing through intelligent multi-agent orchestration. Featuring autonomous 3-way matching, fraud detection, and AI-assisted decision making, it reduces manual work by up to 80% while improving accuracy and compliance.

**Key Capabilities:**
- 🤖 9-Specialized AI Agents for end-to-end invoice processing
- 📊 3-Way Matching (Invoice, PO, Goods Receipt) with variance detection
- ⚠️ 16+ Exception Categories with automated reasoning
- 🛡️ ML-Powered Fraud Detection and anomaly identification
- 💬 AI Copilot for natural language invoice queries
- 🎯 Risk-based Auto-Routing to approvers
- 📈 Real-time Dashboard with financial insights

Built with Next.js, FastAPI, PostgreSQL, and OpenAI.