# Darpan Labs — Claude Code Implementation Guide

## BLUF
This document contains **9 copy-paste-ready Claude Code prompts** across 5 phases (7 weeks) to build the complete Darpan Labs Digital Twin platform. Each prompt is self-contained with context, schemas, API contracts, test specs, and constraints. Follow sequentially — each phase builds on the previous.

---

## Pre-Requisites (Do Before Session 1)

### 1. Local Environment Setup
```bash
# Create monorepo
mkdir darpan-labs && cd darpan-labs
git init

# Backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic[v2] sqlalchemy alembic asyncpg pgvector litellm celery redis python-jose passlib python-multipart websockets deepgram-sdk elevenlabs sentry-sdk posthog langfuse httpx pytest pytest-asyncio

# Frontend
npx create-next-app@14 frontend --typescript --tailwind --app --src-dir
cd frontend && npm install zustand @tanstack/react-query lucide-react framer-motion recharts sonner

# Database
docker run -d --name darpan-db -e POSTGRES_PASSWORD=darpan -e POSTGRES_DB=darpan -p 5432:5432 pgvector/pgvector:pg16
```

### 2. Repo Structure (Create This First)
```
darpan-labs/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic models
│   │   ├── routers/          # API routes
│   │   ├── services/         # Business logic
│   │   ├── llm/              # LLM abstraction layer
│   │   └── workers/          # Celery tasks
│   ├── prompts/              # LLM prompt templates as .txt files
│   ├── migrations/           # Alembic
│   ├── tests/
│   └── seed_data/            # Question banks JSON
├── frontend/
│   └── src/
│       ├── app/              # Next.js app router
│       ├── components/
│       │   ├── ui/           # Shared UI components
│       │   ├── interview/    # Interview-specific
│       │   ├── twin/         # Twin profile + chat
│       │   └── experiment/   # Experiment engine
│       ├── lib/              # API client, utils
│       ├── hooks/            # Custom React hooks
│       └── styles/           # Theme + globals
├── docker-compose.yml
└── README.md
```

### 3. Theme Specification (Extract from Darpan Labs Website)

```
DARPAN LABS DESIGN SYSTEM
═══════════════════════════

Colors:
  --bg-primary:       #0A0A0A     (near-black background)
  --bg-secondary:     #111111     (card/surface background)
  --bg-elevated:      #1A1A1A     (elevated surfaces, modals)
  --border-default:   #2A2A2A     (subtle borders)
  --border-accent:    #333333     (active borders)

  --text-primary:     #FFFFFF     (headings, primary text)
  --text-secondary:   #A0A0A0     (body text, descriptions)
  --text-muted:       #666666     (labels, placeholders)

  --accent-lime:      #C8FF00     (primary CTA, highlights — the signature Darpan green)
  --accent-lime-dim:  #9ACC00     (hover state)
  --accent-cyan:      #00D4FF     (secondary CTA, links, info)
  --accent-cyan-dim:  #00A8CC     (hover state)

  --success:          #00FF88     (success states)
  --warning:          #FFB800     (warnings)
  --error:            #FF4444     (errors)
  --info:             #00D4FF     (info — same as cyan)

  --confidence-high:  #00FF88     (green)
  --confidence-med:   #FFB800     (amber)
  --confidence-low:   #FF4444     (red)

Typography:
  Font Family: "Inter" (primary), "JetBrains Mono" (code/data)
  Headings: Inter, 600-700 weight
  Body: Inter, 400 weight
  Data/Metrics: JetBrains Mono, 500 weight

  Scale: 12px / 14px / 16px / 20px / 24px / 32px / 48px

Visual Style:
  - Dark-first design (think Linear, Vercel dashboard)
  - Neon wireframe/holographic illustrations
  - Glow effects on primary actions (box-shadow with accent-lime)
  - Subtle grid/dot pattern on backgrounds
  - Cards with 1px border (#2A2A2A), rounded-lg
  - Glass-morphism for modals (backdrop-blur)

Button Styles:
  Primary:   bg-[#C8FF00] text-black font-semibold hover:bg-[#9ACC00]
  Secondary: border border-[#00D4FF] text-[#00D4FF] hover:bg-[#00D4FF]/10
  Ghost:     text-[#A0A0A0] hover:text-white hover:bg-white/5

Specific Components:
  - Progress bars: gradient from #C8FF00 to #00D4FF
  - Confidence badges: color-coded (high=green, med=amber, low=red)
  - Voice waveform: #C8FF00 animated bars on #1A1A1A
  - Module cards: #111111 bg, #2A2A2A border, lime accent on completion
```

---

## Phase 0: Foundation (Week 1) — 1 Claude Code Session

### Session P0: Project Skeleton + DB + Schemas + CI

**Copy this entire prompt into Claude Code:**

```
You are building Phase 0 (Foundation) of the Darpan Labs Digital Twin platform.

## Context
Darpan Labs builds AI-powered digital twins of consumers through voice interviews. The platform has 5 core modules:
1. Voice-Based AI Interviewer (EN/HI/Hinglish)
2. Modular Interview Architecture (4 mandatory + 4 add-on modules)
3. ICL-Based Twin Creation (incremental quality)
4. Twin Chat Interface (confidence + evidence grounding)
5. Experiment Engine (cohort simulation)

Tech stack: FastAPI + Pydantic v2 (backend), Next.js 14 + TypeScript + Tailwind (frontend), Postgres + pgvector, Redis + Celery, LiteLLM.

## Task
Build the complete project foundation. Every subsequent phase inherits this.

### 1. Backend Project Structure
Create a FastAPI app with:
- `app/main.py` — FastAPI app with CORS, error handling, health check
- `app/config.py` — Settings via pydantic-settings (DATABASE_URL, REDIS_URL, LLM keys, ASR/TTS keys)
- `app/database.py` — Async SQLAlchemy engine + session factory + pgvector extension

### 2. Database Models (SQLAlchemy) — ALL tables:

```python
# users
id: UUID (PK)
email: str (unique)
display_name: str
auth_provider_id: str
created_at: timestamptz
updated_at: timestamptz

# consent_events
id: UUID (PK)
user_id: UUID (FK users)
consent_type: str  # "interview", "audio_storage", "sensitive_topics", "data_retention"
consent_version: str
accepted: bool
metadata: jsonb
created_at: timestamptz

# interview_sessions
id: UUID (PK)
user_id: UUID (FK users)
status: str  # active / completed / paused
input_mode: str  # voice / text
language_preference: str  # auto / en / hi
started_at: timestamptz
ended_at: timestamptz (nullable)
total_duration_sec: int (nullable)

