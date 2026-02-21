# AI Career Intelligence Platform

Production-grade career intelligence platform with skill extraction, role matching, job recommendations, and AI career mentor.

## Tech Stack

**Backend:** Python 3.12, Django, DRF, PostgreSQL, JWT (HTTP-only cookies), AWS S3, PyMuPDF, spaCy, Sentence Transformers, FAISS, APScheduler, Google AI Studio, Adzuna

**Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, Axios (cookie auth)

## Quick Start

### Backend

```bash
cd backend
cp ../.env.example ../.env
# Edit .env with SECRET_KEY, DATABASE_URL, etc.

python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# PostgreSQL required
python manage.py migrate
python manage.py seed_roles
python manage.py build_faiss_index
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
# Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
npm run dev
```

### Docker

```bash
cp .env.example .env
# Edit .env
docker-compose up -d
```

## Environment Variables

See `.env.example` for required variables: `SECRET_KEY`, `DATABASE_URL`, `AWS_*`, `GOOGLE_AI_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_API_KEY`.

## Architecture

- **accounts:** Custom User (UUID, email, role), JWT + HTTP-only cookies, rotating refresh tokens
- **documents:** S3 pre-signed uploads, PyMuPDF parsing
- **skills:** Hybrid extraction (FlashText + spaCy + optional LLM), normalization, deduplication
- **embeddings:** Sentence Transformers (all-MiniLM-L6-v2), FAISS index
- **recommendations:** Role matching (FAISS → re-rank → Top 5), skill gap, learning plan
- **jobs:** Adzuna ingestion (APScheduler, 24h), skill-matched jobs
- **chatbot:** Google AI Studio, context-aware career mentor
