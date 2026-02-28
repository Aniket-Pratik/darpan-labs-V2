# Darpan Labs - Implementation Progress

**Last Updated:** 2026-02-26

---

## Overview

| Phase | Name | Status | Duration | Completion |
|-------|------|--------|----------|------------|
| P0 | Foundation | ✅ Complete | Week 1 | 100% |
| P1 | Text Interview + Modules | ✅ Complete | Weeks 2-3 | 100% |
| P2 | Twin Generation + Chat | ✅ Complete | Weeks 3.5-5 | 100% |
| P3 | Voice Pipeline (STT) | ✅ Complete | Weeks 3.5-5 | 100% |
| P4 | Experiments + Polish | ✅ Complete | Weeks 5.5-7 | 100% |

**Overall Progress:** Phase 4 of 4 complete (~100%)

---

## Phase 0: Foundation ✅

**Status:** Complete
**Completed:** 2026-02-26

### Deliverables

| Task | Status | Files |
|------|--------|-------|
| Git init + .gitignore | ✅ | `.gitignore` |
| Backend directory structure | ✅ | `backend/app/` |
| Config + Database setup | ✅ | `config.py`, `database.py` |
| SQLAlchemy models (12 tables) | ✅ | `models/*.py` |
| Pydantic schemas | ✅ | `schemas/*.py` |
| LLM abstraction layer | ✅ | `llm/client.py` |
| Prompt templates (7 files) | ✅ | `prompts/*.txt` |
| FastAPI main.py + health check | ✅ | `main.py` |
| Seed data (4 question banks) | ✅ | `seed_data/question_banks/*.json` |
| Alembic migrations | ✅ | `migrations/` |
| Tests (158 passing) | ✅ | `tests/*.py` (9 files) |
| Frontend (Next.js + Tailwind) | ✅ | `frontend/src/` |
| Docker Compose | ✅ | `docker-compose.yml` |
| README | ✅ | `README.md` |

### Database Tables Created

- [x] users
- [x] consent_events
- [x] interview_sessions
- [x] interview_modules
- [x] interview_turns
- [x] twin_profiles
- [x] evidence_snippets
- [x] twin_chat_sessions
- [x] twin_chat_messages
- [x] cohorts
- [x] experiments
- [x] experiment_results

### Question Banks Created

- [x] M1: Core Identity & Context (15 questions)
- [x] M2: Decision Logic & Risk (15 questions)
- [x] M3: Preferences & Values (15 questions)
- [x] M4: Communication & Social (15 questions)

### Test Coverage (158 tests)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_models.py` | 41 | All 12 database models |
| `test_config.py` | 22 | Settings, defaults, env overrides |
| `test_database.py` | 19 | Engine, session factory, exports |
| `test_prompts.py` | 35 | All 7 prompt templates |
| `test_seed_data.py` | 21 | Question banks M1-M4 |
| `test_schemas.py` | 7 | Pydantic schema validation |
| `test_llm.py` | 7 | LLM client, retry logic |
| `test_health.py` | 2 | Health check endpoints |
| `conftest.py` | - | Pytest fixtures |

---

## Phase 1: Text Interview + Modules ✅

**Status:** Complete
**Completed:** 2026-02-26

### Sprint 1a: Static Interview + Module State (Week 2)

| Task | Status | Files |
|------|--------|-------|
| POST /api/v1/interviews/start | ✅ | `routers/interviews.py` |
| POST /api/v1/interviews/{id}/answer | ✅ | `routers/interviews.py` |
| POST /api/v1/interviews/{id}/next-question | ✅ | `routers/interviews.py` |
| POST /api/v1/interviews/{id}/skip | ✅ | `routers/interviews.py` |
| POST /api/v1/interviews/{id}/pause | ✅ | `routers/interviews.py` |
| POST /api/v1/interviews/{id}/resume | ✅ | `routers/interviews.py` |
| GET /api/v1/interviews/{id}/status | ✅ | `routers/interviews.py` |
| Module state engine | ✅ | `services/module_state_service.py` |
| Interview UI (text) | ✅ | `frontend/src/app/interview/` |
| Session persistence | ✅ | LocalStorage + DB |

### Sprint 1b: Adaptive Questioning (Week 3)

