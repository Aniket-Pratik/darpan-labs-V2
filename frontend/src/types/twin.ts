/**
 * Twin and Chat related TypeScript types.
 */

// Twin Profile types
export interface TwinProfile {
  id: string;
  user_id: string;
  version: number;
  status: 'generating' | 'ready' | 'failed';
  modules_included: string[];
  quality_label: 'base' | 'enhanced' | 'rich' | 'full';
  quality_score: number;
  structured_profile?: StructuredProfile;
  persona_summary_text?: string;
  coverage_confidence: CoverageConfidence[];
  created_at: string;
  version_history: TwinVersionInfo[];
}

export interface StructuredProfile {
  demographics: Record<string, string>;
  personality?: {
    self_description?: string;
    ocean_estimates?: Record<string, { score: number; confidence: number; evidence: string }>;
  };
  decision_making?: {
    speed_vs_deliberation?: string;
    gut_vs_data?: string;
    risk_appetite?: string;
    behavioral_rules?: Array<{ rule: string; confidence: number }>;
  };
  preferences?: Record<string, unknown>;
  communication?: Record<string, string>;
  domain_specific?: Record<string, unknown>;
  uncertainty_flags?: string[];
}

export interface CoverageConfidence {
  domain: string;
  coverage_score: number;
  confidence_score: number;
  signals_captured: string[];
  uncertainty_flags?: string[];
}

export interface TwinVersionInfo {
  version: number;
  modules_included: string[];
  quality_label: string;
  quality_score: number;
  created_at: string;
}

// Twin Generation types
export interface TwinGenerateRequest {
  trigger: 'mandatory_modules_complete' | 'addon_module_complete' | 'manual';
  modules_to_include: string[];
}

// Chat types
export interface TwinChatRequest {
  message: string;
  session_id?: string;
}

export interface EvidenceUsed {
  snippet_id: string;
  why: string;
  snippet_text?: string;
}

export interface TwinChatResponse {
  session_id: string;
  message_id: string;
  response_text: string;
  confidence_score: number;
  confidence_label: 'low' | 'medium' | 'high';
  uncertainty_reason?: string;
  evidence_used: EvidenceUsed[];
  coverage_gaps: string[];
  suggested_module?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'twin';
  content: string;
  confidence_score?: number;
  confidence_label?: string;
  evidence_used?: EvidenceUsed[];
  coverage_gaps?: string[];
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  twin_id: string;
  messages: ChatMessage[];
  created_at: string;
}

export interface ChatSessionItem {
  id: string;
  twin_id: string;
  created_by: string;
  created_at: string;
  message_count: number;
}

export interface BrandChatSessionItem {
  id: string;
  twin_id: string;
  twin_quality_label: string;
  twin_quality_score: number;
  twin_modules: string[];
  created_at: string;
  message_count: number;
}

// Quality label display info
export const QUALITY_LABELS: Record<string, { name: string; color: string; description: string }> = {
  base: {
    name: 'Base',
    color: '#C8FF00',
    description: 'Built from 4 mandatory modules',
  },
  enhanced: {
    name: 'Enhanced',
    color: '#00D4FF',
    description: 'Improved with 1-2 add-on modules',
  },
  rich: {
    name: 'Rich',
    color: '#A855F7',
    description: 'Comprehensive with 3-4 add-on modules',
  },
  full: {
    name: 'Full',
    color: '#F59E0B',
    description: 'Complete profile with all modules',
  },
};

// Confidence display info
export const CONFIDENCE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  high: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
  medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  low: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
};
