# Adaptive AI Interviewer

Independent module implementing the Adaptive AI Interviewer spec
(`Adaptive_AI_Interviewer_Design_Spec_v1.docx`) — a 60-minute
text-administered interview for the laptop category that silently
classifies respondents into one of three archetypes (prosumer, SMB IT
buyer, consumer) and routes them through archetype-specific JTBD,
conjoint, brand, and tone blocks before a universal personality +
values tail.

## Tech stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + async SQLAlchemy (Python 3.11) |
| Frontend | Next.js 14 (TypeScript, App Router) |
| DB | PostgreSQL — **shares the tables declared by `ai-interviewer`** (interview_sessions / interview_modules / interview_turns); adds its own `adaptive_classifications` and `adaptive_outputs` tables |
| LLM | LiteLLM (provider-agnostic — OpenAI / Anthropic / etc., switched via env) |
| Personality battery | BFI-2-S (Soto & John 2017) — academic use |
| Values battery | PVQ-10 (Schwartz / ESS) |
| Classifier | LLM-based (few-shot JSON mode), **not** heuristic-weighted |
| Conjoint | Balanced orthogonal choice sets → aggregate MNL → empirical-Bayes shrinkage for per-respondent part-worths |

## Ports

| Process | Port |
|---------|------|
| Backend | 8002 |
| Frontend | 3002 |

## Running locally

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8002

# Frontend
cd frontend && npm install && npm run dev
```

The backend reads the same `.env` used by the other modules
(`DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `LLM_MODEL`,
etc.) — see `backend/app/config.py`.

## Shared DB note

The new module reuses the three Q&A tables created by
`ai-interviewer` (same column layout, same names). We declare
equivalent SQLAlchemy models here pointing at the same tables; in
production `Base.metadata.create_all` is a no-op for tables that
already exist. Adaptive-specific data (classification history,
per-respondent output JSON) lives in two new tables prefixed
`adaptive_`.
