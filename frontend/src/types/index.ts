export interface User {
  id: string;
  username: string;
  email: string;
  is_premium: boolean;
  analysis_count: number;
}

export interface NewsSource {
  id: string;
  name: string;
  domain: string;
  language: string;
  is_active: boolean;
  requires_javascript: boolean;
  article_count: number;
  created_at: string;
}

export interface Article {
  id: string;
  url: string;
  title: string;
  content: string;
  author: string;
  published_at: string | null;
  source: string;
  source_name: string;
  language: string;
  word_count: number;
  reading_time: number;
  is_processed: boolean;
  is_enriched: boolean;
  processing_error: string;
  analyses: AIAnalysis[];
  analysis_count: number;
  created_at: string;
  updated_at: string;
}

export interface AIAnalysis {
  id: string;
  analysis_type: AnalysisType;
  analysis_type_display: string;
  result: unknown;
  model_used: string;
  processing_time: number;
  created_at: string;
  created_by: string | null;
}

export type AnalysisType =
  | 'jargon'
  | 'viewpoints'
  | 'fact_check'
  | 'bias'
  | 'timeline'
  | 'expert'
  | 'x_pulse';

export interface ProcessingJob {
  id: string;
  article: string;
  article_title: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  job_type: string;
  celery_task_id: string;
  error_message: string;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
  created_at: string;
}

// Analysis result types
export interface JargonResult {
  terms: Array<{
    term: string;
    explanation: string;
    context?: string;
  }>;
}

export interface ViewpointsResult {
  viewpoints: Array<{
    perspective: string;
    argument: string;
    supporting_points: string[];
  }>;
}

export interface FactCheckResult {
  claims: Array<{
    claim: string;
    verdict: 'true' | 'false' | 'misleading' | 'unverifiable';
    explanation: string;
    sources?: string[];
  }>;
}

export interface BiasResult {
  overall_bias: string;
  bias_score: number;
  indicators: string[];
  analysis: string;
}

export interface TimelineResult {
  events: Array<{
    date: string;
    event: string;
    significance: string;
  }>;
}

export interface ExpertResult {
  opinions: Array<{
    expert_field: string;
    opinion: string;
    reasoning: string;
  }>;
}

export interface XPulseResult {
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
  };
  trending_topics: string[];
  key_discussions: Array<{
    topic: string;
    summary: string;
    engagement_level: 'high' | 'medium' | 'low';
  }>;
}