# interview_modules
id: UUID (PK)
session_id: UUID (FK interview_sessions)
module_id: str  # M1, M2, M3, M4, A1-A6
status: str  # active / completed / skipped
started_at: timestamptz
ended_at: timestamptz (nullable)
question_count: int (default 0)
coverage_score: float (default 0.0)
confidence_score: float (default 0.0)
signals_captured: jsonb  # list of signal names
completion_eval: jsonb  # LLM evaluation output

# interview_turns
id: UUID (PK)
session_id: UUID (FK interview_sessions)
module_id: str
turn_index: int
role: str  # interviewer / user / system
input_mode: str  # voice / text
question_text: str (nullable)
question_meta: jsonb  # category, type, rationale, target_signal
answer_text: str (nullable)
answer_raw_transcript: str (nullable)  # raw ASR before correction
answer_language: str (nullable)  # EN / HI / HG
answer_structured: jsonb (nullable)
answer_meta: jsonb (nullable)  # sentiment, specificity, confidence
audio_meta: jsonb (nullable)  # duration_ms, sample_rate, vad_events, asr_confidence
audio_storage_ref: str (nullable)  # S3 path, TTL
created_at: timestamptz

# twin_profiles
id: UUID (PK)
user_id: UUID (FK users)
version: int  # 1, 2, 3...
status: str  # generating / ready / failed
modules_included: text[]  # ["M1","M2","M3","M4","A1"]
quality_label: str  # base / enhanced / rich / full
quality_score: float  # 0.0-1.0
structured_profile_json: jsonb
persona_summary_text: text  # compact prompt payload ≤2500 tokens
persona_full_text: text (nullable)
coverage_confidence: jsonb  # per-module and per-domain map
extraction_meta: jsonb  # model, prompt version, retries
created_at: timestamptz

# evidence_snippets
id: UUID (PK)
user_id: UUID (FK users)
twin_profile_id: UUID (FK twin_profiles, nullable)
module_id: str
turn_id: UUID (FK interview_turns)
snippet_text: text
snippet_category: str  # personality, preference, behavior, context
embedding: vector(1536)  # pgvector
metadata: jsonb
created_at: timestamptz

# twin_chat_sessions
id: UUID (PK)
twin_id: UUID (FK twin_profiles)
created_by: UUID (FK users)
created_at: timestamptz

# twin_chat_messages
id: UUID (PK)
session_id: UUID (FK twin_chat_sessions)
role: str  # user / twin
content: text
confidence_score: float (nullable)
confidence_label: str (nullable)  # low / medium / high
evidence_used: jsonb (nullable)
coverage_gaps: text[] (nullable)
model_meta: jsonb (nullable)
created_at: timestamptz

# cohorts
id: UUID (PK)
created_by: UUID (FK users)
name: str
twin_ids: UUID[]
filters_used: jsonb
created_at: timestamptz

# experiments
id: UUID (PK)
created_by: UUID (FK users)
name: str
cohort_id: UUID (FK cohorts)
scenario: jsonb  # type, prompt, options, context
settings: jsonb  # temperature, max_tokens, etc.
status: str  # pending / running / completed / failed
aggregate_results: jsonb (nullable)
created_at: timestamptz
completed_at: timestamptz (nullable)

# experiment_results
id: UUID (PK)
experiment_id: UUID (FK experiments)
twin_id: UUID (FK twin_profiles)
choice: str (nullable)
reasoning: text
confidence_score: float
confidence_label: str
evidence_used: jsonb
coverage_gaps: text[]
model_meta: jsonb
created_at: timestamptz
```

### 3. Pydantic Schemas (request/response models)
Create Pydantic v2 models for ALL API endpoints:
- InterviewStartRequest/Response
- InterviewAnswerRequest/Response
- InterviewNextQuestionResponse
- TwinGenerateRequest/Response
- TwinProfileResponse
- TwinChatRequest/Response
- CohortCreateRequest/Response
- ExperimentCreateRequest/Response
- ExperimentResultsResponse

### 4. LLM Abstraction Layer
Create `app/llm/client.py`:
- Thin wrapper around LiteLLM
- Support model swapping via config
- Retry logic (max 3)
- JSON validation on responses
- Logging to Langfuse
- NOT an agent framework — just a clean function: `async def generate(prompt, system, temperature, response_format) -> dict`

### 5. Prompt File Structure
Create placeholder .txt files in /prompts/:
- interviewer_question.txt
- module_completion.txt
- profile_extraction.txt
- twin_response.txt
- experiment_response.txt
- transcript_correction.txt
- answer_parser.txt

### 6. Alembic Migrations
Set up Alembic with async support. Create initial migration for ALL tables.

### 7. Frontend Foundation
Set up the Next.js app with:
- Tailwind config using the Darpan Labs theme:
  - Dark mode only
  - Colors: bg-primary (#0A0A0A), accent-lime (#C8FF00), accent-cyan (#00D4FF)
  - Font: Inter (install via next/font)
- Global layout with dark background
- API client utility (fetch wrapper with auth headers)
- Basic auth placeholder (Supabase/Clerk skeleton)

### 8. Docker Compose
Postgres (pgvector), Redis, backend, frontend, Celery worker.

### 9. Seed Data
Create seed_data/question_banks/ with JSON files:
- M1_core_identity.json (15 questions mapped to signals)
- M2_decision_logic.json (15 questions)
- M3_preferences_values.json (15 questions)
- M4_communication_social.json (15 questions)

Each question format:
{
  "question_id": "M1_q01",
  "question_text": "Can you tell me about what you do and what a typical week looks like for you?",
  "question_type": "open_text",  // open_text, forced_choice, scenario, trade_off, likert
  "target_signals": ["occupation_lifestyle_overview"],
  "follow_up_triggers": ["vague_answer", "single_word"],
  "priority": 1,
  "estimated_seconds": 30
}

## Tests (write these FIRST)
```
test_database_connection()
test_all_tables_created()
test_pydantic_models_validate()
test_llm_client_retry_on_failure()
test_llm_client_json_validation()
test_health_check_endpoint()
test_question_bank_loads_correctly()
test_question_bank_covers_all_signals()
```

## Constraints
- Python 3.11+, FastAPI, Pydantic v2
- Next.js 14+, TypeScript, Tailwind
- Postgres + pgvector
- Write tests first, then implementation
- Keep prompts in /prompts/ directory as .txt files, not hardcoded
- No per-user fine-tuning — ICL only
- All timestamps in UTC
- UUIDs for all primary keys
```

---

## Phase 1: Text Interview + Modules (Weeks 2-3) — 2 Claude Code Sessions

### Session P1a: Static Interview + Module State Machine (Week 2)

