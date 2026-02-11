# InnovateSphere - Comprehensive Project Analysis

## Executive Summary

InnovateSphere is an AI-powered full-stack web application for generating and exploring innovative project ideas. It combines semantic search, machine learning, and human-in-the-loop (HITL) validation to help users discover unique project opportunities across various technology domains.

---

## 1. TECH STACK & DEPENDENCIES

### 1.1 Frontend Stack

**Framework & Libraries:**
- React 18+ (UI framework)
- React Router DOM v7.13.0 (client-side routing)
- Recharts v3.7.0 (data visualization & analytics)

**Styling & CSS:**
- Tailwind CSS v3.3.3 (utility-first CSS framework)
- PostCSS v8.4.29 (CSS processing)
- Autoprefixer v10.4.15 (vendor prefixing)

**HTTP & API:**
- Axios (implied integration, API client for backend communication)

**Development:**
- Node.js (runtime)
- npm (package manager)

### 1.2 Backend Stack

**Framework & Runtime:**
- Python 3.9+ (primary language)
- Flask v2.3.3 (web framework)
- Gunicorn (ASGI/WSGI server for production)

**Database & ORM:**
- PostgreSQL 13+ (primary database, hosted on Neon for production)
- SQLAlchemy v3.0.5 (ORM)
- psycopg2-binary v2.9.7 (PostgreSQL adapter)
- pgvector v0.3.4 (vector similarity search support)

**Authentication & Security:**
- Flask-JWT-Extended v4.5.0 (JWT token management)
- bcrypt v4.0.1 (password hashing)
- PyJWT v2.8.0 (JWT encoding/decoding)

**API & Middleware:**
- Flask-CORS v4.0.0 (CORS support)
- Flask-Caching v2.1.0+ (response caching)
- Flask-Limiter v4.1.0+ (rate limiting)

**Machine Learning & NLP:**
- Sentence Transformers v2.2.2 (embedding models)
- Transformers v4.33.3 (NLP pipeline)
- HuggingFace Hub v0.20.3 (model registry access)
- Torch v2.2.1 (deep learning framework)
- Accelerate v0.27.2 (distributed training)

**LLM Integration:**
- LangChain v0.1.16 (LLM orchestration)
- LangChain Community v0.0.32 (providers & tools)
- Ollama integration (local LLM support)
- OpenAI API support

**External API Integration:**
- arxiv v1.4.4 (academic paper retrieval)
- requests v2.28.0+ (HTTP client)

**Configuration & Environment:**
- python-dotenv v1.0.0 (.env file support)
- pydantic v2.0.0+ (data validation)
- numpy v1.26.4 (numerical computing)

### 1.3 Infrastructure

**Containerization:**
- Docker (application containerization)
- Docker Compose v3.8 (multi-container orchestration)

**Database:**
- PostgreSQL 13+ with pgvector extension
- Neon (platform, PostgreSQL hosting)

**LocalStorage:**
- Docker volumes (persistent data)

---

## 2. HIGH-LEVEL ARCHITECTURE

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React Frontend (Components, Pages, Features)         │  │
│  │  - Landing/Public Pages                              │  │
│  │  - User Dashboard & Profile                          │  │
│  │  - Idea Generation & Exploration                     │  │
│  │  - Admin Review Dashboard                            │  │
│  │  - Novelty Analysis Viewer                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    (HTTP/REST API)
                            │
┌─────────────────────────────────────────────────────────────┐
│                   API GATEWAY LAYER                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Flask Application                                   │  │
│  │  - CORS Handler                                      │  │
│  │  - Rate Limiter                                      │  │
│  │  - JWT Authentication                               │  │
│  │  - Request/Response Logging                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌──────┴─────┐      ┌──────┴─────┐       ┌──────┴──────┐
    │             │      │             │       │              │
┌───▼──────┐ ┌──▼───┐ ┌──▼────┐ ┌────▼──┐ ┌──▼──────┐ ┌────▼──┐
│ Retrieval│ │ Gen. │ │Novelty│ │Admin  │ │Analytics│ │Public │
│ Routes   │ │Routes│ │Routes │ │Routes │ │ Routes   │ │Routes │
└─────┬────┘ └──┬───┘ └───┬───┘ └────┬──┘ └────┬─────┘ └────┬──┘
      │         │         │          │         │            │
┌─────▼─────────▼─────────▼──────────▼─────────▼────────────▼────┐
│                    SERVICE LOGIC LAYER                         │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │ AI Services  │  │Novelty      │  │Extraction        │     │
│  │ - Generator  │  │Analysis     │  │ - Source Parser  │     │
│  │ - LLM Client │  │ - Analyzer  │  │ - Domain Mapper  │     │
│  │              │  │ - Scoring   │  │                  │     │
│  └──────────────┘  └─────────────┘  └──────────────────┘     │
│                                                               │
│  ┌──────────────────┐  ┌─────────────┐  ┌────────────────┐   │
│  │Retrieval Engine  │  │ Semantic    │  │Cache Layer     │   │
│  │ - arXiv Client   │  │ - Embedder  │  │ - Embeddings   │   │
│  │ - GitHub Client  │  │ - Filter    │  │ - State        │   │
│  │ - Orchestrator   │  │ - Ranker    │  │                │   │
│  └──────────────────┘  └─────────────┘  └────────────────┘   │
└──────────┬─────────────────────────────────────────────────────┘
           │
┌──────────▼────────────────────────────────────┐
│         PERSISTENCE LAYER                     │
│  ┌──────────────────────────────────────────┐ │
│  │  PostgreSQL + pgvector Database          │ │
│  │  - Relational Data (Ideas, Users, etc)   │ │
│  │  - Vector Storage (Embeddings)           │ │
│  │  - Metadata & Relationships              │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
           │
