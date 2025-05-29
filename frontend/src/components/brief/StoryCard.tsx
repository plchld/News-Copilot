'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Clock, MessageCircle, BarChart } from 'lucide-react';

interface StoryCardProps {
  story: {
    id: string;
    headline: string;
    summary: string;
    readTime: number;
    category: string;
    hasTimeline?: boolean;
    hasPerspectives?: boolean;
    socialPulse?: {
      trendingLevel: 'low' | 'medium' | 'high';
      topQuestion?: string;
    };
    fullContent?: string;
  };
  isExpanded: boolean;
  onExpand: () => void;
  onCollapse: () => void;
  onDeepDive: () => void;
}

export default function StoryCard({
  story,
  isExpanded,
  onExpand,
  onCollapse,
  onDeepDive,
}: StoryCardProps) {
  const getCategoryColor = (category: string) => {
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

  const handleClick = () => {
    if (isExpanded) {
      onCollapse();
    } else {
      onExpand();
    }
  };

  return (
    <motion.article
      layout
      className="glass-subtle group cursor-pointer overflow-hidden rounded-xl"
      onClick={handleClick}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="p-6">
        {/* Header */}
        <div className="mb-4 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${getCategoryColor(story.category)} border`}
            >
              {story.category}
            </span>
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Clock className="h-3 w-3" />
              {story.readTime} min
            </span>
          </div>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-5 w-5 text-gray-400" />
          </motion.div>
        </div>

        {/* Headline */}
        <h3 className="mb-3 font-serif text-xl leading-tight text-white">
          {story.headline}
        </h3>

        {/* Summary */}
        <p className="leading-relaxed text-gray-300">{story.summary}</p>

        {/* Indicators */}
        <div className="mt-4 flex items-center gap-4">
          {story.hasPerspectives && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <BarChart className="h-3 w-3" />
              <span>Perspectives</span>
            </div>
          )}
          {story.hasTimeline && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>Timeline</span>
            </div>
          )}
          {story.socialPulse && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <MessageCircle className="h-3 w-3" />
              <span>Social pulse</span>
            </div>
          )}
        </div>

        {/* Expanded content */}
        <AnimatePresence>
          {isExpanded && story.fullContent && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="mt-6 border-t border-gray-800 pt-6">
                <div className="prose prose-invert max-w-none">
                  {story.fullContent.split('\n\n').map((paragraph, index) => (
                    <p
                      key={index}
                      className="mb-4 leading-relaxed text-gray-300"
                    >
                      {paragraph}
                    </p>
                  ))}
                </div>

                {/* Deep dive button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeepDive();
                  }}
                  className="mt-6 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium transition-all hover:border-white/20 hover:bg-white/10"
                >
                  Explore deeper
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.article>
  );
}