```
You are building Phase 1a (Static Interview + Module State) of the Darpan Labs Digital Twin platform.

## Context
This is a voice-first AI interviewer that builds digital twins of consumers. Phase 0 created the foundation (DB, schemas, project structure). Now we build the interview engine — TEXT FIRST. All logic here will be reused when voice is added later. Voice is just a transport layer on top of this.

The interview has a modular architecture:
- 4 mandatory modules (M1-M4, ~12 min total) → produces a "Base Twin"
- 4+ add-on modules (A1-A6) → improves twin fidelity
- Multi-session: users can complete modules across different sessions/days

## Existing Code
Reference the P0 codebase:
- SQLAlchemy models in app/models/
- Pydantic schemas in app/schemas/
- Question banks in seed_data/question_banks/
- LLM client in app/llm/client.py

## Task
Build the complete text-based interview system with static question sequencing.

### Backend APIs:

1. POST /api/v1/interviews/start
   - Create session, initialize module plan (M1→M2→M3→M4)
   - Return first question from M1
   - Request body: { user_id, modules_to_complete: ["M1","M2","M3","M4"], sensitivity_settings }
   - Response: { session_id, status, first_module, module_plan, first_question }

2. POST /api/v1/interviews/{session_id}/answer
   - Accept text answer, persist as interview_turn
   - Return ack with answer metadata
   - Request: { answer_text, question_id }
   - Response: { turn_id, answer_received: true }

3. POST /api/v1/interviews/{session_id}/next-question
   - Static sequencing: pick next question from question bank for current module
   - Track module state: update question_count, mark signals_captured
   - If module complete (all priority-1 questions asked OR question_count >= max) → transition to next module
   - If all modules done → return { status: "all_modules_complete" }
   - Response: { question_id, question_text, question_type, module_id, module_progress }

4. GET /api/v1/interviews/{session_id}/status
   - Return full session state: completed modules, current module, progress per module

5. POST /api/v1/interviews/{session_id}/skip
   - Skip current question, record reason
   - Response: next question

6. POST /api/v1/interviews/{session_id}/pause
   - Pause session, persist state

7. POST /api/v1/interviews/{session_id}/resume
   - Resume from last incomplete module, exact turn

### Module State Engine (app/services/module_engine.py):
- Per-module tracking: coverage_score, confidence_score, signals_captured
- Module transitions: when current module done, auto-advance
- Static completion criteria: question_count >= required minimum per module
- Session persistence: state saved after EVERY turn

### Frontend (Interview UI):
- Single-question-per-screen flow
- Text input field
- Progress bar showing modules (M1 ████░░ M2 ░░░░ M3 ░░░░ M4 ░░░░)
- Current module name + description
- Skip button
- Pause/Resume button
- Module transition animation (show brief summary between modules)

IMPORTANT THEME: Use the Darpan Labs dark theme:
- Background: #0A0A0A
- Cards: #111111 with #2A2A2A borders
- Progress: gradient #C8FF00 → #00D4FF
- Primary button: bg-[#C8FF00] text-black
- Text: white headings, #A0A0A0 body
- Font: Inter

## Tests (write FIRST)
```
test_start_interview_creates_session()
test_start_interview_returns_first_question()
test_submit_answer_persists_turn()
test_next_question_returns_from_correct_module()
test_module_transitions_when_complete()
test_all_modules_complete_returns_status()
test_skip_question_records_reason()
test_pause_persists_state()
test_resume_continues_from_correct_turn()
test_session_state_survives_reconnect()
test_no_duplicate_questions_within_module()
```

## Constraints
- Python 3.11+, FastAPI, Pydantic v2
- Next.js 14+, TypeScript, Tailwind (dark theme)
- Postgres + pgvector
- Write tests first, then implementation
- No LLM calls yet — pure static sequencing
- State saved after every single turn (crash-safe)
```

### Session P1b: Adaptive Questioning + Follow-ups (Week 3)

```
You are building Phase 1b (Adaptive Questioning) of the Darpan Labs Digital Twin platform.

## Context
Phase 1a built static text interviews with module state tracking. Now we add LLM-powered adaptive questioning: the AI interviewer generates contextual follow-ups, evaluates answer quality, and determines module completion dynamically.

## Existing Code
- Interview APIs: POST /start, /answer, /next-question, /skip, /pause, /resume
- Module state engine in app/services/module_engine.py
- Question banks in seed_data/
- LLM client in app/llm/client.py

## Task
Replace static question sequencing with LLM-powered adaptive logic.

### 1. Answer Parser (app/services/answer_parser.py)
After each user answer, run LLM analysis:
- Extract: specificity score (0-1), conditions/rules mentioned, contradiction signals, sentiment
- Determine if follow-up needed: vague answer, single word, contradiction, high-leverage topic
- Output structured JSON

Implement this prompt in prompts/answer_parser.txt:
```
SYSTEM: You are analyzing a user's answer in a digital twin interview.
DEVELOPER:
Module: {module_id} - {module_name}
Question asked: {question_text}
Target signal: {target_signal}
User's answer: {answer_text}
Previous answers in this module: {previous_answers}

TASK: Analyze the answer quality and extract signals.
OUTPUT JSON:
{
  "specificity_score": 0.0-1.0,
  "signals_extracted": [{"signal": "string", "value": "string", "confidence": 0.0}],
  "behavioral_rules": [{"rule": "if X then Y", "confidence": 0.0}],
  "needs_followup": true|false,
  "followup_reason": "vague|contradiction|high_leverage|null",
  "sentiment": "positive|neutral|negative|mixed"
}
```

### 2. Coverage/Confidence Scorer (app/services/scoring.py)
Update module coverage and confidence after each parsed answer:
- coverage_score: proportion of target signals captured
- confidence_score: average confidence across captured signals
- Both updated in interview_modules table

### 3. Adaptive Question Planner (app/services/question_planner.py)
Replace static sequencing with LLM-based question selection.

Implement prompts/interviewer_question.txt:
```
SYSTEM: You are a friendly, adaptive interviewer building a digital twin.
You are conducting module: {module_name}
Module goal: {module_goal}
Target signals: {signal_targets}

RULES:
1. Ask ONE question per turn. Keep it conversational.
2. Questions should be short (under 30 words).
3. Avoid jargon. This is a conversation, not a survey.
4. Ask follow-ups only when answer is vague or ambiguous.
5. Do not repeat questions already answered.
6. Respect sensitivity settings: {sensitivity_settings}

DEVELOPER:
Module status: {questions_asked}/{max_questions}, coverage={coverage}, confidence={confidence}
Signals captured: {captured_signals}
Signals still needed: {missing_signals}
Recent conversation:
{recent_turns}

