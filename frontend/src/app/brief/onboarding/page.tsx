'use client';

import { useState, useRef } from 'react';
import { motion, useMotionValue, useTransform, PanInfo } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { ThemeToggle } from '@/components/ui/theme-toggle';

// Mock onboarding stories for calibration
const onboardingStories = [
  {
    id: 1,
    category: 'tech',
    headline: 'EU passes groundbreaking AI regulation',
    preview:
      'New rules aim to balance innovation with safety, affecting major tech companies globally.',
    color: '#3B82F6',
  },
  {
    id: 2,
    category: 'politics',
    headline: 'Greek parliament debates economic reforms',
    preview:
      "Key legislation could reshape the country's fiscal policy for the next decade.",
    color: '#EF4444',
  },
  {
    id: 3,
    category: 'business',
    headline: 'Startup funding reaches record highs',
    preview:
      'Venture capital investments surge despite global economic uncertainty.',
    color: '#10B981',
  },
  {
    id: 4,
    category: 'world',
    headline: 'Climate summit yields new commitments',
    preview:
      'Nations pledge ambitious targets for carbon reduction and renewable energy.',
    color: '#8B5CF6',
  },
  {
    id: 5,
    category: 'culture',
    headline: 'Ancient Greek artifacts return home',
    preview:
      'Museum repatriation marks significant cultural heritage milestone.',
    color: '#F59E0B',
  },
  {
    id: 6,
    category: 'health',
    headline: 'Mediterranean diet study shows benefits',
    preview:
      'New research confirms long-term health advantages of traditional eating patterns.',
    color: '#EC4899',
  },
  {
    id: 7,
    category: 'science',
    headline: 'Space mission discovers water on Mars',
    preview:
      'Breakthrough finding could revolutionize our understanding of planetary habitability.',
    color: '#06B6D4',
  },
];

