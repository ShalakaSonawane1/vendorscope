# VendorScope 🔍

AI-powered vendor risk analysis platform that automates security due diligence through intelligent document crawling, RAG-based query answering, and comparative risk assessment.

## 🎯 Overview

VendorScope helps security, legal, and procurement teams evaluate third-party vendors by automatically discovering, indexing, and analyzing vendor trust pages (security, privacy, compliance documentation) using advanced AI techniques.

## ✨ Features

- 🤖 **AI-Powered Analysis**: RAG architecture with OpenAI embeddings for intelligent query answering
- 🕷️ **Smart Crawler**: Automatically discovers and indexes vendor trust pages with link-following
- 📊 **Risk Assessment**: Compare multiple vendors with AI-driven security analysis
- 🔄 **Document Versioning**: Track changes in vendor security postures over time
- ⚡ **Sub-second Search**: Vector similarity search across 100+ documents
- 📝 **Cited Responses**: Every answer includes source attribution

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern async web framework
- **PostgreSQL + pgvector** - Vector database for embeddings
- **Celery + Redis** - Distributed task queue
- **SQLAlchemy** - ORM with Alembic migrations
- **OpenAI API** - GPT-4 + text-embedding-3-small

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client

### Infrastructure
- **Docker** - Containerization
- **Railway** - Hosting (backend + databases)
- **Vercel** - Frontend hosting

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API key

## 📖 Usage

1. **Add Vendors**: Click "Add Vendor" and enter vendor details (e.g., Stripe, Adyen)
2. **Wait for Crawl**: System automatically discovers and indexes trust pages (~30 seconds)
3. **Query Vendors**: Ask questions like "Is Stripe SOC 2 compliant?"
4. **Compare Vendors**: Select multiple vendors for side-by-side risk analysis

## 🏗️ Architecture
```
┌─────────────┐
│  Next.js UI │  ← User Interface
└──────┬──────┘
       │
┌──────▼──────┐
│ FastAPI     │  ← REST API
└──────┬──────┘
       │
   ┌───┴────┐
   ▼        ▼
┌──────┐ ┌──────────┐
│Celery│ │PostgreSQL│  ← Background Jobs + Vector DB
│+Redis│ │+pgvector │
└──────┘ └──────────┘
   │
   ▼
┌────────────────┐
│ Smart Crawler  │  ← Discovers trust pages
│ RAG Engine     │  ← Semantic search
│ AI Agent       │  ← Query processing
└────────────────┘
```

## 🎓 Learning Outcomes

This project demonstrates:
- Full-stack AI application development
- Distributed systems architecture
- RAG implementation with vector databases
- Production-grade async Python
- Modern React with TypeScript
- DevOps with Docker and cloud deployment

## Acknowledgments

- Built as a learning project
- Inspired by real-world vendor risk management workflows at enterprise companies
- Uses OpenAI's GPT-4 and embedding models
