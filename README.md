# Darpan Labs - Digital Twin Platform

AI-powered digital twin platform for consumer research. Build behavioral twins from voice interviews and run experiments on twin cohorts.

## Overview

Darpan Labs enables:
- **Voice Interviews**: Conduct AI-powered interviews in English, Hindi, or Hinglish
- **Digital Twins**: Create behavioral/personality twins from interview data (ICL-based, no fine-tuning)
- **Twin Chat**: Chat with twins, see confidence scores and evidence
- **Experiments**: Run scenarios against cohorts of twins with aggregate insights

## Tech Stack

- **Backend**: FastAPI, Pydantic v2, SQLAlchemy, Celery
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Database**: PostgreSQL with pgvector
- **LLM**: LiteLLM (supports OpenAI, Anthropic, etc.)
- **Queue**: Redis + Celery

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- PostgreSQL with pgvector (or use Docker)

### 1. Clone and Setup

```bash
cd darpan-labs

# Create backend virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start with Docker

```bash
# Start all services
docker-compose up -d

# Run migrations
cd backend
alembic upgrade head
```

### 3. Or Run Locally

```bash
# Start database (with Docker)
docker-compose up db redis -d

# Run backend
cd backend
uvicorn app.main:app --reload

# In another terminal, run frontend
cd frontend
npm install
npm run dev
```

### 4. Verify

- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Project Structure

```
darpan-labs/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── database.py      # Async SQLAlchemy
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   ├── llm/             # LLM abstraction
│   │   └── workers/         # Celery tasks
│   ├── prompts/             # LLM prompt templates
│   ├── migrations/          # Alembic migrations
│   ├── tests/               # Pytest tests
│   └── seed_data/           # Question banks
├── frontend/
│   └── src/
│       ├── app/             # Next.js app router
│       ├── components/      # React components
│       └── lib/             # Utilities
└── docker-compose.yml
```

## Database Models

| Table | Description |
|-------|-------------|
| users | User accounts |
| consent_events | Consent tracking |
| interview_sessions | Interview sessions |
| interview_modules | Module progress (M1-M4, A1-A6) |
| interview_turns | Q&A turns |
| twin_profiles | Digital twin data |
| evidence_snippets | Evidence with embeddings |
| twin_chat_sessions | Chat sessions |
| twin_chat_messages | Chat messages |
| cohorts | Twin cohorts |
| experiments | Experiment definitions |
| experiment_results | Per-twin results |

## Development Phases

- **Phase 0**: Foundation (this phase) ✅
- **Phase 1**: Text Interview + Modules
- **Phase 2**: Twin Generation + Chat
- **Phase 3**: Voice Pipeline
- **Phase 4**: Experiments + Polish

## Running Tests

```bash
cd backend
pytest -v
```

## Environment Variables

See `.env.example` for all configuration options:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key (for LLM)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)
- `DEEPGRAM_API_KEY`: Deepgram API key (for ASR, later phases)
- `ELEVENLABS_API_KEY`: ElevenLabs API key (for TTS, later phases)

## License

Confidential - Darpan Labs
