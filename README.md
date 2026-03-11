# InnovateSphere

AI-powered research idea generation platform with evidence-grounded pipelines, human-in-the-loop governance, and novelty analysis.

## Architecture

**3-shell frontend** (Admin / User / Public) built with React + Vite + Tailwind CSS.  
**3-mode backend** (Demo / Hybrid / Production) built with Flask + SQLAlchemy.  
**Database**: Neon PostgreSQL (cloud-native serverless Postgres) with pgvector.  
**LLM**: Ollama (qwen2.5:7b) or OpenAI with automatic fallback.

### Generation Pipeline

| Mode | Passes | Evidence | Novelty | Use Case | Status |
|------|--------|----------|---------|----------|--------|
| Demo | 1-pass | Minimal | Skipped | Fast demos | Active |
| Hybrid | 2-pass | Live retrieval (arXiv + GitHub) | Skipped | Daily usage | **Active (default)** |
| Production | 4-pass | Full retrieval + validation | Full analysis | Research-grade | Theoretical |

## Features

- **Evidence-Grounded Generation**: Multi-pass LLM pipeline with live source retrieval from arXiv and GitHub
- **Async Generation with SSE**: Job-based async generation with Server-Sent Events for real-time progress streaming
- **Novelty Analysis**: Multi-engine novelty scoring (semantic, structural, temporal, cross-domain)
- **HITL Governance**: Admin verdict system (validate/downgrade/reject), human-verified toggle, hallucination flagging
- **Generation Traces**: Full audit trail of every pipeline phase (Phase 0–4) for transparency
- **Bias Transparency**: Configurable bias profiles with penalty breakdowns visible to admins
- **Abuse Detection**: Application-level rate limiting with auto-block after repeated infractions
- **JWT Auth**: Access + refresh tokens with real logout (token blocklist)
- **3-Shell Frontend**: Separate Admin, User, and Public interfaces with feature-based architecture
- **Component Library**: Radix UI primitives + custom UI components (Badge, Card, Dialog, ScoreDisplay, etc.)

## Tech Stack

### Backend
- **Flask 2.3.3** + Flask-SQLAlchemy 3.0.5, Flask-JWT-Extended, Flask-Caching, Flask-Limiter, Flask-Migrate
- **Pydantic v2** schema validation for LLM outputs
- **Sentence-Transformers** (all-MiniLM-L6-v2) for semantic embeddings
- **PostgreSQL** on Neon with pgvector extension (pooler-safe connection handling)
- **OpenAI SDK** (>=1.0.0) for cloud LLM integration

### Frontend
- **React 18.2** + Vite 7.3.1 (build tool) + React Router v6.22.3
- **Tailwind CSS 3.3.3** (dark-first design system with neutral palette)
- **Radix UI** primitives (Dialog, Dropdown, Select, Tabs, Toast, Tooltip, etc.)
- **Recharts 3.7** for admin analytics charts
- **Framer Motion** for user-shell page transitions
- **Lucide React** + React Icons for iconography
- **Axios 1.12** with automatic token refresh interceptor
- **Sonner** for toast notifications

## Project Structure

