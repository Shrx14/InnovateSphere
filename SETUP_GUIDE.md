# InnovateSphere - Complete Setup & Deployment Guide

**A comprehensive cookbook for setting up and running InnovateSphere on any device.**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Prerequisites](#prerequisites)
4. [Quick Start (Docker)](#quick-start-docker)
5. [Manual Setup (Recommended for Development)](#manual-setup-recommended-for-development)
6. [Environment Configuration](#environment-configuration)
7. [Running the Application](#running-the-application)
8. [Development Workflow](#development-workflow)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Configuration](#advanced-configuration)
12. [Deployment](#deployment)

---

## Project Overview

**InnovateSphere** is a full-stack web application that helps users generate innovative project ideas using AI, manage their profiles, and collaborate on creative endeavors.

### Key Features
-  Secure user authentication with JWT tokens
-  AI-powered project idea generation with LLM (supports Ollama & OpenAI)
-  Evidence-grounded novelty scoring with GitHub/arXiv integration
-  Modern React frontend with Tailwind CSS
-  RESTful Flask API backend
-  Rate limiting and abuse detection
-  Comprehensive test suite (unit, integration, end-to-end)

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10+, macOS 10.15+, or Ubuntu 18.04+
- **CPU:** 4 cores (2+ minimum)
- **RAM:** 8GB (16GB+ recommended for Ollama)
- **Disk Space:** 30GB total
- **Internet:** Stable connection for API calls

### Recommended
- **OS:** Ubuntu 22.04 LTS, macOS 12+, or Windows 11
- **CPU:** 8+ cores
- **RAM:** 32GB
- **GPU:** Optional (NVIDIA/AMD for faster inference)
- **SSD:** 50GB+ free space

---

## Prerequisites

### Windows Installation

1. **Git:** \winget install Git.Git\ or download from https://git-scm.com/download/win
2. **Python 3.11+:** \winget install Python.Python.3.12\ or https://python.org (check "Add Python to PATH")
3. **Node.js 18+:** \winget install OpenJS.NodeJS.LTS\ or https://nodejs.org
4. **PostgreSQL 14+:** \winget install PostgreSQL.PostgreSQL\ (optional, SQLite fine for dev)
5. **Ollama:** Download from https://ollama.ai (optional, for local LLM)

**Verify:**
\\\powershell
python --version
node --version
npm --version
git --version
\\\

### macOS Installation

\\\ash
/bin/bash -c 'curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash'
brew install git python node postgresql
brew install --cask ollama  # Optional
\\\

### Linux (Ubuntu/Debian) Installation

\\\ash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3.11 python3-pip python3-venv nodejs npm postgresql postgresql-contrib
curl https://ollama.ai/install.sh | sh  # Optional
\\\

### Clone Repository

\\\ash
cd ~/Projects
git clone https://github.com/yourusername/InnovateSphere.git
cd InnovateSphere
\\\

---

## Quick Start (Docker)

**Prerequisites:** Docker Desktop installed

\\\ash
cd InnovateSphere
docker-compose up --build

# Services available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:5000
# - Database: localhost:5432
\\\

Stop with: \docker-compose down\

---

## Manual Setup (Recommended for Development)

### Backend Setup

**1. Create Virtual Environment:**

\\\ash
cd backend

# Windows
python -m venv venv
venv\\Scripts\\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
\\\

**2. Install Dependencies:**

\\\ash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
\\\

**3. Verify Installation:**

\\\ash
python -c "from flask import Flask; print(' Flask works')"
python -c "from sentence_transformers import SentenceTransformer; print(' Transformers work')"
\\\

### Database Setup

**Option A: PostgreSQL**

\\\powershell
# Windows
\='postgres'
psql -U postgres -h localhost -c "CREATE DATABASE innovatesphere;"

# macOS
brew services start postgresql
psql postgres -c "CREATE DATABASE innovatesphere;"

# Linux
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE innovatesphere;"
\\\

**Option B: SQLite (Development)**

Use in \.env\: \DATABASE_URL=sqlite:///innovatesphere.db\

### Frontend Setup

\\\ash
cd frontend
npm install
\\\

---

## Environment Configuration

### backend/.env

\\\
# DATABASE
DATABASE_URL=sqlite:///innovatesphere.db

# SECURITY
SECRET_KEY=your-secret-key-change-this
JWT_SECRET=your-jwt-secret-change-this
JWT_ALGO=HS256
JWT_EXP_SECONDS=3600

# FLASK
FLASK_APP=backend.core.app
FLASK_ENV=development
FLASK_DEBUG=1

# LLM CONFIG (Ollama - free local)
LLM_PROVIDER=ollama
LLM_MODEL_NAME=phi3:mini
OLLAMA_BASE_URL=http://localhost:11434
LLM_STARTUP_HARD_FAIL=false

# Or use OpenAI (paid)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# EMBEDDING
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# RETRIEVAL
MAX_SOURCES_FOR_LLM=8
MIN_EVIDENCE_REQUIRED=3
MAX_GENERATION_REQUESTS_PER_MIN=6

# SECURITY
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
GITHUB_TOKEN=ghp_...  # Optional

# RATE LIMITING
ABUSE_WINDOW_SECONDS=60
AUTO_BLOCK_AFTER_INFRACTIONS=5
\\\

### frontend/.env.local

\\\
REACT_APP_API_URL=http://localhost:5000
REACT_APP_API_TIMEOUT=30000
NODE_ENV=development
\\\

### Generate Secure Secrets

\\\ash
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"
python -c "import secrets; print(f'JWT_SECRET={secrets.token_hex(32)}')"
\\\

---

## Running the Application

### Development Mode (3 Terminal Windows)

**Terminal 1: Ollama**
\\\ash
ollama serve
# First run: ollama pull phi3:mini  (~2-3GB download)
\\\

**Terminal 2: Backend**
\\\ash
cd backend
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
python -m flask run --port 5000
\\\

**Terminal 3: Frontend**
\\\ash
cd frontend
npm start
\\\

**Verify it works:**
- Frontend: http://localhost:3000
- Backend health: \curl http://localhost:5000/health\
- Ollama: \curl http://localhost:11434/api/tags\

### Production Mode

Backend:
\\\ash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 "backend.core.app:create_app()"
\\\

Frontend:
\\\ash
cd frontend
npm run build
# Deploy build/ folder
\\\

---

## Testing

\\\ash
# All tests
pytest tests/ -v

# By category
pytest tests/backend/ -v
pytest tests/integration/ -v

# Single test
pytest tests/backend/test_auth.py::test_create_access_token -v

# With coverage
pytest --cov=backend --cov-report=html
\\\

---

## Troubleshooting

### Backend

**Port 5000 in use:**
\\\powershell
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
\\\

**Module not found:**
\\\ash
source venv/bin/activate  # Activate environment
pip install -r requirements.txt
\\\

**Ollama connection error:**
\\\ash
# Start Ollama separately: ollama serve
# Or set in .env: LLM_STARTUP_HARD_FAIL=false
\\\

**Database error:**
\\\ash
# SQLite - check file exists: ls -la innovatesphere.db
# PostgreSQL - verify running: psql -U postgres -h localhost
\\\

### Frontend

**npm install error:**
\\\ash
npm cache clean --force
rm package-lock.json node_modules -r
npm install
\\\

**API connection error:**
- Check backend is running on :5000
- Check REACT_APP_API_URL in .env.local
- Check CORS_ORIGINS in backend/.env

**Styling not loading:**
\\\ash
npm run tailwind:init
npm start
\\\

---

## Advanced Configuration

### Use OpenAI

\\\
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...your-key...
LLM_MODEL_NAME=gpt-3.5-turbo
\\\

### Use PostgreSQL

\\\
DATABASE_URL=postgresql://user:password@localhost:5432/innovatesphere
\\\

### Custom Embedding

\\\
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIM=768
\\\

---

## Deployment

### Heroku

\\\ash
heroku login
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
\\\

### AWS EC2

\\\ash
ssh -i key.pem ubuntu@instance-ip
git clone repo && cd InnovateSphere
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
nano .env  # Configure
gunicorn -w 4 "backend.core.app:create_app()"
\\\

### Docker

\\\ash
docker build -t innovatesphere-backend backend/
docker build -t innovatesphere-frontend frontend/
docker-compose -f docker-compose.prod.yml up -d
\\\

---

## Quick Reference

\\\ash
# Activate backend
source backend/venv/bin/activate

# Start services (3 terminals)
ollama serve
flask run
npm start  # from frontend/

# Install deps
pip install -r backend/requirements.txt
npm install --prefix frontend

# Run tests
pytest tests/ -v

# Database
flask db migrate
flask db upgrade
\\\

---

## Pre-Launch Checklist

-  Python 3.11+ & Node 18+ installed
-  Git cloned repository
-  Backend venv created & activated
-  Backend dependencies installed
-  backend/.env configured
-  Database initialized
-  frontend/.env.local configured
-  Frontend dependencies installed
-  Tests pass: \pytest tests/ -v\
-  Ollama running (if using)
-  Backend starts: \lask run\
-  Frontend starts: \
pm start\
-  App loads at http://localhost:3000
-  API responds at http://localhost:5000/health

---

**Last Updated:** February 2026  
**Version:** 1.0.0

## Project Directory Structure

```
InnovateSphere/
├── backend/                      # Flask API backend
│   ├── venv/                     # Python virtual environment (git-ignored)
│   ├── core/
│   │   ├── app.py               # Flask app factory & entry point
│   │   ├── config.py            # Configuration management
│   │   ├── db.py                # Database setup
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── auth.py              # JWT authentication
│   │   └── __init__.py
│   ├── api/
│   │   ├── routes/              # API endpoint blueprints
│   │   │   ├── generation.py    # POST /api/generate
│   │   │   ├── novelty.py       # POST /api/novelty/analyze
│   │   │   ├── ideas.py         # GET/POST /api/ideas
│   │   │   └── auth.py          # POST /api/login, /register
│   │   └── __init__.py
│   ├── generation/              # Idea generation engine
│   │   ├── generator.py         # Core generation logic
│   │   └── constraints.py
│   ├── novelty/                 # Novelty scoring system
│   │   ├── analyzer.py          # Scoring algorithm
│   │   └── __init__.py
│   ├── retrieval/               # External data retrieval
│   │   ├── github_client.py     # GitHub API integration
│   │   ├── arxiv_client.py      # arXiv API integration
│   │   └── __init__.py
│   ├── ai/                      # LLM integration
│   │   ├── llm_client.py        # Ollama/OpenAI wrapper
│   │   ├── prompts.py           # Prompt templates
│   │   └── registry.py          # Model registry
│   ├── tests/                   # Test suite (restructured)
│   │   ├── backend/             # Backend unit tests
│   │   ├── integration/         # Integration tests
│   │   ├── scripts/             # Script tests
│   │   └── unit/                # Unit tests
│   ├── requirements.txt         # Python package dependencies
│   ├── app.py                   # Compatibility shim for imports
│   ├── run.py                   # Development entry point
│   └── .env                     # Environment variables (git-ignored)
│
├── frontend/                     # React frontend application
│   ├── public/                  # Static files, favicon, manifest
│   ├── src/
│   │   ├── components/          # Reusable React components
│   │   │   ├── LoginForm.jsx
│   │   │   ├── IdeaGenerator.jsx
│   │   │   ├── IdeaCard.jsx
│   │   │   └── ...
│   │   ├── pages/               # Page-level components
│   │   │   ├── HomePage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── ...
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.js
│   │   │   ├── useIdeas.js
│   │   │   └── ...
│   │   ├── context/             # React Context for state
│   │   │   └── AuthContext.jsx
│   │   ├── config/              # Frontend configuration
│   │   │   └── api.js
│   │   ├── App.jsx              # Root component
│   │   ├── index.js             # Entry point
│   │   └── index.css            # Global styles
│   ├── package.json             # Node.js dependencies
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   ├── postcss.config.js        # PostCSS configuration
│   ├── .env.local               # Frontend environment (git-ignored)
│   └── build/                   # Production build (git-ignored)
│
├── docs/                        # Documentation
│   ├── AI_ARCHITECTURE.md       # LLM integration details
│   ├── FRONTEND_DESIGN.md       # Frontend architecture
│   ├── API_REFERENCE.md         # API endpoint documentation
│   ├── PROJECT_ANALYSIS.md      # Project analysis
│   ├── DIAGRAMS_MERMAID.md      # Architecture diagrams
│   ├── TODO.md                  # Development TODO items
│   └── ...
│
├── tests/                       # Consolidated test suite (restructured)
│   ├── backend/                 # Backend unit tests
│   │   ├── test_auth.py
│   │   ├── test_config.py
│   │   ├── test_abuse.py
│   │   └── __init__.py
│   ├── integration/             # Integration & E2E tests
│   │   ├── test_api_integration.py
│   │   ├── test_github_queries.py
│   │   ├── test_orchestrator_integration.py
│   │   └── __init__.py
│   ├── scripts/                 # Script-based tests
│   │   ├── test_components.py
│   │   ├── test_novelty_direct.py
│   │   └── __init__.py
│   ├── unit/                    # Additional unit tests
│   └── __init__.py
│
├── SETUP_GUIDE.md              # This file - comprehensive setup guide
├── README.md                   # Project overview
├── package.json               # Root package.json (Tailwind/PostCSS config)
├── postcss.config.js          # PostCSS configuration (root level)
├── tailwind.config.js         # Tailwind CSS configuration (root level)
├── .gitignore                 # Git ignore rules
└── instance/                  # Instance-specific files (git-ignored)
```

---

## Development Workflow

### Making Backend Changes

1. **Activate virtual environment:**
   ```bash
   source backend/venv/bin/activate  # macOS/Linux
   backend\venv\Scripts\activate     # Windows
   ```

2. **Edit files in backend/ folders:**
   - `backend/api/routes/` - Add or modify API endpoints
   - `backend/core/` - Core app logic
   - `backend/generation/` - Idea generation engine
   - `backend/novelty/` - Novelty scoring
   - `backend/retrieval/` - GitHub/arXiv integration

3. **Flask auto-reloads changes:**
   - Run: `python -m flask run --port 5000`
   - Changes auto-detected (FLASK_DEBUG=1 in .env)
   - Server restarts automatically

4. **Test your changes:**
   ```bash
   pytest tests/backend/test_yourfile.py -v
   ```

### Making Frontend Changes

1. **Start React dev server:**
   ```bash
   cd frontend
   npm start
   ```

2. **Edit files in frontend/src/:**
   - `components/` - Reusable UI components
   - `pages/` - Full-page components
   - `hooks/` - Custom React hooks
   - `config/` - Application configuration

3. **React hot-reloads changes:**
   - Browser auto-refreshes on file save
   - No need to restart dev server

4. **Test your changes:**
   ```bash
   npm test  # Run React test suite
   ```

### Database Changes

1. **Modify SQLAlchemy models:**
   ```python
   # backend/core/models.py
   class Idea(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       new_field = db.Column(db.String(100))
   ```

2. **Create migration:**
   ```bash
   cd backend
   flask db migrate -m "Add new_field to Idea table"
   ```

3. **Apply migration:**
   ```bash
   flask db upgrade
   ```

---

## Complete Testing Guide

### Test Suite Organization

```
tests/
├── backend/                    # Unit tests for backend modules
│   ├── test_auth.py           # Authentication & JWT tokens
│   ├── test_config.py         # Configuration validation
│   ├── test_abuse.py          # Abuse detection & rate limiting
│   └── test_novelty_endpoint.py
│
├── integration/               # Integration & end-to-end tests
│   ├── test_api_integration.py
│   ├── test_github_queries.py
│   ├── test_novelty_fixes.py
│   └── test_orchestrator_integration.py
│
├── scripts/                   # Script-based component tests
│   ├── test_components.py
│   ├── test_novelty_direct.py
│   └── test_payload_formats.py
│
└── unit/                      # Additional unit tests
```

### Running Tests

```bash
# Run ALL tests
pytest tests/ -v

# Run specific category
pytest tests/backend/ -v          # Backend unit tests only
pytest tests/integration/ -v      # Integration tests only
pytest tests/scripts/ -v          # Script tests only

# Run single test file
pytest tests/backend/test_auth.py -v

# Run specific test function
pytest tests/backend/test_auth.py::test_create_access_token -v

# Run tests matching pattern
pytest -k "novelty" -v            # All tests with "novelty" in name

# Show print output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests only
pytest --lf

# Generate HTML coverage report
pytest --cov=backend --cov-report=html
# View at: htmlcov/index.html

# Run with specific markers
pytest -m "integration" -v
```

### Writing Tests

**Backend test example:**
```python
import pytest
from backend.core.auth import create_access_token

def test_create_access_token():
    token = create_access_token(identity=1, additional_claims={'role': 'user'})
    
    # Token should not be None
    assert token is not None
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Token should be decodable
    import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["sub"] == "1"
    assert payload["role"] == "user"
```

---

## Complete Troubleshooting Guide

### Common Issues & Solutions

#### "ImportError: No module named 'flask'"
```bash
# Solution: Activate virtual environment and reinstall
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -c "from flask import Flask; print('Success')"
```

#### "Address already in use: ('127.0.0.1', 5000)"
```powershell
# Windows: Find and kill process
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux: Find and kill process
lsof -i :5000
kill -9 <PID>

# Or use different port
python -m flask run --port 5001
```

#### "OSError: [Errno 48] Address already in use" (macOS)
```bash
# Kill processes using port
sudo lsof -i :5000
sudo kill -9 <PID>

# Or use different port
FLASK_RUN_PORT=5001 flask run
```

#### "ConnectionRefusedError: Ollama not running"
```bash
# Solution 1: Start Ollama in separate terminal
ollama serve

# Solution 2: Allow app to start without Ollama (development)
# In backend/.env:
LLM_STARTUP_HARD_FAIL=false

# Solution 3: Check Ollama is accessible
curl http://localhost:11434/api/tags
```

#### "CUDA out of memory" (when using GPU)
```bash
# Use smaller model
# backend/.env:
LLM_MODEL_NAME=phi3:mini

# Or use CPU only
# Stop Ollama and restart
OLLAMA_HOST=127.0.0.1 ollama serve
```

#### "ModuleNotFoundError: No module named 'backend'"
```bash
# Make sure sys.path includes repo root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from repo root
cd InnovateSphere
python -m flask run  # Not flask run from backend/
```

#### "psycopg2.Error: could not translate host name"
```bash
# PostgreSQL not running or wrong connection string
# Check connection string in backend/.env

# Start PostgreSQL
# Windows: Should auto-start
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Test connection
psql -U postgres -h localhost
```

#### "UNIQUE constraint failed: user.email"
```python
# SQLAlchemy ORM error - email already exists
# Solution: Use different email during testing or reset database
db.session.query(User).delete()
db.session.commit()
```

#### "npm ERR! code EACCES: permission denied"
```bash
# Node.js permission issue
npm cache clean --force
npm cache verify

# Reinstall packages
rm -rf node_modules package-lock.json
npm install
```

#### "error:0308010C:digital envelope routines::unsupported (... NODE_OPTIONS=--openssl-legacy-provider)"
```bash
# Node version incompatibility with React scripts
# Set environment variable
export NODE_OPTIONS=--openssl-legacy-provider  # macOS/Linux
set NODE_OPTIONS=--openssl-legacy-provider     # Windows

npm start
```

#### "React router TypeError: Cannot read property 'pathname' of undefined"
```bash
# Usually browser history issue or missing wrapper
# Clear browser cache: Ctrl+Shift+Delete
# Hard refresh: Ctrl+Shift+R or Cmd+Shift+R
```

#### "CORS error: No 'Access-Control-Allow-Origin' header"
```bash
# backend/.env - update CORS_ORIGINS to match frontend URL
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Or allow all (development only):
CORS_ORIGINS=*
```

---

## Environment Variables Reference

### Backend (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///innovatesphere.db` | Database connection string |
| `SECRET_KEY` | `dev-secret-key` | Flask secret key - **change in production** |
| `JWT_SECRET` | `dev-jwt-secret` | JWT signing secret - **change in production** |
| `JWT_ALGO` | `HS256` | JWT algorithm |
| `JWT_EXP_SECONDS` | `3600` | JWT token expiration time (seconds) |
| `FLASK_APP` | `backend.core.app` | Flask app module |
| `FLASK_ENV` | `development` | Flask environment (development/production) |
| `FLASK_DEBUG` | `1` | Enable Flask debug mode (auto-reload) |
| `LLM_PROVIDER` | `ollama` | LLM provider (ollama/openai) |
| `LLM_MODEL_NAME` | `phi3:mini` | Model name to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | `` | OpenAI API key (if using OpenAI) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Model for embeddings |
| `EMBEDDING_DIM` | `384` | Embedding dimensionality |
| `MAX_SOURCES_FOR_LLM` | `8` | Max sources shown to LLM |
| `MIN_EVIDENCE_REQUIRED` | `3` | Minimum sources for validation |
| `MAX_GENERATION_REQUESTS_PER_MIN` | `6` | Rate limit (requests/minute) |
| `ABUSE_WINDOW_SECONDS` | `60` | Abuse detection window |
| `AUTO_BLOCK_AFTER_INFRACTIONS` | `5` | Auto-block after N violations |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `GITHUB_TOKEN` | `` | GitHub API token (optional) |
| `LLM_STARTUP_HARD_FAIL` | `true` | Fail app startup if LLM unavailable |

### Frontend (.env.local)

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_API_URL` | `http://localhost:5000` | Backend API URL |
| `REACT_APP_API_TIMEOUT` | `30000` | API request timeout (ms) |
| `NODE_ENV` | `development` | Node environment |

---

## Performance Tips

### Backend Optimization

1. **Use connection pooling:**
   ```python
   # backend/core/config.py
   SQLALCHEMY_ENGINE_OPTIONS = {
       'pool_size': 10,
       'pool_recycle': 3600,
       'pool_pre_ping': True,
   }
   ```

2. **Enable query optimization:**
   ```python
   # Only in production
   SQLALCHEMY_ECHO = False
   ```

3. **Cache expensive operations:**
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

4. **Use async for I/O:**
   ```bash
   pip install flask-asyncio
   ```

### Frontend Optimization

1. **Code splitting:**
   ```jsx
   const LazyComponent = React.lazy(() => import('./Component'));
   ```

2. **Memoization:**
   ```jsx
   const MemoComponent = React.memo(Component);
   ```

3. **Production build:**
   ```bash
   npm run build
   # Minified and optimized
   ```

---

## Support & Resources

- **GitHub Repository:** https://github.com/yourusername/InnovateSphere
- **Issues:** GitHub Issues tab
- **Discussions:** GitHub Discussions
- **Email:** support@innovatesphere.dev
- **Documentation:** See `docs/` folder

---

For issues, see GitHub Issues or email support@innovatesphere.dev
