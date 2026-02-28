/**
 * Interview-related TypeScript types.
 */

// Module types
export type ModuleStatus = 'pending' | 'active' | 'completed' | 'skipped';
export type InterviewStatus = 'idle' | 'loading' | 'active' | 'paused' | 'completed' | 'error';
export type QuestionType = 'open_text' | 'forced_choice' | 'scenario' | 'trade_off' | 'likert';
export type NextQuestionStatus = 'continue' | 'module_complete' | 'all_modules_complete';

// API Request types
export interface InterviewStartRequest {
  user_id: string;
  input_mode?: 'voice' | 'text';
  language_preference?: 'auto' | 'en' | 'hi';
  modules_to_complete?: string[];
  sensitivity_settings?: {
    allow_sensitive_topics: boolean;
    allowed_sensitive_categories: string[];
  };
  consent?: {
    accepted: boolean;
    consent_version?: string;
    allow_audio_storage_days?: number;
    allow_data_retention_days?: number;
  };
}

export interface InterviewAnswerRequest {
  answer_text: string;
  question_id: string;
  input_mode?: 'voice' | 'text';
  audio_meta?: Record<string, unknown>;
}

export interface InterviewSkipRequest {
  reason?: string;
}

// API Response types
export interface ModuleInfo {
  module_id: string;
  module_name: string;
  estimated_duration_min: number;
  status: ModuleStatus;
}

export interface ModulePlanItem {
  module_id: string;
  status: ModuleStatus;
  est_min: number;
}

export interface FirstQuestion {
  question_id: string;
  question_text: string;
  question_type: string;
  target_signal: string;
}

export interface QuestionMeta {
  question_id: string;
  question_type: QuestionType;
  target_signal: string;
  rationale?: string;
  is_followup: boolean;
  parent_question_id?: string;
}

export interface ModuleProgress {
  module_id: string;
  module_name: string;
  questions_asked: number;
  coverage_score: number;
  confidence_score: number;
  signals_captured: string[];
  status: ModuleStatus;
}

export interface InterviewStartResponse {
  session_id: string;
  status: string;
  voice_config?: {
    websocket_url?: string;
    audio_format: string;
    tts_voice: string;
  };
  first_module: ModuleInfo;
  module_plan: ModulePlanItem[];
  first_question: FirstQuestion;
}

export interface InterviewAnswerResponse {
  turn_id: string;
  answer_received: boolean;
  answer_meta?: Record<string, unknown>;
}

export interface InterviewNextQuestionResponse {
  question_id?: string;
  question_text?: string;
  question_type?: string;
  question_meta?: QuestionMeta;
  module_id: string;
  module_progress: ModuleProgress;
  status: NextQuestionStatus;
  module_summary?: string;
  acknowledgment_text?: string;
}

export interface InterviewStatusResponse {
  session_id: string;
  status: 'active' | 'paused' | 'completed';
  input_mode: string;
  language_preference: string;
  started_at: string;
  total_duration_sec?: number;
  modules: ModuleProgress[];
  current_module?: string;
  completed_modules: string[];
}

export interface InterviewPauseResponse {
  session_id: string;
  status: string;
  can_resume: boolean;
  resume_at_module: string;
  resume_at_question: number;
}

// Module display info
export const MODULE_INFO: Record<string, { name: string; description: string }> = {
  M1: {
    name: 'Core Identity & Context',
    description: 'Understanding who you are and your life context',
  },
  M2: {
    name: 'Decision Logic & Risk',
    description: 'How you make decisions and handle uncertainty',
  },
  M3: {
    name: 'Preferences & Values',
    description: 'Your priorities and what matters to you',
  },
  M4: {
    name: 'Communication & Social',
    description: 'Your interaction style and social tendencies',
  },
};

// Module-based onboarding types
export type UserModuleStatusType = 'not_started' | 'in_progress' | 'completed';

export interface UserModuleStatus {
  module_id: string;
  module_name: string;
  description: string;
  status: UserModuleStatusType;
  coverage_score?: number;
  confidence_score?: number;
  estimated_duration_min: number;
  session_id?: string;
}

export interface UserModulesResponse {
  user_id: string;
  modules: UserModuleStatus[];
  completed_count: number;
  total_required: number;
  can_generate_twin: boolean;
  existing_twin_id?: string;
}

export interface StartSingleModuleRequest {
  user_id: string;
  module_id: string;
  input_mode?: 'voice' | 'text';
  language_preference?: 'auto' | 'en' | 'hi';
  consent?: {
    accepted: boolean;
    consent_version?: string;
  };
}

export interface ModuleCompleteResponse {
  session_id: string;
  module_id: string;
  module_name: string;
  status: string;
  module_summary?: string;
  coverage_score: number;
  confidence_score: number;
  can_generate_twin: boolean;
  remaining_modules: string[];
}

export interface TwinEligibilityResponse {
  user_id: string;
  can_generate_twin: boolean;
  completed_modules: string[];
  missing_modules: string[];
  message: string;
}

// Voice WebSocket message types
export type VoiceServerMessage =
  | { type: 'final_transcript'; text: string; language: string; confidence: number }
  | { type: 'processing' }
  | {
      type: 'next_question';
      question_id: string | null;
      question_text: string | null;
      question_type: string | null;
      module_progress: ModuleProgress;
      status: NextQuestionStatus;
      module_summary?: string;
    }
  | { type: 'error'; message: string }
  | { type: 'timeout_prompt'; message: string };

export type VoiceClientMessage =
  | { type: 'control'; action: 'start' | 'stop' | 'switch_to_text' }
  | { type: 'text_answer'; text: string };