┌──────────▼────────────────────────────────────┐
│    EXTERNAL SERVICES                          │
│  - arXiv API (academic papers)                │
│  - GitHub API (open source repos)             │
│  - Ollama / OpenAI (LLM backends)             │
│  - HuggingFace (embedding models)             │
└───────────────────────────────────────────────┘
```

---

## 3. USER FLOW DIAGRAMS

### 3.1 User Journey - Idea Exploration (Anonymous)

```
User Starts
    │
    ├─ Visit Landing Page ──────► View Public Overview
    │       │                         │
    │       └─ Browse Explore ─────► Search/Filter Ideas
    │              │
    │              └─ No Auth ──────► Limited View (No Sources/Reviews)
    │                    │
    │                    └─ See CTA: "Sign Up for Full Access"
    │
    └─ Click Idea ──────────────► View Partial Details
           │                      - Title, Title, Tech Stack
           │                      - Requires_login flag
           │
           └─ Request Sign Up

Legend: ──► (action) │ (flow) └─ (branch)
```

### 3.2 User Journey - Idea Generation (Authenticated)

```
Authenticated User
    │
    ├─ Access /user/generate
    │       │
    │       ├─ Input Query & Domain Selection
    │       │       │
    │       │       └─ Submit Generation Request
    │               │
    │               ▼
    │       ┌─────────────────────┐
    │       │ GENERATION PIPELINE │
    │       └──────────┬──────────┘
    │                  │
    │   ┌──────────────┼─────────────────┐
    │   │              │                  │
    │   ▼              ▼                  ▼
    │  Phase 0:    Phase 1:          Phase 2:
    │  Input       Retrieval         Landscape
    │  Prep        Sources           Analysis
    │  │ Query     │ ArXiv           │ Gaps/Trends
    │  │ Domain    │ GitHub          │ Saturation
    │  │ Feasible? │ Ranking         │
    │   │   (min 3 sources)
    │   │
    │   ▼
    │  Evidence Gate: Pass? ──No──► Error: Insufficient Evidence
    │  │
    │  │Yes
    │  │
    │   ┌───────────────┬───────────────┐
    │   │               │               │
    │   ▼               ▼               ▼
    │  Phase 2:    Phase 3:         Phase 4:
    │  Landscape   Constraint       Evidence
    │  Analysis    Synthesis        Validation
    │  │ Problem   │ HITL Rules     │ Source Fact
    │  │ Related   │ Bias Profiles  │ Check
    │  │ Tech      │ Admin Verdic   │
    │  │           │                │
    │   └───────────┬────────────────┘
    │               │
    │               ▼
    │           Novelty Analysis
    │           │ Similarity Score
    │           │ Specificity
    │           │ Temporal Signals
    │
    │           Quality Score Calc
    │           │ Feedback Impact
    │           │ Evidence Bonus
    │           │ Review Rating
    │
    │               │
    │               ▼
    │           Idea Generated
    │           │ Stored in DB
    │           │ Verified
    │           │ Public/Draft?
    │
    └─ User Receives Generated Idea
           │
           ├─ View Full Details (Sources, Analysis)
           ├─ Request Idea (Track Demand)
           ├─ Leave Review (1-5 Rating)
           └─ Share/Bookmark
```

### 3.3 User Journey - Admin Review Queue

```
Admin User
    │
    ├─ Access /admin/review
    │       │
    │       ├─ View Review Queue
    │       │   │ Pending Ideas
    │       │   │ Flagged Ideas
    │       │   │ User Feedback
    │       │
    │       └─ Review Individual Idea
    │           │
    │           ├─ View Full Trace
    │           │   │ Generation phases
    │           │   │ Constraints applied
    │           │   │ Bias penalties
    │           │
    │           ├─ See User Feedback
    │           │   │ Quality ratings
    │           │   │ Factual errors
    │           │   │ Hallucinations
    │           │
    │           └─ Make Verdict
    │               │
    │               ├─ ✓ Validated ──────► Boost Quality Score
    │               ├─ ▼ Downgraded ──────► Reduce Quality Score
    │               └─ ✗ Rejected ────────► Set Low Multiplier
    │                       │
    │                       └─ Record Reason
    │                           Update Similar Ideas
    │
    └─ View Analytics
        │ Quality Trends
        │ Novelty Clustering
        │ Domain Performance
        │ User Engagement