```
├── backend/
│   ├── core/           # App factory, config, models (20 models), DB, auth
│   ├── api/routes/     # 10 blueprints (~38 endpoints): admin, analytics, auth,
│   │                   #   domains, generation, health, ideas, novelty, platform, public, retrieval
│   ├── ai/             # LLM client (Ollama/OpenAI), prompts, bias registry
│   ├── generation/     # Pipeline (generator, constraints, job_queue, schemas)
│   ├── novelty/        # Multi-engine novelty analysis (engines/, scoring/, utils/)
│   ├── retrieval/      # arXiv + GitHub live retrieval, source reputation, caching
│   ├── semantic/       # Embedding (cached), filtering, ranking
│   ├── scripts/        # DB migrations, seed data, optimization
│   └── utils/          # Auth helpers, serializers, health checks
├── frontend/
│   └── src/
│       ├── features/   # Feature-based architecture:
│       │   ├── admin/      # AdminShell, ReviewQueue, Analytics, AbuseEvents, IdeaDetail
│       │   ├── auth/       # LoginPage, RegisterPage
│       │   ├── dashboard/  # UserDashboard
│       │   ├── explore/    # ExplorePage (public browsing)
│       │   ├── generate/   # GeneratePage (idea creation)
│       │   ├── idea/       # IdeaDetail (public idea view)
│       │   ├── landing/    # LandingPage
│       │   ├── novelty/    # NoveltyPage, MyIdeasPage, SourcesList
│       │   ├── shared/     # PublicShell, Header
│       │   └── user/       # UserShell, UserNav
│       ├── components/ # ProtectedRoute, AdminProtectedRoute, ErrorBoundary, ui/ primitives
│       ├── context/    # AuthContext (JWT + refresh)
│       ├── hooks/      # useDebounce, useGeneration, useIdeas, useJob
│       ├── lib/        # API client, formatScore, motion presets, phaseLabels, utils
│       └── config/     # Runtime config (VITE_API_URL)
├── tests/
│   ├── backend/        # Backend unit tests (15 test files)
│   ├── integration/    # Integration tests (15 test files)
│   ├── scripts/        # Script-based component tests (10 test files)
│   └── unit/           # Additional unit tests
└── docs/               # Architecture docs, diagrams, design rules
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
npm run dev                    # Vite dev server on http://localhost:3000
npm run build                  # Production build to build/
npm run preview                # Preview production build
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Neon PostgreSQL connection string |
| `SECRET_KEY` | `dev-secret-key` | Flask secret key |
| `JWT_SECRET` | `dev-jwt-secret` | JWT signing secret |
| `JWT_EXP_SECONDS` | `3600` | Access token expiry (seconds) |
| `JWT_REFRESH_EXP_SECONDS` | `604800` | Refresh token expiry (7 days) |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `LLM_MODEL_NAME` | `qwen2.5:7b` | Model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | — | Required if provider is `openai` |
| `LLM_TIMEOUT_SECONDS` | `60` | LLM request timeout |
| `LLM_MAX_RETRIES` | `4` | LLM retry attempts |
| `LLM_STARTUP_HARD_FAIL` | `true` | Fail app startup if LLM unavailable |
| `LLM_FALLBACK_ENABLED` | `false` | Enable automatic LLM fallback |
| `LLM_FALLBACK_PROVIDER` | `openai` | Fallback LLM provider |
| `DEMO_MODE` | `false` | Enable 1-pass demo pipeline |
| `HYBRID_MODE` | `true` | Enable 2-pass hybrid pipeline |
| `MIN_EVIDENCE_REQUIRED` | `3` | Min sources before LLM generation |
| `MIN_NOVELTY_SCORE` | `25` | Min novelty to pass evidence gate |
| `MAX_SOURCES_FOR_LLM` | `8` | Max sources sent to LLM prompt |
| `MAX_GENERATION_REQUESTS_PER_MIN` | `6` | Rate limit for generation |
| `ABUSE_WINDOW_SECONDS` | `60` | Abuse detection window |
| `AUTO_BLOCK_AFTER_INFRACTIONS` | `5` | Auto-block threshold |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `DEFAULT_AI_PIPELINE_VERSION` | `v2` | Active pipeline version |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-Transformers model |
| `EMBEDDING_DIM` | `384` | Embedding dimensionality |

## API Overview (~38 endpoints across 10 blueprints)

### Health
- `GET /api/health` — System health check

### Public
- `GET /api/public/ideas` — Browse public ideas (cached 5min, supports `domain`, `q`, pagination)
- `GET /api/public/ideas/<id>` — Public idea detail with view tracking
- `GET /api/public/top-ideas` — Top 10 ideas by quality + views
- `GET /api/public/top-domains` — Top 10 domains by idea count
- `GET /api/public/stats` — Platform statistics (total ideas, domains, users)

### Domains
- `GET /api/domains` — List all domains with categories

### Auth
- `POST /api/register` — Register (rate-limited: 5/min)
- `POST /api/login` — Login (returns access + refresh tokens)
- `POST /api/refresh` — Refresh access token
- `POST /api/logout` — Logout (adds JTI to blocklist)

### User (JWT required)
- `POST /api/ideas/generate` — Async idea generation (returns `job_id`, 202)
- `GET /api/ideas/generate/<job_id>` — Poll generation status
- `GET /api/ideas/generate/<job_id>/stream` — SSE real-time progress stream
- `GET /api/ideas/mine` — User's own ideas (paginated)
- `GET /api/ideas/<id>` — Authenticated idea detail + view tracking
- `POST /api/ideas/<id>/feedback` — Submit structured feedback (6 types)
- `POST /api/ideas/<id>/review` — Submit/upsert star rating (1–5)
- `GET /api/ideas/<id>/reviews` — List reviews for an idea
- `GET /api/ideas/<id>/feedbacks` — List feedbacks grouped by type
- `GET /api/ideas/<id>/novelty-explanation` — Detailed novelty score explanation (owner only)

### Retrieval & Novelty (JWT required)
- `POST /api/retrieval/sources` — Retrieve sources for a query + domain
- `POST /api/novelty/analyze` — Run novelty analysis on a description

### Admin (JWT + admin role)
- `GET /api/admin/ideas/quality-review` — Review queue (flagged/low-evidence ideas)
- `GET /api/admin/ideas/<id>` — Full admin idea detail
- `POST /api/admin/ideas/<id>/verdict` — Submit verdict (validated/downgraded/rejected)
- `POST /api/admin/ideas/<id>/human-verified` — Toggle human-verified flag
- `POST /api/admin/ideas/<id>/sources/<sid>/hallucinated` — Flag/unflag source as hallucinated
- `GET /api/admin/ideas/<id>/generation-trace` — View generation trace (Phase 0–5)
- `GET /api/admin/ideas/<id>/bias-breakdown` — Bias/penalty breakdown
- `POST /api/admin/ideas/<id>/rescore` — Re-run novelty scoring
- `GET /api/admin/abuse-events` — List abuse events (paginated)

### Analytics (JWT + admin role)
- `GET /api/analytics/admin/kpis` — Admin KPI dashboard
- `GET /api/admin/domains` — Domain statistics
- `GET /api/admin/trends` — 30-day idea creation trends
- `GET /api/admin/distributions` — Novelty & quality score histograms
- `GET /api/admin/user-domains` — User domain preference counts
- `GET /api/analytics/admin/bias-transparency` — Bias impact analysis

### Legacy / Platform
- `GET /api/ai/pipeline-version` — Current AI pipeline version
- `POST /api/check_novelty` — Legacy novelty alias
- `POST /api/generate-idea` — Deprecated (returns 410)
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