export default function OnboardingPage() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [exitDirection, setExitDirection] = useState<'left' | 'right' | null>(
    null,
  );
  const [_preferences, setPreferences] = useState<Record<string, number>>({});
  const constraintsRef = useRef(null);
  const router = useRouter();

  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0, 1, 1, 1, 0]);
  const swipeOpacityRight = useTransform(x, [0, 100], [0, 0.3]);
  const swipeOpacityLeft = useTransform(x, [-100, 0], [0.3, 0]);

  const handleDragEnd = (
    _event: MouseEvent | TouchEvent | PointerEvent,
    info: PanInfo,
  ) => {
    const threshold = 100;
    if (Math.abs(info.offset.x) > threshold) {
      const direction = info.offset.x > 0 ? 'right' : 'left';
      setExitDirection(direction);

      // Record preference (right = interested, left = not interested)
      const story = onboardingStories[currentIndex];
      setPreferences((prev) => ({
        ...prev,
        [story.category]: direction === 'right' ? 1 : 0,
      }));

      // Move to next story
      setTimeout(() => {
        setCurrentIndex((prev) => prev + 1);
        setExitDirection(null);
        x.set(0);
      }, 200);
    } else {
      // Snap back to center
      x.set(0);
    }
  };

  const handleContinue = () => {
    // Save preferences and continue to daily brief
    router.push('/brief/daily');
  };

  if (currentIndex >= onboardingStories.length) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6">
        {/* Theme toggle in top right */}
        <div className="absolute top-6 right-6 z-20">
          <ThemeToggle />
        </div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md text-center"
        >
          <div className="mb-6 text-6xl">✨</div>
          <h2 className="mb-4 text-2xl font-serif text-[var(--text-primary)]">
            Perfect! We've calibrated your brief.
          </h2>
          <p className="mb-8 text-[var(--text-tertiary)]">
            Your personalized daily brief is ready, tailored to your interests.
          </p>
          <button
            onClick={handleContinue}
            className="glass-button-premium no-select group"
          >
            <span className="relative z-10">View Your Brief</span>
            <div className="shine" />
          </button>
        </motion.div>
      </div>
    );
  }

  const visibleStories = onboardingStories.slice(
    currentIndex,
    currentIndex + 3,
  );

  return (
    <div className="min-h-screen">
      {/* Theme toggle in top right */}
      <div className="absolute top-6 right-6 z-20">
        <ThemeToggle />
      </div>
      
      {/* Header */}
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-2xl font-serif text-[var(--text-primary)]">
            Calibrate Your Brief
          </h1>
          <p className="text-[var(--text-tertiary)]">
            Swipe right for stories you'd want to read, left to skip
          </p>
        </div>

        {/* Progress indicators */}
        <div className="mb-12 flex justify-center gap-2">
          {onboardingStories.map((_, index) => (
            <div
              key={index}
              className={`progress-dot-premium ${index <= currentIndex ? 'active' : ''}`}
            />
          ))}
        </div>

        {/* Card stack */}
        <div className="mx-auto max-w-md">
          <div className="relative h-[600px]" ref={constraintsRef}>
            {visibleStories.map((story, index) => {
              const isTop = index === 0;

              return (
                <motion.div
                  key={story.id}
                  className="absolute inset-x-0"
                  initial={{
                    scale: 1 - index * 0.05,
                    y: index * 10,
                    opacity: index === 0 ? 1 : 0.9 - index * 0.1,
                    zIndex: visibleStories.length - index,
                  }}
                  animate={{
                    scale: 1 - index * 0.05,
                    y: index * 10,
                    opacity: index === 0 ? 1 : 0.9 - index * 0.1,
                    zIndex: visibleStories.length - index,
                  }}
                  exit={
                    index === 0 && exitDirection
                      ? {
                          x: exitDirection === 'right' ? 300 : -300,
                          opacity: 0,
                          scale: 0.8,
                          transition: { duration: 0.2 },
                        }
                      : undefined
                  }
                  drag={isTop ? 'x' : false}
                  dragConstraints={constraintsRef}
                  dragElastic={0.2}
                  onDragEnd={isTop ? handleDragEnd : undefined}
                  style={isTop ? { x, rotate, opacity } : undefined}
                >
                  <div
                    className="h-full w-full cursor-grab rounded-2xl glass-premium p-6 shadow-2xl active:cursor-grabbing"
                    style={{
                      transform: `rotate(${index === 1 ? -2 : index === 2 ? 2 : 0}deg)`,
                    }}
                  >
                    {/* Category badge */}
                    <div className="mb-4">
                      <span
                        className="inline-block rounded-md border px-3 py-1 text-xs font-medium uppercase tracking-wider"
                        style={{
                          color: story.color,
                          backgroundColor: `${story.color}1A`,
                          borderColor: `${story.color}33`,
                        }}
                      >
                        {story.category}
                      </span>
                    </div>

                    {/* Headline */}
                    <h3 className="mb-4 text-2xl font-serif leading-tight text-white">
                      {story.headline}
                    </h3>

                    {/* Preview */}
                    <p className="leading-relaxed text-gray-400">
                      {story.preview}
                    </p>

                    {/* Swipe indicators (only on top card) */}
                    {isTop && (
                      <>
                        {/* Green overlay for right swipe */}
                        <motion.div
                          className="swipe-overlay-right absolute inset-0 rounded-2xl"
                          style={{ opacity: swipeOpacityRight }}
                        />
                        {/* Red overlay for left swipe */}
                        <motion.div
                          className="swipe-overlay-left absolute inset-0 rounded-2xl"
                          style={{ opacity: swipeOpacityLeft }}
                        />
                      </>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Swipe hints */}
          <div className="mt-8 flex justify-center gap-12 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-red-500/20 flex items-center justify-center">
                ←
              </div>
              Skip
            </div>
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-green-500/20 flex items-center justify-center">
                →
              </div>
              Interested
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