```

---

## 4. SYSTEM ARCHITECTURE

### 4.1 Core Modules & Components

#### **Backend Core (backend/core/)**

**app.py - Flask Application Factory**
- Creates Flask app with configuration
- Initializes extensions: SQLAlchemy, JWT, Cache, Limiter
- Handles CORS, request logging, error handling
- Database connection pooling (Neon-safe config)

**models.py - Database Schema**
- `ProjectIdea` - Core idea entity with quality/novelty scores
- `Domain` / `DomainCategory` - Taxonomy
- `User` - User profiles with roles
- `IdeaSource` - Retrieved sources (arXiv, GitHub)
- `IdeaReview` / `IdeaFeedback` - User engagement
- `AdminVerdict` - HITL verdicts with impacts
- `GenerationTrace` - Audit trail (4 phases + constraints)
- `IdeaView` / `ViewEvent` - Analytics

**db.py - Database Configuration**
- SQLAlchemy session management
- Migration support

**auth.py - Authentication Core**
- JWT token validation
- User context extraction

**config.py - Configuration Management**
- Environment variables
- LLM provider selection (Ollama/OpenAI)
- Model names & endpoints
- Rate limits & timeouts
- Evidence thresholds

#### **API Routes (backend/api/routes/)**

| Module | Responsibility |
|--------|-----------------|
| `generation.py` | POST /api/ideas/generate - Multi-pass generation pipeline |
| `retrieval.py` | POST /api/retrieval/sources - Source discovery & ranking |
| `novelty.py` | GET /api/novelty/analyze - Novelty scoring & explanation |
| `ideas.py` | GET/POST /api/ideas/* - Idea CRUD, reviews, feedback |
| `admin.py` | GET/POST /api/admin/* - Admin review, verdicts, analytics |
| `public.py` | GET /api/public/ideas - Anonymous browsing |
| `domains.py` | GET /api/domains - Domain taxonomy |
| `health.py` | GET /api/health - System health check |

#### **AI Module (backend/ai/)**

**llm_client.py - Provider-Agnostic LLM Interface**
- `generate_json()` - JSON extraction from LLM output
- Supports Ollama (local) and OpenAI
- Automatic retries & fallback mock mode
- Provider routing in config

**prompts.py - Multi-Pass Prompt Templates**
- PASS1_SYSTEM / PROMPT - Landscape analysis
- PASS2_SYSTEM / PROMPT - Problem formulation
- PASS3_SYSTEM / PROMPT - Constraint-guided synthesis
- PASS4_SYSTEM / PROMPT - Evidence validation

**registry.py - Model & Pipeline Registry**
- Active AI pipeline version tracking
- Bias profile selection
- Prompt version management

#### **Generation Module (backend/generation/)**

**generator.py - Multi-Pass Generator**
```
Input: User query, domain, constraints
├─ Phase 0: Input conditioning (feasibility estimate)
├─ Phase 1: Retrieval (arXiv + GitHub orchestration)
├─ Phase 2: Landscape analysis (LLM pass 1)
├─ Phase 3: Constraint synthesis (LLM pass 2-3, bias penalties)
├─ Phase 4: Evidence validation (LLM pass 4)
└─ Output: Scored ProjectIdea with sources
```

**constraints.py - HITL Constraint Engine**
- Build constraints from bias profiles
- Track admin verdicts
- Apply penalties to similar ideas
- Reject patterns detection

**schemas.py - Validation & Serialization**
- `validate_generated_idea()` - Output schema validation

#### **Retrieval Module (backend/retrieval/)**

**orchestrator.py - Multi-Source Retrieval**
- Orchestrates arXiv + GitHub search
- Deduplication & ranking
- Semantic filtering stage
- Tier classification

**arxiv_client.py - Academic Paper Search**
- Query building with domain mapping
- XML parsing
- Metadata extraction (published_date)

**github_client.py - Repository Search**
- Query construction with truncation
- GitHub API v3 integration
- Star-based ranking
- Fallback retry logic

**source_reputation.py - Admin Feedback Aggregation**
- Tracks validation/rejection counts
- Computes source reputation scores

**cached_retrieval.py - Retrieval Caching**
- In-memory source cache
- Reduces API calls

#### **Semantic Module (backend/semantic/)**

**cached_embedder.py - Cached Embeddings**
- SentenceTransformer wrapper
- LRU cache (5000 embeddings)
- Thread-safe for request handling

**embedder.py - Embedding Generation**
- Model loading (sentence-transformers)
- Text normalization

**filter.py - Semantic Similarity Filter**
- Cosine similarity computation
- Threshold-based filtering

**ranker.py - Source Ranking**
- Multi-factor ranking (recency, stars, relevance)

#### **Novelty Module (backend/novelty/)**

**analyzer.py - Main Novelty Scorer**
```
novelty_score = blend(
  base_score(signals),
  signal_analysis[similarity, specificity, temporal, saturation],
  bonuses[domain_weighting],
  penalties[hitl_feedback, saturation]
)
```

**scoring/**
- `base.py` - Base score from signals (0-100)
- `bonuses.py` - Domain & context bonuses
- `penalties.py` - Saturation & admin penalties
- `blending.py` - Signal fusion

**utils/**
- `signals.py` - Similarity, specificity, temporal signals
- `calibration.py` - HITL calibration
- `observability.py` - Telemetry & tracing

**normalization.py** - Map score to level (Very Low → Very High)

**explain.py** - Generate human-readable explanations

**service.py** - High-level novelty API

### 4.2 Frontend Architecture

```
frontend/src/
├── Context/
│   └── AuthContext.jsx ────────────► Global auth state
│
├── Features/
│   ├── auth/ ──────┐
│   │   ├── pages/  │  └─► LoginPage, RegisterPage
│   │   └── context │
│   │
│   ├── landing/ ───► LandingPage (public overview)
│   │
│   ├── explore/ ───► ExplorePage (browse public ideas)
│   │
│   ├── generate/ ──► GeneratePage (idea generation)
│   │   ├── forms/ (InputForm, ParameterSelector)
│   │   └── hooks/ (useGeneration)
│   │
│   ├── idea/ ──────► IdeaDetail (view, review, feedback)
│   │   ├── components/
│   │   └── hooks/
│   │
│   ├── dashboard/ ─► UserDashboard (user stats)
│   │
│   ├── novelty/ ───► NoveltyPage (novelty explanation)
│   │   ├── components/ (NoveltyBreakdown, etc)
│   │   └── hooks/
│   │
│   ├── admin/ ─────► AdminReviewQueue, AdminAnalytics
│   │   ├── pages/
│   │   ├── components/
│   │   └── hooks/
│   │
│   └── shared/ ────► Common components
│       ├── Navbar, Footer
│       ├── Charts, Cards
│       └── Modals
│
├── Components/
│   ├── ProtectedRoute.jsx ──────────► User auth guard
│   └── AdminProtectedRoute.jsx ─────► Admin auth guard
│
├── Lib/ ────────────────────────────► Utilities
│   ├── api.js (Axios instance)
│   ├── auth.js (JWT handling)
│   └── helpers.js
│
└── Hooks/
    ├── useAuth.js
    ├── useFetch.js
    └── useGeneration.js
