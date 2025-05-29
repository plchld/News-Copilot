'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { Headphones, BookOpen, CheckCircle } from 'lucide-react';
import StoryCard from '@/components/story/StoryCard';
import AudioPlayer from '@/components/audio/AudioPlayer';
import { BriefLoadingSkeleton } from '@/components/ui/SkeletonLoading';

// Hard-coded daily stories (max 5 - NEVER show more)
const dailyStories = [
  {
    id: '1',
    headline: 'EU implements groundbreaking AI safety regulations',
    summary:
      'New legislation sets global standards for artificial intelligence development, requiring risk assessments for high-impact AI systems and protecting fundamental rights.',
    fullSummary: 'The European Union has passed comprehensive AI safety regulations that will fundamentally reshape how artificial intelligence systems are developed and deployed across the bloc. These groundbreaking rules establish global standards for AI development, requiring comprehensive risk assessments for high-impact AI systems and ensuring protection of fundamental rights. The legislation introduces a risk-based approach to AI regulation, with stricter requirements for systems deemed to pose greater risks to safety, health, and fundamental rights.',
    category: 'tech',
    readTime: 4,
    lastUpdated: '2 hours ago',
    hasTimeline: true,
    hasPerspectives: true,
    hasSocialPulse: true,
    timeline: {
      events: [
        {
          id: '1',
          date: 'March 2024',
          title: 'Initial draft legislation',
          summary: 'Commission publishes first AI Act proposal',
          details: 'The European Commission released its initial proposal for AI regulation, marking the first comprehensive attempt to regulate artificial intelligence at the EU level.',
          isMajor: true
        },
        {
          id: '2', 
          date: 'April 2024',
          title: 'Parliamentary amendments',
          summary: 'MEPs propose key changes to risk categories',
          details: 'The European Parliament introduced significant amendments to strengthen protections and clarify risk assessment procedures.'
        },
        {
          id: '3',
          date: 'May 2024',
          title: 'Final vote and approval',
          summary: 'Legislation passes with overwhelming majority',
          details: 'The AI Act received final approval with 523 votes in favor, establishing the world\'s first comprehensive AI regulation.',
          isMajor: true
        }
      ]
    },
    perspectives: {
      sources: [
        { id: '1', name: 'Tech Weekly', position: 25, analysis: 'Emphasizes innovation benefits and global competitiveness' },
        { id: '2', name: 'Privacy Watch', position: 15, analysis: 'Focuses on fundamental rights protections and privacy safeguards' },
        { id: '3', name: 'Business Today', position: 75, analysis: 'Concerns about regulatory burden on industry' }
      ],
      progressiveQuote: 'This landmark legislation puts human rights at the center of AI development',
      conservativeQuote: 'Excessive regulation could stifle European innovation in the global AI race',
      progressiveTerms: ['human rights', 'protection', 'accountability'],
      conservativeTerms: ['innovation', 'competitiveness', 'burden']
    },
    socialPulse: {
      trendingLevel: 'high' as const,
      trendingDescription: 'Widely discussed across tech and policy communities',
      topQuestion: 'How will this affect AI development in my country?',
      questionAnswer: 'The EU AI Act will likely influence global AI standards, even for companies outside Europe.',
      misconception: {
        claim: 'The AI Act will ban all AI development in Europe',
        correction: 'The Act regulates high-risk AI systems but encourages innovation in low-risk applications'
      },
      sentiment: {
        positive: 45,
        neutral: 35,
        negative: 20
      }
    },
    duration: 240
  },
  {
    id: '2',
    headline: 'Greek parliament passes major economic reforms',
    summary:
      'Sweeping changes to taxation and labor laws aim to boost competitiveness while protecting worker rights, marking a significant shift in fiscal policy.',
    fullSummary: 'The Greek parliament has approved comprehensive economic reforms that represent the most significant changes to the country\'s fiscal and labor policies in over a decade. The sweeping legislation includes substantial modifications to taxation structures and labor laws, designed to boost national competitiveness while maintaining protections for worker rights.',
    category: 'politics',
    readTime: 3,
    lastUpdated: '4 hours ago',
    hasTimeline: true,
    hasPerspectives: true,
    hasSocialPulse: false,
    duration: 180
  },
  {
    id: '3',
    headline: 'Mediterranean startup ecosystem reaches record funding',
    summary:
      'Venture capital investments in Southern European startups surpass €2.1 billion, driven by fintech and climate tech innovations.',
    fullSummary: 'The Mediterranean startup ecosystem has achieved a historic milestone with venture capital investments reaching €2.1 billion, representing a 40% increase from the previous year. This surge is primarily driven by breakthrough innovations in fintech and climate technology sectors.',
    category: 'business',
    readTime: 2,
    lastUpdated: '6 hours ago',
    hasTimeline: false,
    hasPerspectives: true,
    hasSocialPulse: true,
    duration: 120
  },
  {
    id: '4',
    headline: 'Ancient Minoan settlement discovered on Crete',
    summary:
      'Archaeological team uncovers 3,500-year-old Bronze Age town, revealing new insights into early Aegean civilization and trade networks.',
    fullSummary: 'An international archaeological team has made a remarkable discovery on the Greek island of Crete, uncovering a well-preserved 3,500-year-old Bronze Age settlement that provides unprecedented insights into Minoan civilization and ancient Mediterranean trade networks.',
    category: 'culture',
    readTime: 3,
    lastUpdated: '8 hours ago',
    hasTimeline: true,
    hasPerspectives: false,
    hasSocialPulse: false,
    duration: 180
  },
  {
    id: '5',
    headline: 'Climate change accelerates Mediterranean warming',
    summary:
      'New research shows the region warming 20% faster than global average, with implications for agriculture, tourism, and water resources.',
    fullSummary: 'Groundbreaking climate research reveals that the Mediterranean region is experiencing warming at a rate 20% faster than the global average, with far-reaching implications for agriculture, tourism industries, and water resource management across Southern Europe and North Africa.',
    category: 'science',
    readTime: 4,
    lastUpdated: '1 hour ago',
    hasTimeline: true,
    hasPerspectives: true,
    hasSocialPulse: true,
    duration: 240
  },
];

