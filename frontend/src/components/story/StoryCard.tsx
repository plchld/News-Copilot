'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, BarChart3, MessageCircle, TrendingUp } from 'lucide-react';
import ExpandedStoryView from './ExpandedStoryView';

interface Story {
  id: string;
  category: string;
  headline: string;
  summary: string;
  readTime: number;
  lastUpdated: string;
  fullSummary: string;
  hasTimeline?: boolean;
  hasPerspectives?: boolean;
  hasSocialPulse?: boolean;
  timeline?: any;
  perspectives?: any;
  socialPulse?: any;
}

interface StoryCardProps {
  story: Story;
  index: number;
  isPlaying?: boolean;
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

export default function StoryCard({ story, index, isPlaying = false }: StoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <>
      <motion.article
        layout
        className="relative overflow-hidden cursor-pointer"
        onClick={() => setIsExpanded(true)}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
      >
        <div className={`
          story-card-premium group
          ${isPlaying ? 'ring-2 ring-white/20 ring-offset-4 ring-offset-black' : ''}
        `}>
          {/* Category and time */}
          <div className="flex items-center justify-between mb-3">
            <span className={`
              text-xs font-medium uppercase tracking-wider
              ${getCategoryColor(story.category)}
            `}>
              {story.category}
            </span>
            <span className="text-xs text-white/40">
              {story.readTime} min read
            </span>
          </div>

          {/* Headline */}
          <h2 className="text-xl font-serif text-white/90 leading-tight mb-3 line-clamp-2 group-hover:text-white transition-colors">
            {story.headline}
          </h2>

          {/* Summary */}
          <p className="text-white/60 leading-relaxed line-clamp-3 text-sm mb-4">
            {story.summary}
          </p>

          {/* Depth indicators - subtle promise of more */}
          <div className="flex items-center gap-4">
            {story.hasTimeline && (
              <div className="flex items-center gap-1.5 text-white/30 hover:text-white/50 transition-colors">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-xs">Timeline</span>
              </div>
            )}
            {story.hasPerspectives && (
              <div className="flex items-center gap-1.5 text-white/30 hover:text-white/50 transition-colors">
                <BarChart3 className="w-3.5 h-3.5" />
                <span className="text-xs">Perspectives</span>
              </div>
            )}
            {story.hasSocialPulse && (
              <div className="flex items-center gap-1.5 text-white/30 hover:text-white/50 transition-colors">
                <TrendingUp className="w-3.5 h-3.5" />
                <span className="text-xs">Social pulse</span>
              </div>
            )}
          </div>
        </div>
      </motion.article>

      {/* Expanded state */}
      <AnimatePresence>
        {isExpanded && (
          <ExpandedStoryView 
            story={story} 
            onClose={() => setIsExpanded(false)} 
          />
        )}
      </AnimatePresence>
    </>
  );
}