```

**Key Frontend Pages:**

| Page | Route | Auth | Purpose |
|------|-------|------|---------|
| Landing | / | None | Overview, signup CTA |
| Explore | /explore | None | Browse public ideas |
| Login | /login | None | Authentication |
| Register | /register | None | User signup |
| IdeaDetail | /idea/:id | Optional | View full idea, review |
| UserDashboard | /user/dashboard | Required | User's ideas & stats |
| GeneratePage | /user/generate | Required | Create new idea |
| NoveltyPage | /user/novelty | Required | Analyze novelty |
| AdminReviewQueue | /admin/review | Admin | Review pending ideas |
| AdminAnalytics | /admin/analytics | Admin | Platform analytics |

---

## 5. DATABASE DESIGN

### 5.1 Core Entities & Relationships

```
┌──────────────┐
│ Users        │
├──────────────┤
│ id (PK)      │
│ email        │ (unique)
│ password_hash│
│ role         │ ('user', 'admin')
│ created_at   │
└──┬───────────┘
   │ 1:N
   │
   ├───────────────────────┬──────────────┬──────────────┐
   │                       │              │              │
   │1:N                  1:N            1:N            1:N
   ▼                       ▼              ▼              ▼
┌──────────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ IdeaRequest      │ │IdeaReview    │ │IdeaFeedback │ │GenerationTrace
├──────────────────┤ ├──────────────┤ ├─────────────┤ ├──────────────┤
│ id (PK)          │ │ id (PK)      │ │ id (PK)     │ │ id (PK)      │
│ user_id (FK)     │ │ user_id (FK) │ │ user_id (FK)│ │ user_id (FK) │
│ idea_id (FK)  ──┐│ │ idea_id (FK)─┐│ │ idea_id (FK)│ │ idea_id (FK) │
│ created_at       │ │ rating    1-5 │ │ feedback_ty │ │ query        │
│ request_context  │ │ comment   text│ │ comment     │ │ phase_*_out  │
└──────────────────┘ │ created_at    │ │ created_at  │ │ constraints  │
                     └──────────────┘ └─────────────┘ │ timings      │
                                                      └──────────────┘
                                                             │
                                                             │ 1:N
                                                             ▼
                                                      ┌──────────────┐
                                                      │ ProjectIdea  │
                                                      │ (PRIMARY)    │
                                                      └──────────────┘

┌──────────────────┐            ┌──────────────────┐
│    ProjectIdea   │            │   Domain         │
├──────────────────┤            ├──────────────────┤
│ id (PK)          │            │ id (PK)          │
│ title            │            │ name (unique)    │
│ problem_statement│            │                  │
│ tech_stack       │            └──────┬───────────┘
│ domain_id (FK)──┐│                   │
│ ai_pipeline_vers│                   │ 1:N
│ is_ai_generated  │                   │
│ is_public        │                   ▼
│ is_validated     │            ┌──────────────────┐
│ created_at       │            │ DomainCategory   │
│ view_count       │            ├──────────────────┤
│ quality_score    │            │ id (PK)          │
│ novelty_score    │            │ name             │
│ novelty_context  │            │ domain_id (FK)   │
│ idea_embedding   │            └──────────────────┘
└────────┬─────────┘
         │
         │ 1:N
         ▼
    ┌──────────────┐
    │ IdeaSource   │
    ├──────────────┤
    │ id (PK)      │
    │ idea_id (FK) │
    │ source_type  │ (arxiv/github)
    │ title        │
    │ url          │ (unique)
    │ summary      │
    │ published_dt │
    └──────────────┘
```

### 5.2 Audit & Control Tables

```
┌──────────────────────┐
│ AdminVerdict         │
├──────────────────────┤
│ id (PK)              │
│ idea_id (FK, unique) │──────► Links to ProjectIdea
│ admin_id (FK)        │──────► Links to User (admin)
│ verdict              │ (validated/downgraded/rejected)
│ reason (text)        │
│ created_at           │
└──────────────────────┘

┌──────────────────────┐
│ BiasProfile          │
├──────────────────────┤
│ id (PK)              │
│ name (unique)        │
│ version              │
│ rules (JSON)         │
│ is_active            │
│ created_at           │
└──────────────────────┘

┌──────────────────────┐
│ PromptVersion        │
├──────────────────────┤
│ id (PK)              │
│ name                 │
│ prompts_json (JSON)  │
│ is_active            │
│ created_at           │
└──────────────────────┘

┌──────────────────────┐
│ AiPipelineVersion    │
├──────────────────────┤
│ id (PK)              │
│ version (unique)     │
│ is_active            │
│ created_at           │
└──────────────────────┘
```

### 5.3 Analytics Tables

```
┌──────────────────────┐
│ IdeaView             │
├──────────────────────┤
│ id (PK)              │
│ idea_id (FK)         │
│ user_id (FK, nullable)
│ viewed_at            │
│ (indexed: idea, user, date)
└──────────────────────┘