| Task | Status | Files |
|------|--------|-------|
| Prompt loading service | ✅ | `services/prompt_service.py` |
| Question bank service | ✅ | `services/question_bank_service.py` |
| Answer parser (LLM-powered) | ✅ | `services/answer_parser_service.py` |
| Coverage/confidence scorer | ✅ | `services/module_state_service.py` |
| Adaptive question planner | ✅ | `services/interview_service.py` |
| Module completion evaluator | ✅ | `services/module_state_service.py` |
| Follow-up rules | ✅ | `services/interview_service.py` |
| Multi-session resume | ✅ | `routers/interviews.py` |
| LLM response schemas | ✅ | `schemas/llm_responses.py` |

### Backend Services Created

| Service | Description | File |
|---------|-------------|------|
| PromptService | Load/format prompt templates | `services/prompt_service.py` |
| QuestionBankService | Load JSON question banks, static selection | `services/question_bank_service.py` |
| AnswerParserService | LLM-powered answer parsing with heuristic fallback | `services/answer_parser_service.py` |
| ModuleStateService | Coverage/confidence scoring, module transitions | `services/module_state_service.py` |
| InterviewService | Core orchestration, adaptive questioning | `services/interview_service.py` |

### Frontend Components Created

| Component | Description | File |
|-----------|-------------|------|
| InterviewContainer | Main interview container | `components/interview/InterviewContainer.tsx` |
| QuestionCard | Question display + textarea input | `components/interview/QuestionCard.tsx` |
| ModuleProgress | Progress bar with M1-M4 indicators | `components/interview/ModuleProgress.tsx` |
| ModuleTransition | Framer Motion celebration animation | `components/interview/ModuleTransition.tsx` |
| Zustand Store | Full interview state management | `store/interviewStore.ts` |
| Interview Types | TypeScript interfaces | `types/interview.ts` |
| API Client | Interview API functions | `lib/interviewApi.ts` |

### Test Coverage (199 tests)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_models.py` | 41 | All 12 database models |
| `test_config.py` | 22 | Settings, defaults, env overrides |
| `test_database.py` | 19 | Engine, session factory, exports |
| `test_prompts.py` | 35 | All 7 prompt templates |
| `test_seed_data.py` | 21 | Question banks M1-M4 |
| `test_schemas.py` | 7 | Pydantic schema validation |
| `test_llm.py` | 7 | LLM client, retry logic |
| `test_health.py` | 2 | Health check endpoints |
| `test_interview_services.py` | 39 | Interview services + LLM schemas |
| `conftest.py` | - | Pytest fixtures |

---

## Phase 2: Twin Generation + Chat ✅

**Status:** Complete
**Completed:** 2026-02-26

### Sprint 2a: Twin Generation Pipeline

| Task | Status | Files |
|------|--------|-------|
| LLM response schemas (Profile, Persona, Evidence, Twin) | ✅ | `schemas/llm_responses.py` |
| Profile extraction service | ✅ | `services/profile_builder.py` |
| Persona summary generator | ✅ | `services/persona_generator.py` |
| Evidence chunking + embeddings | ✅ | `services/evidence_indexer.py` |
| Twin generation orchestrator | ✅ | `services/twin_generation_service.py` |
| Twin versioning + quality scoring | ✅ | `services/twin_generation_service.py` |
| Twin profile API (generate, get, versions) | ✅ | `routers/twins.py` |
| Twin generation UI (real API integration) | ✅ | `frontend/src/app/twin/generate/` |
| Persona summary prompt template | ✅ | `prompts/persona_summary.txt` |
| Evidence chunking prompt template | ✅ | `prompts/evidence_chunking.txt` |

### Sprint 2b: Twin Chat

| Task | Status | Files |
|------|--------|-------|
| Evidence retriever (pgvector semantic search) | ✅ | `services/evidence_retriever.py` |
| Twin chat service (response + confidence) | ✅ | `services/twin_chat_service.py` |
| Chat session APIs (chat, history, sessions) | ✅ | `routers/chat.py` |
| Confidence scoring (high/medium/low) | ✅ | Via LLM + twin_response.txt prompt |
| Module-aware suggestions | ✅ | `services/twin_chat_service.py` |
| Chat UI (messages, input, confidence badges) | ✅ | `frontend/src/components/twin/` |
| Twin profile card component | ✅ | `frontend/src/components/twin/TwinProfileCard.tsx` |
| Evidence drawer component | ✅ | `frontend/src/components/twin/EvidenceDrawer.tsx` |
| Chat page | ✅ | `frontend/src/app/twin/chat/page.tsx` |
| Twin API client | ✅ | `frontend/src/lib/twinApi.ts` |
| Twin TypeScript types | ✅ | `frontend/src/types/twin.ts` |
| Streaming responses | 🔲 | Deferred to Phase 4 (SSE) |