TASK: Generate the next interview question.
OUTPUT JSON:
{
  "question_text": "string",
  "question_type": "open_text|forced_choice|scenario|trade_off",
  "target_signal": "string",
  "rationale": "why this question now",
  "is_followup": true|false,
  "parent_question_id": "string|null"
}
```

### 4. Module Completion Evaluator (app/services/module_evaluator.py)
LLM evaluates whether module criteria are met.

Implement prompts/module_completion.txt:
```
SYSTEM: You are evaluating whether an interview module is complete.
DEVELOPER:
Module: {module_id} - {module_name}
Required signals: {signal_targets}
Completion criteria: coverage >= {coverage_threshold}, confidence >= {confidence_threshold}
Questions and answers so far: {module_turns}

TASK: Evaluate module completion.
OUTPUT JSON:
{
  "module_id": "M2",
  "is_complete": true|false,
  "coverage_score": 0.0,
  "confidence_score": 0.0,
  "signals_captured": ["signal1", "signal2"],
  "signals_missing": ["signal3"],
  "behavioral_rules_extracted": [{"rule": "string", "confidence": 0.0}],
  "recommendation": "COMPLETE|ASK_MORE|SKIP_OPTIONAL",
  "suggested_next_questions": []
}
```

Module completion thresholds:
- M1: coverage ≥ 0.70, confidence ≥ 0.65, min 4 questions
- M2: coverage ≥ 0.75, confidence ≥ 0.70, min 2 behavioral rules
- M3: coverage ≥ 0.75, confidence ≥ 0.70, min 3 preference dimensions
- M4: coverage ≥ 0.70, confidence ≥ 0.65, min 4 questions

### 5. Recap/Confirmation
At module end, generate a brief summary: "I heard that you tend to... Is that right?"
If user corrects, update signals. Then transition to next module.

### 6. Multi-Session Resume
User can close mid-M2, return next day, continue from exact turn. Module state + all turns persisted.

### 7. Updated Frontend
- Show real-time module progress with coverage bar
- Display "Thinking..." while LLM generates next question
- Show module completion summary with smooth transition
- Add recap confirmation step between modules

## Tests (write FIRST)
```
test_answer_parser_extracts_signals()
test_answer_parser_detects_vague_answer()
test_coverage_score_updates_after_answer()
test_adaptive_question_targets_missing_signals()
test_no_repeated_questions()
test_followup_generated_for_vague_answer()
test_module_completion_evaluator_correct()
test_module_transitions_on_criteria_met()
test_multi_session_resume_from_exact_turn()
test_recap_generated_at_module_end()
test_stopping_heuristic_fires_correctly()
```

## Constraints
- Python 3.11+, FastAPI, Pydantic v2
- Write tests first, then implementation
- Keep ALL prompts in /prompts/ as .txt files
- LLM calls use the abstraction layer from P0
- JSON validation + retry (max 3) on all LLM outputs
- No per-user fine-tuning — ICL only
```

---

## Phase 2: Twin Generation + Chat (Weeks 3.5-5) — 2 Claude Code Sessions

### Session P2a: Twin Generation Pipeline (Week 3.5-4)

```
You are building Phase 2a (Twin Generation Pipeline) of the Darpan Labs Digital Twin platform.

## Context
Phase 1 built the complete text-based adaptive interview with modular architecture. When a user completes mandatory modules M1-M4, we now need to generate their digital twin. The twin is built via ICL (in-context learning) — no fine-tuning. Each completed module improves the twin.

Twin quality progression:
- M1-M4 only → Base Twin (~55-65% fidelity)
- + 1-2 add-ons → Enhanced Twin (~65-75%)
- + 3-4 add-ons → Rich Twin (~75-85%)
- All modules → Full Twin (~80-90%)

## Existing Code
- Complete interview system (text-based, adaptive)
- All DB models including twin_profiles, evidence_snippets
- LLM client with retry + JSON validation

## Task
Build the twin generation pipeline: interview data → structured profile → persona summary → evidence index → versioned twin.

### 1. Profile Extraction (app/services/profile_builder.py)
Takes all completed module transcripts and generates structured profile.

Implement prompts/profile_extraction.txt:
```
SYSTEM: You are extracting a structured personality/behavioral profile from interview transcripts to create a digital twin.

DEVELOPER:
Completed modules: {completed_modules}
All interview turns (by module):
{all_module_turns}

TASK: Extract a comprehensive structured profile.
OUTPUT JSON:
{
  "demographics": {
    "age_band": "string",
    "occupation_type": "string",
    "living_context": "string",
    "life_stage": "string"
  },
  "personality": {
    "self_description": "string",
    "ocean_estimates": {
      "openness": {"score": 0.0, "confidence": 0.0, "evidence": "string"},
      "conscientiousness": {"score": 0.0, "confidence": 0.0, "evidence": "string"},
      "extraversion": {"score": 0.0, "confidence": 0.0, "evidence": "string"},
      "agreeableness": {"score": 0.0, "confidence": 0.0, "evidence": "string"},
      "neuroticism": {"score": 0.0, "confidence": 0.0, "evidence": "string"}
    }
  },
  "decision_making": {
    "speed_vs_deliberation": "string",
    "gut_vs_data": "string",
    "risk_appetite": "string",
    "behavioral_rules": [{"rule": "string", "confidence": 0.0}]
  },
  "preferences": {
    "dimensions": [
      {"axis": "control_vs_convenience", "leaning": "string", "strength": 0.0},
      {"axis": "price_vs_quality", "leaning": "string", "strength": 0.0}
    ]
  },
  "communication": {
    "directness": "string",
    "conflict_style": "string",
    "social_energy": "string"
  },
  "domain_specific": {},
  "uncertainty_flags": ["domains where data is missing"]
}
```

### 2. Persona Summary Generator (app/services/persona_generator.py)
Generate a ≤2500 token natural language summary from structured profile. This is the "prompt payload" that represents the twin in all downstream interactions.

### 3. Evidence Chunking + Embeddings (app/services/evidence_indexer.py)
- Chunk interview answers into evidence snippets
- Each snippet: text, category (personality/preference/behavior/context), module_id, turn_id
- Generate embeddings via OpenAI/provider API
- Store in pgvector for semantic retrieval

### 4. Twin Versioning
- Create immutable twin version on generation
- Track modules_included, quality_label, quality_score
- quality_label logic:
  - modules_included has M1-M4 only → "base"
  - + 1-2 add-ons → "enhanced"
  - + 3-4 add-ons → "rich"
  - all modules → "full"
- quality_score = weighted average of module coverage scores

### 5. Incremental Regeneration
When add-on module completes → automatically regenerate twin with expanded data → new version number.

### 6. JSON Validation + Retry
All LLM outputs validated against Pydantic schemas. Bounded retry (max 3) on schema failures.

### 7. APIs
- POST /api/v1/interviews/{session_id}/generate-twin
  - Trigger: mandatory modules complete
  - Request: { trigger: "mandatory_modules_complete", modules_to_include: ["M1","M2","M3","M4"] }
  - Response: { job_id, status: "queued", expected_completion_sec, twin_version, quality_label }

- GET /api/v1/twins/{twin_id}
  - Returns full profile with coverage map, quality badge, persona summary

- GET /api/v1/twins/{twin_id}/versions
  - Returns version history

### 8. Twin Profile UI (Frontend)
- Summary card with persona text
- Per-module confidence bars (colored: high=green, med=amber, low=red)
- Uncertainty gaps highlighted
- Quality badge (base/enhanced/rich/full) with glow effect
- "Improve Twin" CTA → lists available add-on modules with estimated improvement
- Version history toggle

Use Darpan theme: dark cards (#111111), lime accent (#C8FF00) for quality badge, cyan (#00D4FF) for CTAs.

## Tests (write FIRST)
```
test_profile_extraction_from_module_transcripts()
test_persona_summary_under_2500_tokens()
test_evidence_chunking_correct()
test_evidence_embeddings_stored_in_pgvector()
test_twin_version_created_correctly()
test_quality_label_base_for_mandatory_only()
test_quality_label_enhanced_with_addon()
test_incremental_regeneration_on_addon_complete()
test_json_validation_retry_on_malformed_output()
test_twin_profile_api_returns_coverage_map()
```

## Constraints
- Python 3.11+, FastAPI, Pydantic v2
- Write tests first, then implementation
- Keep ALL prompts in /prompts/ as .txt files
- Twin generation runs as async Celery task
- Persona summary MUST be ≤ 2500 tokens
- No per-user fine-tuning — ICL only
```

