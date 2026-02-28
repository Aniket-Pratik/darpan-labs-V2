/**
 * Experiment and Cohort related TypeScript types.
 */

// Cohort types
export interface TwinSummary {
  twin_id: string;
  quality_label: string;
  quality_score: number;
  modules_completed: string[];
}

export interface CohortFilters {
  min_quality?: 'base' | 'enhanced' | 'rich' | 'full' | null;
  required_modules?: string[];
}

export interface CohortCreateRequest {
  name: string;
  twin_ids: string[];
  filters?: CohortFilters | null;
}

export interface CohortCreateResponse {
  id: string;
  name: string;
  twin_count: number;
  created_at: string;
}

export interface Cohort {
  id: string;
  name: string;
  twin_ids: string[];
  twins: TwinSummary[];
  filters_used?: CohortFilters | null;
  created_at: string;
}

// Experiment types
export type ScenarioType = 'forced_choice' | 'likert_scale' | 'open_scenario' | 'preference_rank';

export interface ExperimentScenario {
  type: ScenarioType;
  prompt: string;
  options?: string[] | null;
  context?: string | null;
}

export interface ExperimentSettings {
  require_reasoning: boolean;
  temperature: number;
  max_tokens: number;
}

export interface ExperimentCreateRequest {
  name: string;
  cohort_id: string;
  scenario: ExperimentScenario;
  settings?: ExperimentSettings;
}

export interface ExperimentCreateResponse {
  experiment_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  cohort_size: number;
  estimated_completion_sec: number;
}

export interface EvidenceUsedInExperiment {
  snippet_id: string;
  why: string;
}

export interface IndividualResult {
  twin_id: string;
  twin_name?: string | null;
  twin_quality: string;
  modules_completed: string[];
  choice?: string | null;
  reasoning: string;
  confidence_score: number;
  confidence_label: 'low' | 'medium' | 'high';
  evidence_used: EvidenceUsedInExperiment[];
  coverage_gaps: string[];
}

export interface ChoiceDistribution {
  count: number;
  percentage: number;
}

export interface KeyPattern {
  pattern: string;
  supporting_twins: number;
  confidence: number;
}

export interface AggregateResults {
  choice_distribution: Record<string, ChoiceDistribution>;
  aggregate_confidence: number;
  confidence_distribution: Record<string, number>;
  key_patterns: KeyPattern[];
  dominant_reasoning_themes: string[];
}

export interface ExperimentResults {
  experiment_id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  cohort_size: number;
  completed_responses: number;
  execution_time_sec?: number | null;
  aggregate_results?: AggregateResults | null;
  individual_results: IndividualResult[];
  limitations_disclaimer: string;
  created_at: string;
  completed_at?: string | null;
}

export interface ExperimentListItem {
  id: string;
  name: string;
  status: string;
  cohort_size: number;
  created_at: string;
  completed_at?: string | null;
}

export interface ExperimentStatus {
  experiment_id: string;
  status: string;
  completed_responses: number;
  total_twins: number;
  progress_pct: number;
}

// Display helpers
export const SCENARIO_TYPES: Record<ScenarioType, { label: string; description: string }> = {
  forced_choice: {
    label: 'Forced Choice',
    description: 'Choose one option from a list',
  },
  likert_scale: {
    label: 'Likert Scale',
    description: 'Rate on a scale (1-5)',
  },
  open_scenario: {
    label: 'Open Scenario',
    description: 'Free-form response to a situation',
  },
  preference_rank: {
    label: 'Preference Rank',
    description: 'Rank options by preference',
  },
};

export const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: 'bg-white/10', text: 'text-white/50' },
  running: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  completed: { bg: 'bg-green-500/20', text: 'text-green-400' },
  failed: { bg: 'bg-red-500/20', text: 'text-red-400' },
};