### Backend Services Created

| Service | Description | File |
|---------|-------------|------|
| ProfileBuilderService | Extract structured profile from interview transcripts via LLM | `services/profile_builder.py` |
| PersonaGeneratorService | Generate compact first-person persona summary (≤2500 tokens) | `services/persona_generator.py` |
| EvidenceIndexerService | Chunk answers into evidence snippets + generate embeddings | `services/evidence_indexer.py` |
| EvidenceRetrieverService | Semantic search via pgvector with category diversity | `services/evidence_retriever.py` |
| TwinGenerationService | Orchestrate full pipeline: profile → persona → evidence | `services/twin_generation_service.py` |
| TwinChatService | Chat with twins: evidence retrieval → LLM → confidence scoring | `services/twin_chat_service.py` |

### API Endpoints Created

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/twins/generate` | Generate a digital twin |
| GET | `/api/v1/twins/{twin_id}` | Get twin profile |
| GET | `/api/v1/twins/user/{user_id}` | Get user's latest twin |
| GET | `/api/v1/twins/{twin_id}/versions` | Get version history |
| POST | `/api/v1/twins/{twin_id}/chat` | Chat with a twin |
| GET | `/api/v1/twins/{twin_id}/chat/sessions` | List chat sessions |
| GET | `/api/v1/twins/{twin_id}/chat/{session_id}/history` | Get chat history |

### Frontend Components Created

| Component | Description | File |
|-----------|-------------|------|
| ChatContainer | Main chat container with twin loading + message management | `components/twin/ChatContainer.tsx` |
| ChatMessage | Individual message bubble with user/twin styling | `components/twin/ChatMessage.tsx` |
| ChatInput | Message input with auto-resize + send button | `components/twin/ChatInput.tsx` |
| ConfidenceBadge | Color-coded confidence indicator (HIGH/MED/LOW) | `components/twin/ConfidenceBadge.tsx` |
| EvidenceDrawer | Expandable evidence panel with snippet display | `components/twin/EvidenceDrawer.tsx` |
| TwinProfileCard | Twin profile summary (compact + full modes) | `components/twin/TwinProfileCard.tsx` |

### Test Coverage (260 tests total, 64 new)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_twin_generation.py` | 37 | Schemas, quality logic, prompts, services, heuristics |
| `test_twin_chat.py` | 27 | Chat schemas, formatting, router registration |

---

## Phase 3: Voice Pipeline (STT) ✅

**Status:** Complete
**Completed:** 2026-02-26

### Sprint 3a: Voice Infrastructure

| Task | Status | Files |
|------|--------|-------|
| WebSocket endpoint | ✅ | `routers/voice.py` |
| Browser mic capture (16kHz native resampling) | ✅ | `frontend/src/hooks/useVoice.ts` |
| ASR integration (Deepgram Nova-3, SDK v6) | ✅ | `services/asr_service.py` |
| Turn-taking (VAD via Deepgram endpointing) | ✅ | `services/voice_orchestrator.py` |
| Silence timeout prompts (8s gentle, 20s pause offer) | ✅ | `services/voice_orchestrator.py` |
| Voice controls UI (mic button, recording states) | ✅ | `components/interview/VoiceControls.tsx` |
| Live transcript display (partial + final) | ✅ | `components/interview/TranscriptDisplay.tsx` |
| Voice/text mode toggle | ✅ | `components/interview/QuestionCard.tsx` |

### Sprint 3b: Bilingual + Integration