### Session P2b: Twin Chat (Weeks 4-5)

```
You are building Phase 2b (Twin Chat Interface) of the Darpan Labs Digital Twin platform.

## Context
Phase 2a built the twin generation pipeline. Users now have versioned digital twins with structured profiles, persona summaries, and evidence snippets in pgvector. Now we build the chat interface: users ask questions → twin responds in-persona with confidence + evidence grounding.

## Existing Code
- Twin profiles with persona_summary_text and structured_profile_json
- Evidence snippets with embeddings in pgvector
- LLM client with retry + JSON validation

## Task
Build the complete twin chat experience with confidence scoring and evidence grounding.

### 1. Evidence Retrieval (app/services/evidence_retriever.py)
- Semantic search over evidence snippets using pgvector
- Top-k (k=5) by relevance with category diversity (don't return 5 personality snippets if question is about behavior)
- Filter by twin's modules_included

### 2. Twin Response Generation
Implement prompts/twin_response.txt:
```
SYSTEM: You are simulating how a specific person would respond.
You must answer AS this person, based on their profile and evidence.

RULES:
1. Stay consistent with persona's stated preferences, values, and behavioral rules.
2. Ground your answer in evidence from their interview.
3. If profile lacks data for this question, say so with low confidence.
4. Do not invent traits not supported by evidence.
5. Answer in first person, naturally.
6. Be specific — avoid generic responses.

DEVELOPER:
Persona Profile:
{persona_summary_text}

Relevant Evidence:
{retrieved_evidence}

Completed modules: {modules_included}
Modules NOT completed: {missing_modules}

Chat history (this session):
{chat_history}

USER QUESTION:
{user_question}

OUTPUT JSON:
{
  "response_text": "first-person response",
  "confidence_score": 0.0-1.0,
  "confidence_label": "low|medium|high",
  "uncertainty_reason": "string or null",
  "evidence_used": [{"snippet_id": "string", "why": "string"}],
  "coverage_gaps": ["missing module domains"],
  "suggested_module": "A2|null (complete this to improve answer)"
}
```

### 3. Confidence Scoring Logic
- HIGH (0.75-1.0): Question domain fully covered by completed modules, multiple evidence snippets support answer
- MEDIUM (0.5-0.74): Partial coverage, some inference needed
- LOW (0.0-0.49): Question domain not covered by any completed module, high uncertainty

### 4. Module-Aware Suggestions
When confidence is low due to missing module: "Complete module A2 (Spending Behavior) to improve this answer."

### 5. APIs
- POST /api/v1/twins/{twin_id}/chat
  - Request: { message, session_id (optional — creates new if absent) }
  - Response: { response_text, confidence_score, confidence_label, evidence_used, coverage_gaps, suggested_module, session_id }

- GET /api/v1/twins/{twin_id}/chat/{session_id}/history
  - Returns all messages in session

### 6. Chat UI (Frontend)
Build a beautiful chat interface:
- Left panel: twin profile card (name, quality badge, module coverage)
- Right/main panel: chat messages
- Twin messages show:
  - Response text
  - Confidence badge (colored: high=#00FF88, med=#FFB800, low=#FF4444)
  - Expandable evidence section (click to see supporting snippets)
  - "Improve this answer" suggestion when relevant
- User input: text field with send button
- Streaming response (show tokens as they arrive)

Darpan theme:
- Chat background: #0A0A0A
- User message bubbles: #1A1A1A with #2A2A2A border
- Twin message bubbles: #111111 with subtle #C8FF00 left border
- Confidence badge: pill-shaped, color-coded
- Evidence expandable: accordion with #1A1A1A bg
- Input: dark field with #2A2A2A border, #C8FF00 send button

## Tests (write FIRST)
```
test_evidence_retrieval_returns_relevant_snippets()
test_evidence_retrieval_category_diversity()
test_twin_response_in_persona()
test_confidence_score_high_for_covered_topics()
test_confidence_score_low_for_uncovered_topics()
test_twin_response_includes_evidence_ids()
test_chat_session_maintains_context()
test_module_suggestion_when_low_confidence()
test_json_validation_retry_on_malformed_output()
test_streaming_response_works()
```

## Constraints
- Python 3.11+, FastAPI, Pydantic v2
- Next.js 14+, TypeScript, Tailwind (dark theme)
- Write tests first, then implementation
- Streaming via SSE for chat responses
- Chat session context limited to current window (no long-term memory)
- Evidence retrieval must complete in <500ms
```

---

## Phase 3: Voice Pipeline (Weeks 3.5-5, parallel with P2) — 2 Claude Code Sessions

### Session P3a: Voice Infrastructure (Week 3.5-4)

