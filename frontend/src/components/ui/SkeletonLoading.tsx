'use client';

import { motion } from 'framer-motion';

// Skeleton for story cards during loading
export function StoryCardSkeleton() {
  return (
    <motion.div
      className="story-card-premium animate-pulse"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* Category and time skeleton */}
      <div className="flex items-center justify-between mb-3">
        <div className="h-3 bg-white/10 rounded w-16" />
        <div className="h-3 bg-white/10 rounded w-20" />
      </div>

      {/* Headline skeleton */}
      <div className="space-y-2 mb-3">
        <div className="h-5 bg-white/10 rounded w-full" />
        <div className="h-5 bg-white/10 rounded w-3/4" />
      </div>

      {/* Summary skeleton */}
      <div className="space-y-2 mb-4">
        <div className="h-4 bg-white/10 rounded w-full" />
        <div className="h-4 bg-white/10 rounded w-full" />
        <div className="h-4 bg-white/10 rounded w-1/2" />
      </div>

      {/* Depth indicators skeleton */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className="w-3.5 h-3.5 bg-white/10 rounded" />
          <div className="h-3 bg-white/10 rounded w-12" />
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3.5 h-3.5 bg-white/10 rounded" />
          <div className="h-3 bg-white/10 rounded w-16" />
        </div>
      </div>
    </motion.div>
  );
}

// Skeleton for brief loading
export function BriefLoadingSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <StoryCardSkeleton key={i} />
      ))}
    </div>
  );
}

// Skeleton for timeline loading
export function TimelineLoadingSkeleton() {
  return (
    <div className="relative">
      {/* Header skeleton */}
      <div className="mb-8">
        <div className="h-6 bg-white/10 rounded w-32 mb-2" />
        <div className="h-4 bg-white/10 rounded w-48" />
      </div>

      {/* Timeline skeleton */}
      <div className="relative">
        <div className="absolute left-8 top-0 bottom-0 w-px bg-white/10" />
        
        <div className="space-y-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="relative flex items-start gap-4">
              <div className="w-4 h-4 rounded-full bg-white/10 border-2 border-white/20" />
              <div className="flex-1 space-y-2">
                <div className="h-3 bg-white/10 rounded w-20" />
                <div className="h-4 bg-white/10 rounded w-3/4" />
                <div className="h-3 bg-white/10 rounded w-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Skeleton for perspectives loading
export function PerspectivesLoadingSkeleton() {
  return (
    <div>
      {/* Header skeleton */}
      <div className="mb-8">
        <div className="h-6 bg-white/10 rounded w-32 mb-2" />
        <div className="h-4 bg-white/10 rounded w-56" />
      </div>

      {/* Spectrum skeleton */}
      <div className="relative h-20 mb-12">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-red-500/5 rounded-lg" />
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/10" />
        
        {/* Source dots skeleton */}
        {[25, 50, 75].map((position, i) => (
          <div
            key={i}
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white/10"
            style={{ left: `${position}%` }}
          />
        ))}
      </div>

      {/* Comparison skeleton */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
          <div className="h-4 bg-white/10 rounded w-32 mb-2" />
          <div className="h-3 bg-white/10 rounded w-full mb-2" />
          <div className="h-3 bg-white/10 rounded w-24" />
        </div>
        <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg">
          <div className="h-4 bg-white/10 rounded w-32 mb-2" />
          <div className="h-3 bg-white/10 rounded w-full mb-2" />
          <div className="h-3 bg-white/10 rounded w-24" />
        </div>
      </div>
    </div>
  );
}

// Skeleton for social pulse loading
export function SocialPulseLoadingSkeleton() {
  return (
    <div className="space-y-8">
      {/* Trending level skeleton */}
      <div className="flex items-center gap-4 p-4 glass-subtle-premium rounded-lg">
        <div className="w-12 h-12 rounded-lg bg-white/10" />
        <div className="space-y-2">
          <div className="h-4 bg-white/10 rounded w-32" />
          <div className="h-3 bg-white/10 rounded w-48" />
        </div>
      </div>

      {/* Question skeleton */}
      <div className="p-4 glass-subtle-premium rounded-lg border border-white/[0.05]">
        <div className="flex items-start gap-3">
          <div className="w-5 h-5 bg-white/10 rounded mt-0.5" />
          <div className="flex-1 space-y-2">
            <div className="h-3 bg-white/10 rounded w-32" />
            <div className="h-4 bg-white/10 rounded w-full" />
            <div className="h-3 bg-white/10 rounded w-3/4" />
          </div>
        </div>
      </div>

      {/* Sentiment skeleton */}
      <div className="space-y-3">
        <div className="h-3 bg-white/10 rounded w-24" />
        <div className="space-y-2">
          {['Positive', 'Neutral', 'Negative'].map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="h-3 bg-white/10 rounded w-16" />
              <div className="flex-1 h-2 bg-white/10 rounded-full" />
              <div className="h-3 bg-white/10 rounded w-8" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Generic shimmer effect for loading states
export function ShimmerEffect() {
  return (
    <div className="animate-pulse">
      <div className="shimmer-bg" />
      <style jsx>{`
        .shimmer-bg {
          background: linear-gradient(
            90deg,
            rgba(255, 255, 255, 0.05) 0%,
            rgba(255, 255, 255, 0.1) 50%,
            rgba(255, 255, 255, 0.05) 100%
          );
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>
    </div>
  );
}