| Task | Status | Files |
|------|--------|-------|
| Hindi/Hinglish/English ASR (Deepgram multi-language) | ✅ | `services/asr_service.py` |
| LLM-based transcript correction | ✅ | `services/transcript_corrector.py` |
| Integration with interview pipeline | ✅ | `services/voice_orchestrator.py` |
| Text fallback (switch to typing mid-interview) | ✅ | `hooks/useVoice.ts`, `QuestionCard.tsx` |
| English-only questions (prompt enforcement) | ✅ | `prompts/interviewer_question.txt` |
| English-only twin responses | ✅ | `prompts/twin_response.txt` |
| Multilingual answer parsing | ✅ | `prompts/answer_parser.txt` |

### Backend Services Created

| Service | Description | File |
|---------|-------------|------|
| ASRService | Deepgram streaming SDK v6 wrapper (Nova-3, multi-language) | `services/asr_service.py` |
| TranscriptCorrectorService | LLM-based ASR error correction with heuristic fallback | `services/transcript_corrector.py` |
| VoiceOrchestrator | Full voice turn coordinator (ASR → correction → interview pipeline) | `services/voice_orchestrator.py` |

### Frontend Components Created/Modified

| Component | Description | File |
|-----------|-------------|------|
| useVoice | Mic capture + WebSocket hook (16kHz PCM streaming) | `hooks/useVoice.ts` |
| VoiceControls | Mic button with pulsing animation, recording/processing states | `components/interview/VoiceControls.tsx` |
| TranscriptDisplay | Real-time partial/final transcript display | `components/interview/TranscriptDisplay.tsx` |
| QuestionCard | Extended with voice/text mode toggle | `components/interview/QuestionCard.tsx` |
| InterviewContainer | Voice hook integration, auto-fallback to text on errors | `components/interview/InterviewContainer.tsx` |
| ModuleInterviewContainer | Voice state management for module interviews | `components/interview/ModuleInterviewContainer.tsx` |
| Zustand Store | Voice state fields + actions (inputMode, transcript, voiceError) | `store/interviewStore.ts` |

### WebSocket Protocol

```
Client → Server:
  Binary frames: raw PCM audio (16kHz, mono, 16-bit)
  JSON: {"type": "control", "action": "start" | "stop" | "switch_to_text"}
  JSON: {"type": "text_answer", "text": "user typed answer"}

Server → Client:
  {"type": "partial_transcript", "text": "mujhe lag..."}
  {"type": "final_transcript", "text": "...", "language": "HG", "confidence": 0.92}
  {"type": "processing"}
  {"type": "next_question", "question_id": "...", "question_text": "...", ...}
  {"type": "error", "message": "..."}
  {"type": "timeout_prompt", "message": "Take your time..."}
```

### Key Technical Decisions
- **No TTS** — questions displayed as text, voice is input-only (STT)
- **Browser-native 16kHz resampling** via `AudioContext({ sampleRate: 16000 })` — avoids aliasing from manual downsampling
- **Deepgram Nova-3** with `language: "multi"` for auto-detection of EN/HI
- **ScriptProcessorNode** for float32→int16 PCM conversion (2048 buffer = 128ms chunks)
- **Auto-fallback to text** after 3 consecutive voice errors
- **Input mode persisted** in localStorage

---

## Phase 4: Experiments + Polish ✅

**Status:** Complete
**Completed:** 2026-02-26

### Sprint 4a: Experiment Engine

| Task | Status | Files |
|------|--------|-------|
| Cohort service (CRUD + filters) | ✅ | `services/cohort_service.py` |
| Cohort API (create, get, list, delete, available-twins) | ✅ | `routers/cohorts.py` |
| Experiment service (create, run, aggregate) | ✅ | `services/experiment_service.py` |
| Experiment API (create, results, status, list) | ✅ | `routers/experiments.py` |
| Parallel twin execution (asyncio semaphore, timeout + retry) | ✅ | `services/experiment_service.py` |
| Aggregate computation (choice dist, confidence, LLM pattern extraction) | ✅ | `services/experiment_service.py` |
| Limitations disclaimer | ✅ | `schemas/experiment.py` |

### Sprint 4b: Add-ons + Frontend