```
You are building Phase 3a (Voice Infrastructure) of the Darpan Labs Digital Twin platform.

## Context
Phase 1 built the complete text-based adaptive interview. Voice is a TRANSPORT LAYER on top of the existing interview logic. The pipeline: User speaks → ASR transcribes → existing answer processing pipeline → TTS generates voice response → user hears next question.

## Existing Code
- Complete text interview system (adaptive questions, module state, coverage scoring)
- All APIs: /start, /answer, /next-question, module engine, etc.
- Frontend interview UI (text mode)

## Task
Build the voice pipeline infrastructure.

### 1. WebSocket Endpoint
Create wss://api/ws/interview/{session_id} for bidirectional audio/text.

Client → Server messages:
- { type: "audio_chunk", data: "<base64_pcm>", seq: 1 }
- { type: "end_of_speech", reason: "user_silence" }
- { type: "interrupt", reason: "user_started_speaking" }
- { type: "switch_to_text", text: "I prefer typing" }

Server → Client messages:
- { type: "partial_transcript", text: "...", confidence: 0.7 }
- { type: "final_transcript", text: "...", language: "EN", confidence: 0.95 }
- { type: "tts_audio_chunk", data: "<base64_audio>", seq: 1 }
- { type: "tts_complete", question_text: "..." }
- { type: "module_progress", module_id: "M2", coverage: 0.65, confidence: 0.58 }
- { type: "module_complete", module_id: "M2", summary: "..." }
- { type: "system_message", text: "Switching to next module..." }

### 2. Voice Orchestrator (app/services/voice_orchestrator.py)
Manages the full voice pipeline per session:
- Receives audio chunks from WebSocket
- Sends to ASR (Deepgram streaming API primary, Whisper fallback)
- Gets transcript back
- Feeds into EXISTING answer processing pipeline (answer_parser → scoring → question_planner)
- Generates next question text
- Sends to TTS (ElevenLabs or Azure Neural TTS)
- Streams audio back to client

### 3. ASR Integration (app/services/asr.py)
- Deepgram streaming API (primary): real-time partial + final transcripts
- Hindi/Hinglish support: language=None for auto-detection
- Fallback: Whisper API (batch mode)
- Store raw transcript + corrected transcript + language tag

### 4. TTS Integration (app/services/tts.py)
- ElevenLabs API or Azure Neural TTS
- Hindi + English voices
- Streamed audio chunks
- SSML with language tags for bilingual responses
- 24h TTL cache for repeated questions

### 5. Turn-Taking Logic (VAD)
| Scenario | Detection | System Behavior |
|----------|-----------|-----------------|
| User finishes speaking | VAD silence > 1.5s | Finalize transcript → process → respond |
| User pauses mid-thought | VAD silence 0.5-1.5s | Wait, show "listening..." |
| User interrupts system | Speech during TTS | Stop TTS immediately, start new ASR |
| Extended silence (>8s) | No speech after question | Gentle prompt: "Take your time..." |
| Extended silence (>20s) | No interaction | "Would you like to continue?" |
| Background noise | VAD false positives | Require min speech >0.3s |

### 6. Audio Storage
- Raw audio chunks → S3 with 7-day TTL
- Audio metadata → Postgres (duration_ms, sample_rate, vad_events, asr_confidence)
- Corrected transcript → Postgres (permanent, matches user retention)

### 7. Voice Interview UI (Frontend)
Replace/enhance the text interview UI:
- Mic permission request with clear explanation
- Waveform / "listening" indicator (animated #C8FF00 bars on #1A1A1A background)
- Real-time partial transcript (faded text, updates as user speaks)
- Final transcript (solid text after processing)
- Module progress indicator
- "Switch to text" button (always visible)
- "Pause and resume later" button
- Mute/unmute toggle
- Language indicator (EN/HI/HG detected)

Darpan theme for voice UI:
- Waveform: #C8FF00 animated bars, pulsing glow when listening
- "Listening..." state: subtle #C8FF00 ring around mic icon
- "Processing..." state: #00D4FF spinner
- "Speaking..." state: #C8FF00 pulse on speaker icon

### 8. Text Fallback
If voice fails (mic denied, 3 consecutive ASR failures, user clicks "Switch to text"):
- UI transitions to text input mode seamlessly
- Module state preserved, progress continues
- Transcript stored as text-typed (no audio metadata)

## Tests (write FIRST)
```
test_websocket_connection_established()
test_audio_chunk_received_and_processed()
test_asr_returns_transcript()
test_tts_generates_audio()
test_turn_taking_silence_detection()
test_turn_taking_interruption_stops_tts()
test_text_fallback_preserves_module_state()
test_audio_stored_with_metadata()
test_audio_ttl_cleanup()
test_voice_answer_feeds_into_same_pipeline_as_text()
```

## Constraints
- Python 3.11+, FastAPI, WebSocket
- Audio format: 16kHz mono PCM
- ASR latency target: p50 < 1.5s, p95 < 3s
- TTS first byte target: p50 < 800ms, p95 < 2s
- End-to-end turn latency: p50 < 4s, p95 < 8s
- Write tests first, then implementation
```

### Session P3b: Bilingual + Integration (Weeks 4-5)

```
You are building Phase 3b (Bilingual Support + Voice Integration) of the Darpan Labs Digital Twin platform.

## Context
Phase 3a built the voice infrastructure (WebSocket, ASR, TTS, turn-taking). Now we add Hindi/Hinglish support and fully integrate voice with the interview logic from Phase 1.

## Existing Code
- Voice pipeline: WebSocket, ASR (Deepgram), TTS (ElevenLabs), VAD
- Complete adaptive interview system (Phase 1)
- Twin generation + chat (Phase 2)

## Task

### 1. Hindi/Hinglish ASR
- Whisper large-v3 with language=None for auto-detection per utterance
- Validate on Hindi and Hinglish test inputs
- Handle Romanized Hindi (e.g., "mujhe lagta hai")

### 2. Transcript Correction (app/services/transcript_corrector.py)
Post-ASR LLM pass to fix common errors.

Implement prompts/transcript_correction.txt:
```
SYSTEM: You are correcting an ASR transcript from a voice interview. The speaker may use English, Hindi, or code-switched Hinglish.

INPUT:
Raw ASR transcript: {raw_transcript}
ASR confidence: {confidence}
Detected language: {detected_language}
Previous turns context: {recent_turns}