┌──────────────────────┐
│ ViewEvent            │
├──────────────────────┤
│ id (PK)              │
│ idea_id (FK)         │
│ user_id (FK, nullable)
│ event_type           │ (view/click/share/rate)
│ duration_ms          │
│ session_id           │
│ created_at           │
└──────────────────────┘
```

---

## 6. DATA FLOW SEQUENCES

### 6.1 Idea Generation Flow

```
Client                 Backend API          Service Layer        Database & External
  │                        │                    │                     │
  │ POST /api/generate     │                    │                     │
  │ {subject, domain}      │                    │                    │
  ├──────────────────────► │                    │                     │
  │                        │ Validate & Parse   │                     │
  │                        │                    │                     │
  │                        │ generate_idea() ──►│                     │
  │                        │                    │ Phase 0: Estimate  │
  │                        │                    │ Feasibility        │
  │                        │                    │                    │
  │                        │                    │ Phase 1: Retrieve ─────► arXiv/GitHub
  │                        │                    │ orchestrator()     ◄─────────────────
  │                        │                    │
  │                        │                    │ Check: Min Sources?
  │                        │ ◄─ ERROR (if fail)
  │                        │
  │                        │                    │ Phase 2: LLM Pass 1
  │                        │                    │ analyze_landscape()
  │                        │
  │                        │                    │ Phase 3: LLM Pass 2-3 ─────► HF Models
  │                        │                    │ constrained_synthesis()
  │                        │                    │ apply_bias_penalties()
  │                        │
  │                        │                    │ Phase 4: LLM Pass 4
  │                        │                    │ validate_evidence()
  │                        │
  │                        │                    │ Analyze Novelty ──────────► Semantic
  │                        │                    │ compute_novelty()   Models/DB
  │                        │                    │
  │                        │                    │ Compute Quality ───────────► DB
  │                        │                    │ compute_quality()   Queries
  │                        │                    │
  │                        │                    │ Save Traces ──────────────► DB Insert
  │                        │                    │ save_generation_trace()    (GenerationTrace)
  │                        │
  │◄────── {idea_id}  ─────┤
  │ generated_id           │
```

### 6.2 Novelty Scoring Sequence

```
User Query          Semantic              Retrieval           Scoring Engine
    │               Module                Module              │
    │                │                     │                  │
    ├─ description  ─┼─► embed_texts() ───────────────────────┤
    │                │                     │                  │
    │                │                     │                  ├─► retrieve_sources()
    │                │◄─ embeddings ───────┼──────────────────┤
    │                │                     │                  │
    │                │                     │                  ├─► compute_similarity_stats()
    │                │◄─ similarity vector─┼──────────────────┤
    │                │                     │                  │
    │                │                     │                  ├─► compute_specificity()
    │                │                     │                  │
    │                │                     │                  ├─► compute_temporal()
    │                │                     │                  │
    │                │                     │                  ├─► blend(signals)
    │                │                     │                  │
    │                │                     │                  ├─► apply_penalties()
    │                │                     │                  │
    │◄─ novelty_score + explanation ──────────────────────────┤
```

### 6.3 Admin Review & Verdict Flow

```
Admin Portal         API Layer           Service Layer        Database
    │                   │                    │                   │
    │ GET /admin/review │                    │                   │
    ├──────────────────►│                    │                   │
    │                   │ get_pending()     │                   │
    │                   │                   │ Query ideas ───────────────► IdeaQuery
    │                   │                   │                   ◄─────────
    │◄─ pending_ideas ──┤                   │
    │                   │                   │
    │ Click idea_id     │                   │
    ├──────────────────►│ GET /admin/idea/id
    │                   │                   │ get_full_context()
    │                   │                   │ - GenerationTrace
    │                   │                   │ - AdminVerdict
    │                   │                   │ - Feedbacks
    │                   │                   │ - Sources
    │◄─ full_context ───┤                   │
    │                   │                   │
    │ POST /admin/verdict│ {verdict}        │
    ├──────────────────►│                   │
    │                   │ record_verdict()──► Insert AdminVerdict
    │                   │                   ├─ Update related ideas
    │                   │                   └─ Cascade penalties
    │◄─ success ────────┤                   │
    │                   │                   │
    │                   │                   │ Update novelty cache
    │                   │                   ├─ Recompute quality
    │                   │                   └─ Log trace
```

---

## 7. API ENDPOINTS

### 7.1 Public Endpoints (No Auth Required)

```
GET  /api/public/ideas
     Query: q (search), domain_id (filter), limit, offset
     Response: [{id, title, domain_name, requires_login, ...}]

GET  /api/ideas/<id>
     Response: {id, title, ..., requires_login: true, signup_message}
     (Limited fields for anonymous)

GET  /api/domains
     Response: [{id, name, categories: []}]

GET  /api/health
     Response: {status: 'healthy', timestamp}
```

### 7.2 User Endpoints (JWT Required)

```
POST /api/ideas/generate
     Body: {subject, domain_id, parameters?}
     Response: {idea_id, novelty_score, quality_score, ...}

POST /api/ideas/<id>/request
     Body: {context?}
     Response: {request_id, tracked_at}

POST /api/ideas/<id>/review
     Body: {rating: 1-5, comment?}
     Response: {review_id, ...}

POST /api/ideas/<id>/feedback
     Body: {feedback_type, comment}
     Feedback types: high_quality, factual_error, hallucinated_source, weak_novelty, etc.
     Response: {feedback_id, ...}

GET  /api/ideas/<id>/novelty-explanation
     Response: {novelty_score, explanation, signals_breakdown, penalties, sources}

GET  /api/user/dashboard
     Response: {stats: {ideas_generated, avg_novelty, ...}, recent_ideas: []}

GET  /api/retrieval/sources
     Body: {query, domain_id, similarity_threshold}
     Response: {sources: [{title, url, source_type, metadata}], retrieved_at}
```

### 7.3 Admin Endpoints (Admin JWT + Verification)

```
GET  /api/admin/review
     Query: status (pending/flagged), limit, offset
     Response: [{idea_id, title, feedback_count, user_feedback, ...}]

GET  /api/admin/idea/<id>
     Response: {idea: {...full details...}, trace: {...}, feedbacks: [...], verdict: {...}}