| Task | Status | Files |
|------|--------|-------|
| Add-on question banks A1 (Lifestyle & Routines, 15 Qs) | ✅ | `seed_data/question_banks/A1_lifestyle_routines.json` |
| Add-on question banks A2 (Spending & Financial, 15 Qs) | ✅ | `seed_data/question_banks/A2_spending_financial.json` |
| Add-on question banks A3 (Career & Growth, 15 Qs) | ✅ | `seed_data/question_banks/A3_career_growth.json` |
| Add-on question banks A4 (Work & Learning, 15 Qs) | ✅ | `seed_data/question_banks/A4_work_learning.json` |
| Experiment API client (TypeScript) | ✅ | `frontend/src/lib/experimentApi.ts` |
| Experiment types (TypeScript) | ✅ | `frontend/src/types/experiment.ts` |
| CohortBuilder component | ✅ | `frontend/src/components/experiment/CohortBuilder.tsx` |
| ScenarioEditor component | ✅ | `frontend/src/components/experiment/ScenarioEditor.tsx` |
| ResultsDashboard component | ✅ | `frontend/src/components/experiment/ResultsDashboard.tsx` |
| Experiments list page | ✅ | `frontend/src/app/experiments/page.tsx` |
| New experiment wizard (4-step flow) | ✅ | `frontend/src/app/experiments/new/page.tsx` |
| Experiment results page | ✅ | `frontend/src/app/experiments/[experimentId]/page.tsx` |
| Dashboard page | ✅ | `frontend/src/app/dashboard/page.tsx` |

### Backend Services Created

| Service | Description | File |
|---------|-------------|------|
| CohortService | CRUD, filtering by quality/modules, twin validation | `services/cohort_service.py` |
| ExperimentService | Orchestrate execution, LLM calls, aggregation | `services/experiment_service.py` |

### API Endpoints Created

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/cohorts` | Create a cohort |
| GET | `/api/v1/cohorts/{cohort_id}` | Get cohort with twin summaries |
| GET | `/api/v1/cohorts/user/{user_id}` | List user's cohorts |
| DELETE | `/api/v1/cohorts/{cohort_id}` | Delete a cohort |
| GET | `/api/v1/cohorts/available-twins` | List available twins for selection |
| POST | `/api/v1/experiments` | Create and run experiment |
| GET | `/api/v1/experiments/{id}` | Get full results + aggregate |
| GET | `/api/v1/experiments/{id}/status` | Get progress/status |
| GET | `/api/v1/experiments/user/{user_id}` | List user's experiments |

### Frontend Components Created

| Component | Description | File |
|-----------|-------------|------|
| CohortBuilder | Twin selection with quality filters | `components/experiment/CohortBuilder.tsx` |
| ScenarioEditor | 4 scenario types, options editor | `components/experiment/ScenarioEditor.tsx` |
| ResultsDashboard | Aggregate charts, patterns, individual results | `components/experiment/ResultsDashboard.tsx` |

### Test Coverage (299 tests total, 39 new)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_experiments.py` | 39 | Schemas, prompts, services, question banks, routers |

### Deferred / Future
| Task | Status | Notes |
|------|--------|-------|
| Holdout evaluation mode | 🔲 | Deferred — requires live validation data |
| Streaming chat responses (SSE) | 🔲 | Deferred from P2 |
| End-to-end tests | 🔲 | |
| Privacy controls (data deletion) | 🔲 | |

---

## Milestones

| Milestone | Deliverable | Target | Status |
|-----------|-------------|--------|--------|
| M0 | Foundation running | End Week 1 | ✅ Complete |
| M1 | Text interview (M1-M4) with adaptive logic | End Week 3 | ✅ Complete |
| M2 | Twin generation + chat with confidence | End Week 5 | ✅ Complete |
| M3 | Voice pipeline integrated (EN/HI/Hinglish) | End Week 5 | ✅ Complete |
| M4 | Experiments + add-ons + demo-ready | End Week 7 | ✅ Complete |

---

## Technical Debt & Notes