TASK: Correct errors and tag language segments.
OUTPUT JSON:
{
  "corrected_transcript": "string",
  "language_tags": [{"start": 0, "end": 24, "lang": "EN"}, ...],
  "primary_language": "EN|HI|HG",
  "correction_applied": true|false,
  "corrections": [{"original": "...", "corrected": "...", "reason": "..."}]
}
```

### 3. Integration with Interview Logic
- Voice transcripts feed into the SAME answer processing pipeline from Phase 1
- input_mode = "voice" flagged on turns
- answer_text = corrected transcript
- answer_raw_transcript = raw ASR output

### 4. Bilingual TTS
- Detect primary language of generated response
- Use appropriate voice model (English voice / Hindi voice)
- For Hinglish: use Hindi voice with English pronunciation capability

### 5. Real-time Transcript Display (Frontend)
- Show partial transcript (faded, updating) while user speaks
- Show final corrected transcript (solid) after processing
- Optional: "Did I hear that right?" correction button

### 6. End-to-end Voice Interview Test
Complete M1-M4 via voice → generates base twin → chat with twin. Full loop.

## Tests (write FIRST)
```
test_hindi_asr_transcription()
test_hinglish_code_switching()
test_transcript_correction_fixes_common_errors()
test_language_detection_tags_correctly()
test_voice_answer_feeds_into_same_pipeline_as_text()
test_bilingual_tts_selects_correct_voice()
test_full_voice_interview_m1_to_m4()
test_text_fallback_mid_voice_session()
test_partial_transcript_displayed_realtime()
```

## Constraints
- Hindi ASR WER target: < 15%
- Hinglish ASR WER target: < 20%
- Transcript correction accuracy: > 90% on flagged corrections
- Write tests first, then implementation
```

---

## Phase 4: Experiments + Add-ons + Polish (Weeks 5.5-7) — 2 Claude Code Sessions

### Session P4a: Experiment Engine (Weeks 5.5-6)

```
You are building Phase 4a (Experiment Engine) of the Darpan Labs Digital Twin platform.

## Context
Phases 1-3 built: voice interviews → modular data collection → twin generation → twin chat. Now we build the experiment engine: users can run scenarios/questions against COHORTS of digital twins and inspect individual + aggregate results. This is the killer feature for B2B firms.

## Existing Code
- Complete twin profiles with structured data + evidence in pgvector
- Twin chat working with confidence + evidence
- All DB models: cohorts, experiments, experiment_results tables

## Task
Build the complete experiment engine.

### 1. Cohort CRUD (app/routers/cohorts.py)
- POST /api/v1/cohorts — create cohort from twin IDs + quality filters
  - Request: { name, twin_ids: [], filters: { min_quality, required_modules } }
  - Validate: all twin IDs exist, meet quality/module criteria
  - MVP limit: 50 twins per cohort

- GET /api/v1/cohorts — list user's cohorts
- GET /api/v1/cohorts/{id} — cohort details with twin summaries

### 2. Experiment Definition
- POST /api/v1/experiments
  - Request: { name, cohort_id, scenario: { type, prompt, options, context }, settings: { temperature: 0.2, max_tokens: 500 } }
  - Supported types: forced_choice, likert_scale, open_scenario, preference_rank
  - Status: pending → running → completed/failed

### 3. Experiment Execution Engine (app/workers/experiment_runner.py)
Celery worker that:
1. Loads experiment + cohort
2. For each twin in cohort (PARALLEL via Celery group):
   a. Load twin profile + evidence
   b. Compose prompt using prompts/experiment_response.txt
   c. Generate response (ICL, low temperature=0.2)
   d. Validate response JSON schema
   e. Store individual result in experiment_results
3. After all twins respond:
   a. Compute aggregate: choice distribution, confidence distribution
   b. Detect patterns/clusters
   c. Identify dominant reasoning themes
4. Update experiment status + aggregate_results

Implement prompts/experiment_response.txt:
```
SYSTEM: You are simulating how a specific person would respond to a scenario.
You must answer AS this person, based on their profile and evidence.

RULES:
1. Stay consistent with persona's stated preferences, values, behavioral rules.
2. Ground answer in evidence from their interview.
3. If profile lacks data, say so with low confidence.
4. Do not invent traits not supported by evidence.
5. Answer in first person, naturally.
6. Be specific — avoid generic responses.

DEVELOPER:
Experiment type: {experiment_type}
Persona Profile: {persona_summary_text}
Relevant Evidence: {retrieved_evidence}
Completed modules: {modules_included}

SCENARIO:
{experiment_prompt}

OPTIONS (if applicable):
{options}

OUTPUT JSON:
{
  "choice": "string or null",
  "choice_index": 0,
  "reasoning": "first-person, 50-150 words",
  "confidence_score": 0.0,
  "confidence_label": "low|medium|high",
  "uncertainty_reason": "string or null",
  "evidence_used": [{"snippet_id": "string", "why": "string"}],
  "coverage_gaps": ["string"]
}
```

### 4. Aggregate Result Computation (app/services/experiment_aggregator.py)
After all individual results:
- choice_distribution: { "Option A": { count, percentage }, ... }
- confidence_distribution: { high: N, medium: N, low: N }
- key_patterns: LLM-identified patterns (e.g., "Twins with high risk tolerance preferred X")
- dominant_reasoning_themes: most common reasoning mentions

### 5. Result APIs
- GET /api/v1/experiments/{id}/results
  - Full result schema with aggregate + individual results
- GET /api/v1/experiments/{id}/results/{twin_id}
  - Individual twin result detail

### 6. Experiment UI (Frontend)
Three-panel layout:

Setup panel:
- Cohort builder: select twins, filter by quality/modules
- Scenario editor: type selector + prompt textarea + options builder
- "Launch Experiment" button

Running state:
- Progress bar: "5/12 twins complete"
- Animated twin cards flipping to "done"

Results dashboard:
- Aggregate chart: bar chart for forced_choice, distribution for likert
- Key patterns panel: LLM-identified insights with supporting twin count
- Dominant themes: pill badges
- Individual twin cards (expandable):
  - Twin name + quality badge
  - Choice + reasoning
  - Confidence badge
  - Evidence used (expandable)
- MANDATORY: Limitations disclaimer on every result view
  "These results are simulated approximations based on digital twin profiles. They are not statistically validated research findings."
- Export: JSON/CSV download
- "Run again with modifications" button

Darpan theme:
- Chart colors: #C8FF00 for Option A, #00D4FF for Option B, #FFB800 for Option C
- Pattern cards: #111111 bg, left accent border color-coded
- Twin result cards: #111111, expandable accordion
- Disclaimer: #1A1A1A bg, #FFB800 warning icon, #A0A0A0 text

## Tests (write FIRST)
```
test_cohort_creation_with_quality_filter()
test_cohort_rejects_invalid_twin_ids()
test_experiment_creation_validates_schema()
test_experiment_execution_parallel()
test_individual_result_has_reasoning_and_evidence()
test_aggregate_choice_distribution_correct()
test_aggregate_confidence_distribution()
test_pattern_detection_produces_insights()
test_experiment_handles_twin_failure_gracefully()
test_max_cohort_size_enforced()
test_disclaimer_present_in_results()
```

## Constraints
- Celery workers for parallel execution
- Max 50 twins per experiment (MVP)
- temperature=0.2 for deterministic responses
- Target: <5s per twin, <45s total for 50 twins
- Target cost: <$3.00 per 50-twin experiment
- Mandatory disclaimer on ALL result views
- Write tests first, then implementation
```

