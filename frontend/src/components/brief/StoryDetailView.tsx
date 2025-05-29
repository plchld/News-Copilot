'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, BarChart, MessageCircle } from 'lucide-react';
import TimelineView from './TimelineView';
import PerspectivesView from './PerspectivesView';
import SocialPulseView from './SocialPulseView';

interface StoryDetailViewProps {
  story: {
    id: string;
    headline: string;
    summary: string;
    readTime: number;
    category: string;
    fullContent: string;
    hasTimeline?: boolean;
    hasPerspectives?: boolean;
    socialPulse?: {
      trendingLevel: 'low' | 'medium' | 'high';
      topQuestion?: string;
    };
    timeline?: Array<{
      date: string;
      event: string;
      description: string;
    }>;
    perspectives?: Array<{
      source: string;
      stance: 'supportive' | 'concerned' | 'neutral';
      quote: string;
    }>;
  };
  onClose: () => void;
}

export default function StoryDetailView({
  story,
  onClose,
}: StoryDetailViewProps) {
  const [activeTab, setActiveTab] = useState<
    'timeline' | 'perspectives' | 'social'
  >('timeline');

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      technology: 'text-tech border-tech/20 bg-tech/10',
      business: 'text-business border-business/20 bg-business/10',
      world: 'text-world border-world/20 bg-world/10',
      politics: 'text-politics border-politics/20 bg-politics/10',
      culture: 'text-culture border-culture/20 bg-culture/10',
      science: 'text-blue-400 border-blue-400/20 bg-blue-400/10',
    };
    return (
      colors[category.toLowerCase()] ||
      'text-primary border-primary/20 bg-primary/10'
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', duration: 0.5 }}
        className="h-full overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="min-h-full bg-gray-900">
          {/* Header */}
          <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-900/80 backdrop-blur-lg">
            <div className="mx-auto max-w-4xl px-4 py-4">
              <div className="flex items-center justify-between">
                <button
                  onClick={onClose}
                  className="flex items-center gap-2 text-gray-400 transition-colors hover:text-white"
                >
                  <svg
                    className="h-5 w-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 19l-7-7m0 0l7-7m-7 7h18"
                    />
                  </svg>
                  Back
                </button>
                <button className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm transition-all hover:border-white/20 hover:bg-white/10">
                  Follow story
                </button>
              </div>
            </div>
          </header>

          {/* Content */}
          <div className="mx-auto max-w-4xl px-4 py-8">
            {/* Category and metadata */}
            <div className="mb-6 flex items-center gap-3">
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getCategoryColor(story.category)} border`}
              >
                {story.category}
              </span>
              <span className="text-sm text-gray-400">
                {story.readTime} min read
              </span>
            </div>

            {/* Headline */}
            <h1 className="mb-6 font-serif text-3xl leading-tight text-white sm:text-4xl">
              {story.headline}
            </h1>

            {/* Full content with jargon explanations */}
            <div className="prose prose-lg prose-invert mb-12 max-w-none">
              {story.fullContent
                .split('\n\n')
                .map((paragraph: string, index: number) => (
                  <p key={index} className="mb-6 leading-relaxed text-gray-300">
                    {paragraph.split(' ').map((word, wordIndex) => {
                      // Simple jargon detection for demo
                      const jargonWords = ['FTC', 'API', 'GDP', 'FDA'];
                      if (jargonWords.includes(word.replace(/[.,!?;:]/, ''))) {
                        return (
                          <span
                            key={wordIndex}
                            className="group relative inline-block"
                          >
                            <span className="cursor-help border-b border-dotted border-gray-500">
                              {word}
                            </span>
                            <span className="pointer-events-none absolute bottom-full left-1/2 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-gray-800 px-3 py-2 text-sm opacity-0 transition-opacity group-hover:opacity-100">
                              {word === 'FTC' && 'Federal Trade Commission'}
                              {word === 'API' &&
                                'Application Programming Interface'}
                              {word === 'GDP' && 'Gross Domestic Product'}
                              {word === 'FDA' && 'Food and Drug Administration'}
                            </span>
                          </span>
                        );
                      }
                      return <span key={wordIndex}>{word} </span>;
                    })}
                  </p>
                ))}
            </div>

            {/* Information layers tabs */}
            <div className="border-t border-gray-800 pt-8">
              <div className="mb-8 flex gap-1">
                {story.hasTimeline && (
                  <button
                    onClick={() => setActiveTab('timeline')}
                    className={`flex-1 rounded-lg px-4 py-3 font-medium transition-all ${
                      activeTab === 'timeline'
                        ? 'bg-white/10 text-white'
                        : 'text-gray-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <Clock className="mr-2 inline h-4 w-4" />
                    Timeline
                  </button>
                )}
                {story.hasPerspectives && (
                  <button
                    onClick={() => setActiveTab('perspectives')}
                    className={`flex-1 rounded-lg px-4 py-3 font-medium transition-all ${
                      activeTab === 'perspectives'
                        ? 'bg-white/10 text-white'
                        : 'text-gray-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <BarChart className="mr-2 inline h-4 w-4" />
                    Perspectives
                  </button>
                )}
                {story.socialPulse && (
                  <button
                    onClick={() => setActiveTab('social')}
                    className={`flex-1 rounded-lg px-4 py-3 font-medium transition-all ${
                      activeTab === 'social'
                        ? 'bg-white/10 text-white'
                        : 'text-gray-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <MessageCircle className="mr-2 inline h-4 w-4" />
                    Social
                  </button>
                )}
              </div>

              {/* Tab content */}
              <div className="min-h-[400px]">
                {activeTab === 'timeline' && story.timeline && (
                  <TimelineView timeline={story.timeline} />
                )}
                {activeTab === 'perspectives' && story.perspectives && (
                  <PerspectivesView perspectives={story.perspectives} />
                )}
                {activeTab === 'social' && story.socialPulse && (
                  <SocialPulseView socialPulse={story.socialPulse} />
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