### Phase 0 Notes
- All 12 database tables created with proper relationships
- LLM client supports retry logic and JSON validation
- Question banks cover all required signals for M1-M4
- Frontend uses Darpan dark theme (#0A0A0A bg, #C8FF00 lime accent)
- Fixed reserved field name issue: `metadata` → `consent_metadata` / `snippet_metadata`

### Phase 1 Notes
- **199 tests passing** (158 from P0 + 41 new interview service tests)
- LLM-powered adaptive questioning with heuristic fallback
- Answer parsing extracts signals with confidence scores
- Module completion evaluated by LLM with coverage/confidence thresholds
- Session persistence via localStorage + database
- Polished UI with Framer Motion animations
- Progress bar shows M1-M4 module status
- Module transitions with celebration animations and summaries

### Phase 3 Notes
- **Deepgram SDK v6** has completely different API from v3 (async context managers, `listen.v1.connect()`, `recv()` loop)
- Browser-native `AudioContext({ sampleRate: 16000 })` resampling is far superior to manual point-sampling
- Nova-3 model with `smart_format` + `punctuate` gives significantly better accuracy than Nova-2
- `autoGainControl` on mic capture improves recognition quality
- Transcript correction service skips LLM call for high-confidence simple English (optimization)
- Voice orchestrator reuses existing `InterviewService.submit_answer()` and `get_next_question()` — no changes to core interview pipeline

### Known Issues
- None currently

### Future Improvements
- [ ] Add rate limiting to API endpoints
- [ ] Implement caching for question banks
- [ ] Add comprehensive API documentation
- [ ] Setup CI/CD pipeline
- [ ] Add end-to-end frontend tests

---

## File Structure Summary

```
darpan-labs/
├── backend/
│   ├── app/
│   │   ├── main.py              ✅
│   │   ├── config.py            ✅
│   │   ├── database.py          ✅
│   │   ├── models/              ✅ (6 files)
│   │   ├── schemas/             ✅ (6 files, +llm_responses.py)
│   │   ├── routers/             ✅ (interviews.py, twins.py, chat.py, voice.py)
│   │   ├── services/            ✅ (11 files)
│   │   │   ├── prompt_service.py
│   │   │   ├── question_bank_service.py
│   │   │   ├── answer_parser_service.py
│   │   │   ├── module_state_service.py
│   │   │   ├── interview_service.py
│   │   │   ├── profile_builder.py
│   │   │   ├── persona_generator.py
│   │   │   ├── evidence_indexer.py
│   │   │   ├── evidence_retriever.py
│   │   │   ├── twin_generation_service.py
│   │   │   ├── twin_chat_service.py
│   │   │   ├── asr_service.py
│   │   │   ├── transcript_corrector.py
│   │   │   └── voice_orchestrator.py
│   │   ├── llm/                 ✅ (client.py)
│   │   └── workers/             🔲 (placeholder)
│   ├── prompts/                 ✅ (9 files)
│   ├── migrations/              ✅
│   ├── tests/                   ✅ (10 files, 199 tests)
│   └── seed_data/               ✅ (4 question banks)
├── frontend/
│   └── src/
│       ├── app/                 ✅ (layout, page, interview/)
│       │   └── interview/
│       │       ├── page.tsx     ✅ (landing page)
│       │       ├── start/       ✅ (start flow)
│       │       └── [sessionId]/ ✅ (interview session)
│       ├── components/          ✅
│       │   ├── interview/
│       │   │   ├── InterviewContainer.tsx
│       │   │   ├── ModuleInterviewContainer.tsx
│       │   │   ├── QuestionCard.tsx
│       │   │   ├── ModuleProgress.tsx
│       │   │   ├── ModuleTransition.tsx
│       │   │   ├── VoiceControls.tsx
│       │   │   └── TranscriptDisplay.tsx
│       │   └── twin/
│       │       ├── ChatContainer.tsx
│       │       ├── ChatMessage.tsx
│       │       ├── ChatInput.tsx
│       │       ├── ConfidenceBadge.tsx
│       │       ├── EvidenceDrawer.tsx
│       │       └── TwinProfileCard.tsx
│       ├── hooks/               ✅ (useVoice.ts)
│       ├── store/               ✅ (interviewStore.ts)
│       ├── types/               ✅ (interview.ts, twin.ts)
│       └── lib/                 ✅ (api.ts, interviewApi.ts, twinApi.ts)
├── docker-compose.yml           ✅
├── README.md                    ✅
└── PROGRESS.md                  ✅ (this file)
```

---

## How to Verify Phase 0

```bash
# 1. Start database
docker-compose up db redis -d

# 2. Install dependencies
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Run tests
pytest -v

# 5. Start backend
uvicorn app.main:app --reload

# 6. Check health
curl http://localhost:8000/health

# 7. Start frontend
cd ../frontend
npm install
npm run dev
```

---

*This document is automatically updated as implementation progresses.*