// Get category color
const getCategoryColor = (category: string): string => {
  const colors: Record<string, string> = {
    tech: '#3B82F6',
    politics: '#EF4444',
    business: '#10B981',
    world: '#8B5CF6',
    culture: '#F59E0B',
    health: '#EC4899',
    science: '#06B6D4',
  };
  return colors[category] || '#6B7280';
};

export default function DailyBriefPage() {
  const [audioMode, setAudioMode] = useState(false);
  const [currentAudioIndex, setCurrentAudioIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const totalReadTime = dailyStories.reduce(
    (acc, story) => acc + story.readTime,
    0,
  );

  return (
    <main className="min-h-screen bg-black">
      {/* Fixed header */}
      <header className="fixed inset-x-0 top-0 z-top glass-premium border-b border-white/5">
        <div className="mx-auto max-w-4xl px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Thursday, May 29</p>
              <h1 className="text-xl font-serif text-white">Your Brief</h1>
            </div>

            {/* Mode toggle */}
            <div className="flex items-center gap-2 p-1 bg-white/[0.03] rounded-xl">
              <button
                onClick={() => setAudioMode(true)}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${audioMode
                    ? 'bg-white/10 text-white'
                    : 'text-white/60 hover:text-white/80'}
                `}
              >
                <span className="flex items-center gap-2">
                  <Headphones className="w-4 h-4" />
                  Audio
                </span>
              </button>
              <button
                onClick={() => setAudioMode(false)}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${!audioMode
                    ? 'bg-white/10 text-white'
                    : 'text-white/60 hover:text-white/80'}
                `}
              >
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  Read
                </span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="pt-24 pb-8">
        <div className="mx-auto max-w-4xl px-6">
          {/* Brief summary */}
          <div className="mb-8 text-center">
            <p className="text-gray-400">
              {dailyStories.length} stories · {totalReadTime} min read
            </p>
          </div>

          {/* Story cards */}
          <div className="space-y-4">
            {isLoading ? (
              <BriefLoadingSkeleton />
            ) : (
              dailyStories.map((story, index) => (
                <StoryCard
                  key={story.id}
                  story={story}
                  index={index}
                  isPlaying={audioMode && currentAudioIndex === index}
                />
              ))
            )}
          </div>

          {/* Completion state - critical for finite feel */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="mt-16 text-center"
          >
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/[0.03] rounded-full">
              <CheckCircle className="w-5 h-5 text-green-500/70" />
              <span className="text-white/60 text-sm">
                That's everything for today
              </span>
            </div>
            <p className="text-white/40 mt-4 text-sm">
              No infinite scroll. No endless feeds. Just what matters.
            </p>
            <Link
              href="/"
              className="inline-block text-white/30 hover:text-white/50 transition-colors text-sm mt-6"
            >
              ← Back to Home
            </Link>
          </motion.div>
        </div>
      </div>


      {/* Enhanced Audio Player */}
      {audioMode && (
        <AudioPlayer
          stories={dailyStories}
          currentIndex={currentAudioIndex}
          onStoryChange={setCurrentAudioIndex}
          isVisible={audioMode}
        />
      )}
    </main>
  );
}