POST /api/admin/idea/<id>/verdict
     Body: {verdict: 'validated'|'downgraded'|'rejected', reason}
     Response: {verdict_id, cascaded_updates: N}

GET  /api/admin/analytics
     Query: domain_id?, start_date?, end_date?
     Response: {quality_trends, novelty_distribution, user_engagement, domain_performance}

POST /api/admin/bias-profile
     Body: {name, version, rules}
     Response: {profile_id, ...}

GET  /api/admin/prompt-versions
     Response: [{id, name, version, is_active}]
```

---

## 8. TECHNICAL WORKFLOW - IDEA GENERATION

### 8.1 Multi-Pass Generation Pipeline

**Phase 0: Input Conditioning**
```
Input: query, domain_id, user_preferences
├─ Sanitize & validate query
├─ Map domain_id to domain name
├─ Estimate feasibility (heuristic based on query complexity)
├─ Check min evidence requirements
└─ Output: conditioned_input for Phase 1
```

**Phase 1: Retrieval**
```
Input: conditioned query, domain
├─ parallel_search:
│   ├─ search_arxiv(query, domain) ──► academic papers
│   └─ search_github(query, domain) ──► code repositories
├─ Deduplicate by URL
├─ Rank by relevance (recency for papers, stars for repos)
├─ Apply reputation scoring (admin feedback history)
├─ Filter: keep top 20 unique sources
└─ Output: ranked sources list
```

**Phase 2: Landscape Analysis (LLM Pass 1)**
```
Input: query, domain, sources
Prompt: Analyze the research landscape...
├─ Identify existing solutions
├─ Detect knowledge gaps
├─ Spot emerging trends
├─ Assess market saturation
└─ Output: landscape narrative
```

**Phase 3: Constraint-Guided Synthesis (LLM Pass 2-3)**
```
Input: query, domain, landscape, sources
├─ Load active bias profile
├─ Load constraint from admin verdicts  (similar ideas)
├─ Generate problem statement + tech stack (with constraints)
├─ Check rejected patterns
├─ Apply source penalties (downweight hallucinated/rejected sources)
├─ Apply domain saturation penalties
└─ Output: constrained_idea (problem + tech)
```

**Phase 4: Evidence Validation (LLM Pass 4)**
```
Input: idea, sources, phase outputs
├─ Map problem statement to evidence
├─ Assign sources to roles:
│   ├─ background (foundational knowledge)
│   ├─ related_work (adjacent solutions)
│   └─ contribution (enabling tech)
├─ Validate factual claims against sources
├─ Cross-check tech stack feasibility
└─ Output: validated_idea + evidence_mapping
```

### 8.2 Scoring Pipeline

**Novelty Scoring Computation**
```
Input: description, domain, retrieved_sources

1. Similarity Analysis
   ├─ embed_text(description)
   ├─ embed_text(sources[*].summary)
   ├─ compute cosine_similarity vector
   └─ stats: mean, variance, min, max

2. Specificity Signal
   ├─ Count unique keywords
   ├─ Analyze query vs sources diversity
   └─ scores: 0-100

3. Temporal Signal
   ├─ Extract published dates from sources
   ├─ Compute recency score
   └─ Penalize if all sources old

4. Saturation Penalty
   ├─ Count similar ideas in domain
   ├─ Compute saturation level
   └─ Penalty: -5 to -30

5. Base Score Blend
   ├─ base = 50 + (specificity * 0.3) + (temporal * 0.2) - (saturation * 0.5)
   └─ Range: 0-100

6. Bonuses
   ├─ Domain weighting
   ├─ Trend detection bonus
   └─ Technical feasibility bonus

7. HITL Penalties
   ├─ Admin verdict cascade
   ├─ Source reputation
   ├─ Bias profile penalties
   └─ Range: -30 to +10

8. Stability Check (Moving Average)
   ├─ Compare to recent similar ideas
   ├─ Smooth extreme scores
   └─ Confidence: High/Medium/Low

Final: novelty_score (0-100), level (Very Low...Very High), confidence
```

**Quality Score Computation**
```
Input: idea, feedbacks, reviews, sources, admin_verdict

base = 50

feedback_impact = Σ(count[feedback_type] * weight)
  ├─ high_quality: +15 per occurrence (cap 3)
  ├─ factual_error: -20 per occurrence
  ├─ hallucinated_source: -25 per occurrence
  └─ (other types with specific weights)

evidence_bonus = min(len(sources) * 2, 20)

rating_bonus = (avg_rating - 3.0) * 2
  ├─ From IdeaReview.rating (1-5 scale)
  └─ Default to 3 if no reviews

verdict_multiplier = {validated: 1.2, downgraded: 0.8, rejected: 0.5}

quality_score = (base + feedback_impact + evidence_bonus + rating_bonus) * verdict_multiplier

Final: clamped to [0, 100]
```

---

## 9. AI ARCHITECTURE

### 9.1 LLM Integration

**Provider Selection**
```
Config.LLM_PROVIDER ∈ {ollama, openai}

If ollama:
  └─ POST {OLLAMA_BASE_URL}/api/generate
     ├─ model: Config.LLM_MODEL_NAME
     ├─ prompt: JSON system + user prompt
     ├─ temperature: 0.2 (consistency)
     └─ num_predict: 1200 tokens

If openai:
  └─ POST https://api.openai.com/v1/chat/completions
     ├─ model: Config.LLM_MODEL_NAME (gpt-4, gpt-3.5, etc)
     ├─ temperature: 0.2
     ├─ max_tokens: 1200
     └─ system + user messages

