# Darpan Labs - AI-Powered Consumer Research Platform

AI-powered interview platform for consumer research. Conducts structured voice/text interviews across modular question banks to build deep consumer understanding.

## Overview

Darpan Labs enables:
- **AI Interviews**: Conduct structured interviews with AI-powered follow-up probing, acknowledgment, and satisfaction scoring
- **Voice Support**: Record voice responses with real-time transcription (OpenAI Whisper) and transcript correction
- **Modular Question Banks**: 8 themed modules (M1-M8) covering identity, preferences, decision logic, lifestyle, sensory aesthetics, product deep-dives, and concept testing
- **Admin Dashboard**: View transcripts, module completion status, and manage interviews
- **Multi-language**: Supports English, Hindi, and Hinglish responses

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Pydantic v2, SQLAlchemy (async), LiteLLM |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Zustand, Framer Motion |
| **Database** | PostgreSQL (asyncpg) |
| **LLM** | LiteLLM (OpenAI, Anthropic, etc.) |
| **Voice/ASR** | OpenAI Whisper API |
| **Auth** | Google OAuth + JWT |
| **Deployment** | Railway / Docker Compose |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (or use Docker)

### 1. Clone and Setup

```bash
git clone https://github.com/Aniket-Pratik/darpan-labs-V2.git
cd darpan-labs-V2

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start with Docker Compose

```bash
docker-compose up -d

# Backend auto-creates tables on startup
```

### 3. Or Run Locally

```bash
# Start database (with Docker)
docker-compose up db -d

# Run backend
cd backend
uvicorn app.main:app --reload

# In another terminal, run frontend
cd frontend
npm install
npm run dev
```

### 4. Verify

- Backend Health: http://localhost:8000/health
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Project Structure

```
darpan-labs/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database.py          # Async SQLAlchemy engine & session
│   │   ├── dependencies.py      # FastAPI dependency injection
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── user.py          # User model
│   │   │   ├── interview.py     # Session, module, turn models
│   │   │   └── consent.py       # Consent tracking
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API route handlers
│   │   │   ├── interviews.py    # Interview CRUD & flow
│   │   │   ├── voice.py         # Voice recording & transcription
│   │   │   ├── auth.py          # Google OAuth & JWT
│   │   │   └── admin.py         # Admin transcript & status views
│   │   ├── services/            # Business logic layer
│   │   │   ├── interview_service.py       # Core interview orchestration
│   │   │   ├── question_bank_service.py   # Module question loading
│   │   │   ├── prompt_service.py          # LLM prompt rendering
│   │   │   ├── answer_parser_service.py   # Response parsing & scoring
│   │   │   ├── module_state_service.py    # Module progress tracking
│   │   │   ├── asr_service.py             # Speech-to-text (Whisper)
│   │   │   ├── voice_orchestrator.py      # Voice pipeline coordination
│   │   │   ├── transcript_corrector.py    # LLM-based transcript cleanup
│   │   │   └── auth_service.py            # Auth logic
│   │   ├── llm/                 # LLM abstraction (LiteLLM)
│   │   └── workers/             # Background task stubs
│   ├── prompts/                 # LLM prompt templates (.txt)
│   │   ├── interviewer_question.txt
│   │   ├── answer_parser.txt
│   │   ├── answer_satisfaction.txt
│   │   ├── acknowledgment.txt
│   │   ├── followup_probe.txt
│   │   ├── module_completion.txt
│   │   └── transcript_correction.txt
│   ├── seed_data/
│   │   └── question_banks/      # JSON question banks (M1-M8)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                 # Next.js app router pages
│       │   ├── page.tsx         # Landing page
│       │   ├── login/           # Login page
│       │   ├── create/modules/  # Module selection & interview start
│       │   ├── interview/       # Interview UI
│       │   ├── profile/         # User profile
│       │   └── admin/           # Admin dashboard
│       ├── components/
│       │   ├── interview/       # Interview chat & voice components
│       │   ├── navigation/      # Nav bar
│       │   ├── auth/            # Auth components
│       │   └── ui/              # Shared UI primitives
│       ├── lib/                 # API client & utilities
│       ├── store/               # Zustand state management
│       ├── hooks/               # Custom React hooks
│       ├── types/               # TypeScript type definitions
│       └── styles/              # Global styles
├── docker-compose.yml
└── README.md
```

## Interview Modules

| Module | Name | Description |
|--------|------|-------------|
| M1 | Core Identity & Context | Demographics, background, self-perception |
| M2 | Preferences & Values | Personal values, brand preferences |
| M3 | Purchase Decision Logic | How they evaluate and buy products |
| M4 | Lifestyle & Grooming | Daily routines, grooming habits |
| M5 | Sensory & Aesthetic | Sensory preferences, aesthetic tastes |
| M6 | Body Wash Deep Dive | Category-specific deep exploration |
| M7 | Media & Influence | Media consumption, influencer impact |
| M8 | Concept Test | Evaluate product concepts with structured scoring |

## API Endpoints

### Interviews
- `POST /api/v1/interviews/start-module` — Start a module interview
- `POST /api/v1/interviews/{session_id}/answer` — Submit an answer
- `POST /api/v1/interviews/{session_id}/complete-module` — Complete current module
- `GET /api/v1/interviews/user/{user_id}/modules` — Get module completion status

### Voice
- `POST /api/v1/voice/transcribe` — Transcribe audio (Whisper)

### Auth
- `POST /api/v1/auth/google` — Google OAuth login
- `GET /api/v1/auth/me` — Get current user

### Admin
- `GET /api/v1/admin/transcripts` — View all transcripts
- `GET /api/v1/admin/modules/status` — Module completion overview

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key (for LLM + Whisper) | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative LLM) | No |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes |
| `AUTH_SECRET_KEY` | JWT signing secret | Yes |
| `LLM_MODEL` | LiteLLM model name (default: `gpt-4-turbo-preview`) | No |
| `CORS_ORIGINS` | Allowed CORS origins (JSON list) | No |
| `SENTRY_DSN` | Sentry error tracking | No |
| `LANGFUSE_PUBLIC_KEY` | Langfuse observability | No |
| `LANGFUSE_SECRET_KEY` | Langfuse observability | No |

## How It Works

1. **User signs in** via Google OAuth
2. **Selects modules** to complete from the module dashboard
3. **AI interviewer** asks questions from the selected module's question bank
4. **User responds** via text or voice (voice is transcribed and corrected by LLM)
5. **Answer parser** evaluates response satisfaction and extracts key insights
6. **Follow-up probes** are generated if the answer needs deeper exploration
7. **Module completes** when all questions are satisfactorily answered
8. **Admin dashboard** allows viewing transcripts and tracking progress

## License

Confidential - Darpan Labs
