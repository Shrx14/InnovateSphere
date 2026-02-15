# InnovateSphere

AI-powered research idea generation platform with evidence-grounded pipelines, human-in-the-loop governance, and novelty analysis.

## Architecture

**3-shell frontend** (Admin / User / Public) built with React + Tailwind CSS.  
**3-mode backend** (Demo / Hybrid / Production) built with Flask + SQLAlchemy.  
**Database**: Neon PostgreSQL (cloud-native serverless Postgres).  
**LLM**: Ollama (qwen2.5:7b) or OpenAI (gpt-4o-mini) with automatic fallback.

### Generation Pipeline

| Mode | Passes | Evidence | Novelty | Use Case |
|------|--------|----------|---------|----------|
| Demo | 1-pass | Minimal | Skipped | Fast demos |
| Hybrid | 2-pass | Live retrieval (arXiv + GitHub) | Skipped | Daily usage |
| Production | 4-pass | Full retrieval + validation | Full analysis | Research-grade |

## Features

- **Evidence-Grounded Generation**: Multi-pass LLM pipeline with live source retrieval from arXiv and GitHub
- **Novelty Analysis**: Multi-engine novelty scoring (semantic, structural, temporal, cross-domain)
- **HITL Governance**: Admin verdict system (validate/downgrade/reject), human-verified toggle, hallucination flagging
- **Generation Traces**: Full audit trail of every pipeline phase for transparency
- **Bias Transparency**: Configurable bias profiles with penalty breakdowns visible to admins
- **Abuse Detection**: Application-level rate limiting with auto-block after repeated infractions
- **JWT Auth**: Access + refresh tokens with real logout (token blocklist)
- **3-Shell Frontend**: Separate Admin, User, and Public interfaces

## Tech Stack

### Backend
- **Flask 2.3** + Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Caching, Flask-Limiter
- **Pydantic v2** schema validation for LLM outputs
- **Sentence-Transformers** (all-MiniLM-L6-v2) for semantic embeddings
- **PostgreSQL** on Neon (pooler-safe connection handling)

### Frontend
- **React** (Create React App) + React Router v6
- **Tailwind CSS** (dark theme, neutral palette)
- **Recharts** for admin analytics charts
- **Axios** with automatic token refresh interceptor

## Project Structure

```
├── backend/
│   ├── core/           # App factory, config, models, DB
│   ├── api/routes/     # REST endpoints (admin, analytics, auth, generation, ideas, novelty, public)
│   ├── ai/             # LLM client, prompts, bias registry
│   ├── generation/     # Pipeline (generator, constraints, job_queue, schemas)
│   ├── novelty/        # Multi-engine novelty analysis
│   ├── retrieval/      # arXiv + GitHub live retrieval, source reputation
│   ├── semantic/       # Embedding, filtering, ranking
│   ├── scripts/        # DB migrations, seed data, optimization
│   └── utils/          # Auth helpers, serializers, health checks
├── frontend/
│   └── src/
│       ├── features/   # Admin, User, Public shells + pages
│       ├── context/    # Auth context (JWT + refresh)
│       ├── hooks/      # Custom React hooks
│       └── lib/        # API client with interceptors
├── tests/
│   ├── backend/        # Unit tests (16 test files)
│   ├── integration/    # Integration tests
│   └── unit/           # Additional unit tests
└── docs/               # Architecture docs, diagrams
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Neon PostgreSQL account (or local PostgreSQL)
- Ollama (optional, for local LLM) or OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, LLM settings

python run.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm start                      # Dev server on http://localhost:3000
npm run build                  # Production build
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Neon PostgreSQL connection string |
| `SECRET_KEY` | — | Flask secret key |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `LLM_MODEL_NAME` | `qwen2.5:7b` | Model name |
| `OPENAI_API_KEY` | — | Required if provider is `openai` |
| `DEMO_MODE` | `false` | Enable 1-pass demo pipeline |
| `HYBRID_MODE` | `true` | Enable 2-pass hybrid pipeline |
| `MIN_EVIDENCE_REQUIRED` | `3` | Min sources before LLM generation |
| `MIN_NOVELTY_SCORE` | `25` | Min novelty to pass evidence gate |

## API Overview

### Public
- `GET /api/public/ideas` — Browse public ideas
- `GET /api/public/stats` — Platform statistics
- `GET /api/public/domains` — Available domains

### Auth
- `POST /api/auth/register` — Register
- `POST /api/auth/login` — Login (returns access + refresh tokens)
- `POST /api/auth/refresh` — Refresh access token
- `POST /api/auth/logout` — Logout (revokes tokens)

### User (JWT required)
- `POST /api/generate` — Generate idea (async, returns job_id)
- `GET /api/generate/status/<job_id>` — Poll generation progress
- `POST /api/ideas/<id>/feedback` — Submit feedback
- `POST /api/ideas/<id>/review` — Submit review

### Admin (JWT + admin role)
- `GET /api/admin/ideas/quality-review` — Review queue
- `POST /api/admin/ideas/<id>/verdict` — Submit verdict
- `POST /api/admin/ideas/<id>/human-verified` — Toggle human-verified
- `POST /api/admin/ideas/<id>/sources/<sid>/hallucinated` — Flag hallucination
- `GET /api/admin/ideas/<id>/generation-trace` — View generation trace
- `POST /api/admin/ideas/<id>/rescore` — Recalculate scores
- `GET /api/admin/abuse-events` — View abuse events

### Analytics (JWT + admin role)
- `GET /api/admin/domains` — Domain statistics
- `GET /api/admin/trends` — Generation trends
- `GET /api/admin/distributions` — Score distributions
- `GET /api/admin/user-domains` — User domain preferences

## Testing

```bash
# Run all backend tests
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/backend/test_generation_schemas.py -v
python -m pytest tests/backend/test_llm_client.py -v
python -m pytest tests/backend/test_job_queue.py -v
```

## Database Migrations

For new deployments, `db.create_all()` runs automatically on startup and creates missing tables.

For adding columns to existing tables, run the DDL script:
```bash
psql $DATABASE_URL -f backend/scripts/add_missing_columns.sql
```

## License

MIT