Fallback: Mock mode (dev testing)
```

**Prompt Engineering**
```
PASS1 (Landscape Analysis)
  System: You are an expert analyst...
  User: Query: {query}, Domain: {domain}
        Analyze research landscape...
  Output: JSON with gaps, trends, saturation

PASS2 (Problem Formulation)
  System: You are a technical architect...
  User: Generate problem statement...
  Output: JSON with problem statement, novelty analysis

PASS3 (Constraint Synthesis)
  System: Apply constraints and bias rules...
  User: Generate tech stack with constraints...
  Output: JSON with tech stack, constraint compliance

PASS4 (Evidence Validation)
  System: Map evidence to claims...
  User: Validate idea against sources...
  Output: JSON with evidence mapping, confidence
```

### 9.2 Embeddings & Semantic Search

**Model: Sentence Transformers**
```
Model: all-MiniLM-L6-v2 (or similar)
├─ Input: Text (query, source summaries)
├─ Output: 384-dim vector (normalized)
├─ Cache: LRU 5000 embeddings
└─ Similarity: cosine(v1, v2)
```

**Semantic Filtering**
```
Query embedding ──► Compute cosine similarity to all source embeddings
                   ├─ Filter: keep sim > threshold (default 0.6)
                   └─ Output: filtered sources
```

### 9.3 Vector Database Support

**pgvector Integration (PostgreSQL)**
```
Column: idea_embedding (vector type)
├─ Stores normalized embedding
├─ Supports: <-> (cosine distance), <#> (negative cosine), <=> (L2 distance)

Queries:
  SELECT * FROM project_ideas
  ORDER BY idea_embedding <-> embedding_vector
  LIMIT 10

Use Case: Find similar ideas, content-based recommendations
```

---

## 10. SECURITY & AUTHENTICATION

### 10.1 Authentication Flow

```
User Input (email, password)
    │
    ▼
POST /api/auth/register or /api/auth/login
    │
    ├─ Hash password with bcrypt
    ├─ Store in database
    ├─ Generate JWT token (HS256, secret=Config.SECRET_KEY)
    │  Payload: {user_id, role, exp: now + 24h}
    │
    └─► Return token to client

Client Stores: JWT in localStorage

Subsequent Requests:
    Header: Authorization: Bearer {jwt_token}
    │
    ▼
@jwt_required() decorator
    │
    ├─ Verify signature
    ├─ Check expiration
    ├─ Extract user_id
    └─ Inject into request context