### Session P4b: Add-on Modules + Polish + Demo (Weeks 6-7)

```
You are building Phase 4b (Add-ons + Polish + Demo Readiness) of the Darpan Labs Digital Twin platform.

## Context
All core features are built. Now: add-on module question banks, holdout evaluation, UI polish, and demo hardening.

## Existing Code
- Complete platform: voice interviews → modules → twin generation → chat → experiments
- All P0-P4a code

## Task

### 1. Add-on Module Question Banks
Create seed_data/question_banks/ for:

A1: Lifestyle & Routines (3-4 min)
- 15-20 questions targeting: daily routines, fitness habits, social life, entertainment preferences
- Improvement to twin: +8-12% fidelity on lifestyle behavior questions

A2: Spending & Financial Behavior (3-4 min)
- 15-20 questions targeting: budget consciousness, impulse vs planned purchasing, brand loyalty, price sensitivity
- Improvement: +10-15% fidelity on purchase/spending questions

A3: Career & Growth Aspirations (3-4 min)
- 15-20 questions targeting: career goals, learning preferences, ambition level, work-life priorities
- Improvement: +8-12% fidelity on professional behavior questions

A4: Work & Learning Style (3-4 min)
- 15-20 questions targeting: solo vs collaborative, feedback response, structured vs flexible, ambiguity tolerance
- Improvement: +8-12% fidelity on work behavior questions

Each follows same format as mandatory modules. Same adaptive logic applies.

### 2. Add-on Module Flow
- User goes to twin profile → "Improve Twin" CTA
- Available modules listed with estimated improvement percentage
- Complete add-on → triggers twin regeneration → new version with updated quality
- Quality label upgrades: base → enhanced → rich → full

### 3. Holdout Evaluation Mode (app/services/holdout_evaluator.py)
- Reserve 8-12 benchmark questions per domain
- After twin generation, ask twin the holdout questions
- Compare twin answers with real user answers (if available)
- Calculate agreement rate → this is the fidelity estimate
- Store in twin_profiles.extraction_meta

### 4. Dashboard / Landing Page (Frontend)
After login, users see:
- Twin card: quality badge, modules completed, coverage visualization
- Quick actions: "Chat with Twin", "Run Experiment", "Improve Twin"
- Recent experiments list
- Twin version history

### 5. UI Polish
- Loading states: skeleton screens with #1A1A1A shimmer
- Error states: friendly messages with retry buttons
- Empty states: helpful CTAs
- Transitions: smooth module transitions, twin generation loading animation
- Mobile responsive: interview works on mobile
- Micro-interactions: completion celebrations (confetti with #C8FF00 and #00D4FF particles)

### 6. Demo Hardening
- Create 3 demo twin profiles with pre-filled data (no interview needed)
- Pre-built demo experiment with results
- "Try Demo" flow that showcases: twin chat + experiment in 2 minutes
- Error handling: graceful degradation if LLM/ASR/TTS goes down

### 7. Observability
- Sentry error tracking on backend
- PostHog product analytics on frontend
- Langfuse LLM trace logging
- Cost tracking per session/experiment

### 8. Data Cleanup
- User deletion: cascade delete all data (sessions, turns, twins, audio, experiments)
- Session deletion: remove audio + transcripts
- Audio TTL: 7-day auto-purge via Celery beat

## Tests (write FIRST)
```
test_addon_module_question_banks_load()
test_addon_module_triggers_twin_regeneration()
test_twin_quality_upgrades_after_addon()
test_holdout_eval_compares_twin_vs_real()
test_delete_twin_removes_all_data()
test_delete_session_removes_audio()
test_demo_twins_accessible()
test_demo_experiment_runs()
test_audio_ttl_cleanup_works()
test_full_e2e_voice_interview_to_experiment()
```

## Constraints
- Write tests first, then implementation
- Demo must work offline (pre-cached LLM responses for demo twins)
- All animations at 60fps
- Mobile-first responsive design
- Audio auto-purge via Celery beat scheduled task
```

---

## Phase Dependency Graph

```
P0 (Foundation) — Week 1
│
▼
P1a (Static Interview) — Week 2
│
▼
P1b (Adaptive Interview) — Week 3
│
├────────────────┐
▼                ▼
P2a (Twin Gen)   P3a (Voice Infra)     ← PARALLEL if 2 engineers
│                │
▼                ▼
P2b (Twin Chat)  P3b (Bilingual)       ← PARALLEL
│                │
└───────┬────────┘
        ▼
P4a (Experiments) — Week 5.5-6
│
▼
P4b (Polish + Demo) — Week 6-7
```

## Critical Tips for Claude Code Sessions

1. **Always paste the prompt EXACTLY as written** — don't summarize or abbreviate
2. **Each session should start by reviewing existing code** — add "## Existing Code: Look at the /backend and /frontend directories to understand what's already built"
3. **If a session goes wrong, start a new one** — don't try to fix a confused session
4. **Commit after each session** — `git add -A && git commit -m "Phase Px complete"`
5. **Test after each phase** — `cd backend && pytest` before moving to next phase
6. **Keep prompts as .txt files** — NEVER hardcode LLM prompts in Python code
7. **Theme consistency** — if the UI looks off, paste the theme spec again

## Tailwind Config for Darpan Theme

Include this in every frontend session:

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        darpan: {
          bg: "#0A0A0A",
          surface: "#111111",
          elevated: "#1A1A1A",
          border: "#2A2A2A",
          "border-active": "#333333",
          lime: "#C8FF00",
          "lime-dim": "#9ACC00",
          cyan: "#00D4FF",
          "cyan-dim": "#00A8CC",
          success: "#00FF88",
          warning: "#FFB800",
          error: "#FF4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        "glow-lime": "0 0 20px rgba(200, 255, 0, 0.3)",
        "glow-cyan": "0 0 20px rgba(0, 212, 255, 0.3)",
      },
    },
  },
  plugins: [],
};

export default config;
```

```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #0A0A0A;
  --bg-secondary: #111111;
  --accent-lime: #C8FF00;
  --accent-cyan: #00D4FF;
}

body {
  background-color: var(--bg-primary);
  color: #FFFFFF;
  font-family: "Inter", sans-serif;
}
```
