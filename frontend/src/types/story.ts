export interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  summary: string;
  details: string;
  isMajor?: boolean;
}

export interface PerspectiveSource {
  id: string;
  name: string;
  position: number;
  analysis: string;
}

export interface SocialPulseData {
  topQuestion: string;
  questionAnswer: string;
  misconception: {
    claim: string;
    correction: string;
  };
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface Story {
  id: string;
  category: string;
  headline: string;
  summary?: string;
  readTime: number;
  lastUpdated: string;
  fullSummary: string;
  hasTimeline?: boolean;
  hasPerspectives?: boolean;
  hasSocialPulse?: boolean;
  timeline?: { events: TimelineEvent[] };
  perspectives?: { 
    sources: PerspectiveSource[]; 
    progressiveQuote: string; 
    conservativeQuote: string; 
    progressiveTerms: string[]; 
    conservativeTerms: string[] 
  };
  socialPulse?: SocialPulseData;
  duration?: number;
}