'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Bell, Clock, BarChart3, Users, TrendingUp } from 'lucide-react';
import TimelineView from './TimelineView';
import PerspectivesView from './PerspectivesView';
import SocialPulseView from './SocialPulseView';
import JargonText, { JargonModal } from './JargonText';
import type { Story } from '@/types/story';

interface ExpandedStoryViewProps {
  story: Story;
  onClose: () => void;
}

type TabType = 'story' | 'timeline' | 'perspectives' | 'social';

interface Tab {
  id: TabType;
  label: string;
  icon: React.ReactNode;
  available: boolean;
}

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    tech: 'text-blue-400',
    politics: 'text-red-400',
    business: 'text-green-400',
    world: 'text-purple-400',
    culture: 'text-yellow-400',
    health: 'text-pink-400',
    science: 'text-cyan-400',
  };
  return colors[category] || 'text-gray-400';
};

export default function ExpandedStoryView({ story, onClose }: ExpandedStoryViewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('story');
  const [showJargonExplanation, setShowJargonExplanation] = useState<{ word: string; explanation: string } | null>(null);

  const tabs: Tab[] = [
    {
      id: 'story',
      label: 'Story',
      icon: <Users className="w-4 h-4" />,
      available: true,
    },
    {
      id: 'timeline',
      label: 'Timeline',
      icon: <Clock className="w-4 h-4" />,
      available: story.hasTimeline || false,
    },
    {
      id: 'perspectives',
      label: 'Perspectives',
      icon: <BarChart3 className="w-4 h-4" />,
      available: story.hasPerspectives || false,
    },
    {
      id: 'social',
      label: 'Social Pulse',
      icon: <TrendingUp className="w-4 h-4" />,
      available: story.hasSocialPulse || false,
    },
  ];

  const availableTabs = tabs.filter(tab => tab.available);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black overflow-y-auto"
    >
      {/* Header with back button */}
      <header className="sticky top-0 z-10 glass-premium border-b border-white/[0.05]">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white/60 hover:text-white/90 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to brief</span>
          </button>

          {/* Follow story button */}
          <button className="flex items-center gap-2 px-4 py-2 bg-white/[0.05] hover:bg-white/[0.08] rounded-lg transition-colors">
            <Bell className="w-4 h-4" />
            <span className="text-sm">Follow story</span>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-3xl mx-auto px-6 py-12">
        {/* Category and metadata */}
        <div className="flex items-center gap-4 mb-6">
          <span className={`
            text-xs font-medium uppercase tracking-wider
            ${getCategoryColor(story.category)}
          `}>
            {story.category}
          </span>
          <span className="text-xs text-white/40">
            {story.readTime} min read • Updated {story.lastUpdated}
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-5xl font-serif text-white leading-tight mb-8">
          {story.headline}
        </h1>

        {/* Progressive depth tabs */}
        <div className="mb-8">
          <div className="flex gap-1 p-1 bg-white/[0.03] rounded-xl border border-white/[0.05] mb-8">
            {availableTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300
                  ${activeTab === tab.id
                    ? 'bg-white/10 text-white shadow-lg'
                    : 'text-white/60 hover:text-white/80 hover:bg-white/[0.05]'
                  }
                `}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="min-h-[400px]"
            >
              {activeTab === 'story' && (
                <div className="prose prose-invert prose-lg max-w-none">
                  <JargonText 
                    content={story.fullSummary}
                    onJargonClick={setShowJargonExplanation}
                  />
                </div>
              )}
              
              {activeTab === 'timeline' && story.timeline && (
                <TimelineView timeline={story.timeline} />
              )}
              
              {activeTab === 'perspectives' && story.perspectives && (
                <PerspectivesView perspectives={story.perspectives} />
              )}
              
              {activeTab === 'social' && story.socialPulse && (
                <SocialPulseView socialData={story.socialPulse} />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Jargon explanation modal */}
      <JargonModal 
        term={showJargonExplanation}
        onClose={() => setShowJargonExplanation(null)}
      />
    </motion.div>
  );
}