```

### 10.2 Authorization

**Role-Based Access Control**
```
Routes:
├─ Public: /api/public/*, /api/domains, /api/health
├─ User: /api/ideas/generate, /api/ideas/*/request, /api/user/*
│        (requires @jwt_required())
│
└─ Admin: /api/admin/*
         (requires @jwt_required() + require_admin())
```

**Rate Limiting**
```
Config:
├─ Default: 100 requests/hour per IP
├─ Generation: 20 requests/hour per user (bypass for admins)
├─ Retrieval: 50 requests/hour per user
└─ Admin: 500 requests/hour (elevated limit)

Implementation: Flask-Limiter with Redis/local backend
```

---

## 11. DEPLOYMENT & INFRASTRUCTURE

### 11.1 Docker Compose Configuration

```yaml
Services:
├── db (PostgreSQL 13 + pgvector)
│  ├─ Port: 5433
│  ├─ Volume: postgres_data (persistent)
│  └─ Init: Migrate schema, seed data
│
├── backend (Flask)
│  ├─ Port: 5000
│  ├─ Env: DATABASE_URL, LLM_PROVIDER, etc
│  └─ Depends: db
│
└── frontend (React dev server)
   ├─ Port: 3000
   ├─ Env: REACT_APP_API_BASE_URL=http://localhost:5000
   └─ Depends: backend (for health)

Networks: Single isolated network (all services communicate internally)
```

### 11.2 Production Considerations

**Database (Neon)**
- Managed PostgreSQL with pgvector
- Connection pooling (Neon Pooler for Serverless)
- Automatic backups
- Point-in-time restore

**Backend Deployment**
- Gunicorn/ASGI server
- Reverse proxy: Nginx
- Environment-based config
- Health check: GET /api/health

**Frontend Deployment**
- Build: npm run build (React optimized)
- Static hosting: Vercel, Netlify, or CDN
- API proxy configuration

---

## 12. KEY FEATURES BREAKDOWN

### 12.1 Core Features

| Feature | Implementation |
|---------|-----------------|
| **Idea Generation** | Multi-pass LLM pipeline with constraint synthesis |
| **Novelty Analysis** | Semantic similarity + temporal signals + admin feedback |
| **Quality Scoring** | HITL feedback aggregation + admin verdicts |
| **Source Retrieval** | Dual search (arXiv + GitHub) with ranking & caching |
| **Admin Review** | HITL loop with verdict cascading & penalty application |
| **User Engagement** | Reviews, feedback, requests, bookmarks |
| **Analytics** | Dashboards, trends, domain performance metrics |

### 12.2 Advanced Features

| Feature | Purpose |
|---------|---------|
| **Bias Profiles** | Domain-specific constraint rules |
| **Prompt Versioning** | A/B test different generation strategies |
| **AI Pipeline Versions** | Track & switch between model versions |
| **Generation Traces** | Complete audit trail (4 phases + constraints) |
| **Source Reputation** | Aggregate admin feedback per source URL |
| **Semantic Filtering** | Optional similarity-based result refinement |
| **HITL Penalties** | Cascade admin decisions to similar ideas |

---

## 13. ERROR HANDLING & VALIDATION

### 13.1 Common Validation Checks

```python
# Idea Generation
├─ Min query length: 10 chars
├─ Valid domain_id
├─ Min sources retrieved: 3
├─ Generated idea schema compliance
└─ Source URL uniqueness

# Admin Verdict
├─ Valid verdict: {validated, downgraded, rejected}
├─ Reason non-empty
└─ Idea exists and not yet verdicted

# User Feedback
├─ Rating: 1-5 only
├─ Unique per user+idea+type
└─ Comment length: 0-1000 chars
```

### 13.2 Error Responses

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {...optional context...},
  "timestamp": "2024-02-08T12:34:56Z"
}

HTTP Status Codes:
├─ 200: Success
├─ 201: Created
├─ 400: Validation error
├─ 401: Unauthorized
├─ 403: Forbidden (insufficient permissions)
├─ 404: Not found
├─ 422: Unprocessable entity (LLM output validation failed)
├─ 429: Rate limit exceeded
└─ 500: Server error
```

---

## 14. PERFORMANCE & SCALING

### 14.1 Caching Strategy

```
Layer 1: In-Memory (Flask-Cache)
├─ API responses: 5 min TTL
├─ Domain list: 1 hour TTL
└─ Novelty scores: 30 min TTL

Layer 2: Semantic Cache (CachedEmbedder)
├─ Text embeddings: LRU 5000
├─ Reuse across requests
└─ Hash-based lookup

Layer 3: Database
├─ idea_embedding column (pgvector)
├─ Indexes on domain, created_at
└─ View-count aggregation
```

### 14.2 Database Optimization

```sql
Indexes:
├─ project_ideas: (domain_id), (created_at)
├─ idea_views: (idea_id), (user_id), (viewed_at)
├─ idea_feedbacks: (feedback_type)
├─ generation_traces: (idea_id), (user_id), (created_at)
└─ idea_sources: (idea_id)

Query Optimization:
├─ Lazy loading relationships
├─ Statement timeouts: 5 second
├─ Connection pooling: pool_pre_ping
└─ Pagination: limit + offset
```

---

## 15. MONITORING & OBSERVABILITY

### 15.1 Logging

```
Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Key Logs:
├─ Incoming requests (headers, body)
├─ API response times
├─ LLM API calls & retries
├─ Source retrieval attempts
├─ Database query timing
├─ JWT validation successes/failures
└─ Admin actions (verdicts, profile updates)
```

### 15.2 Metrics & Tracing

```
Telemetry Points:
├─ novelty.software.score (Novelty scorer)
├─ generation.phase_*.duration (Phase timings)
├─ retrieval.source_count (Sources retrieved)
├─ llm.response_time (LLM latency)
├─ cache.hit_rate (Cache efficiency)
└─ db.query_time (Database latency)

Traces:
├─ trace_id (per generation)
└─ Links phases, sources, scores
```

---

## 16. EXTENSION POINTS & FUTURE ROADMAP

### Possible Enhancements

1. **Multi-Model Support**: LLaMA, Claude, Gemini
2. **Fine-tuning**: Domain-specific prompt optimization
3. **Collaborative Generation**: Multiple users working on ideas
4. **Marketplace**: Buy/sell project ideas
5. **Advanced Search**: Full-text, filters, faceting
6. **Real-time Collaboration**: WebSocket for live ideation
7. **Mobile App**: React Native or Flutter
8. **Blockchain**: Idea ownership & attribution tracking
9. **API Marketplace**: Expose core services as public APIs
10. **Workflow Automation**: Export to project boards (JIRA, Linear)

---

## 17. CONFIGURATION REFERENCE

### Core Config Variables

```python
# Database
DATABASE_URL = "postgresql://user:pass@host:5432/innovate_db"

# LLM
LLM_PROVIDER = "ollama"  # or "openai"
LLM_MODEL_NAME = "neural-chat"  # or "gpt-4"
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_TIMEOUT_SECONDS = 60
LLM_MAX_RETRIES = 3

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# API
SECRET_KEY = "your-secret-key"
JWT_EXPIRATION_HOURS = 24
RATE_LIMIT_GENERATION = "20/hour"

# Evidence
MIN_EVIDENCE_REQUIRED = 3

# Features
ENABLE_SEMANTIC_FILTER = True
ENABLE_NOVELTY_ANALYSIS = True
ENABLE_ADMIN_CASCADE = True
```

---

## 18. SUMMARY TABLE: Components at a Glance

| Component | Type | Key Responsibility | Tech |
|-----------|------|-------------------|------|
| **Frontend** | UI | User interaction, forms, dashboards | React, Tailwind |
| **Flask App** | API | Request routing, middleware, response | Flask |
| **Generation** | Service | 4-pass idea synthesis | LLM (Ollama/OpenAI) |
| **Retrieval** | Service | Paper + repo search, ranking | arXiv, GitHub APIs |
| **Novelty** | Service | Semantic scoring, signal fusion | SentenceTransformers |
| **Semantic** | Utility | Embeddings, similarity, filtering | Embeddings DB |
| **Database** | Storage | Persistent data + vectors | PostgreSQL + pgvector |
| **Auth** | Security | User authentication, authorization | JWT, bcrypt |
| **Cache** | Performance | Response & embedding caching | Flask-Cache, LRU |
| **Admin HITL** | Validation | Human feedback loop, verdicts | Manual review UI |

---

This comprehensive analysis provides the foundation for creating:
✅ **User Flow Diagrams** - Journeys through explore, generate, review  
✅ **System Architecture** - Component relationships & data flow  
✅ **Technical Workflow** - Step-by-step generation & scoring  
✅ **AI Architecture** - LLM integration, embedding pipeline  
✅ **Database Design** - Entity relationships, indexes, tables  

Use this document as reference for diagramming tools like:
- Lucidchart / Draw.io (for formal architecture)
- Mermaid.js (for flowcharts in markdown)
- Figma (for design system visualization)
