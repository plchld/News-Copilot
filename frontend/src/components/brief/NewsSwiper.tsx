'use client';

import { useState, useRef } from 'react';
import {
  motion,
  useMotionValue,
  useTransform,
  AnimatePresence,
} from 'framer-motion';

interface Story {
  id: string;
  headline: string;
  source: string;
  category: string;
  imageUrl?: string;
  previewText: string;
}

interface NewsSwiperProps {
  stories: Story[];
  currentIndex: number;
  onSwipe: (
    direction: 'left' | 'right',
    storyId: string,
    category: string,
  ) => void;
}

export default function NewsSwiper({
  stories,
  currentIndex,
  onSwipe,
}: NewsSwiperProps) {
  const [exitDirection, setExitDirection] = useState<'left' | 'right' | null>(
    null,
  );
  const constraintsRef = useRef(null);

  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 0, 200], [-15, 0, 15]);
  const opacity = useTransform(
    x,
    [-200, -100, 0, 100, 200],
    [0.5, 1, 1, 1, 0.5],
  );

  // Create gradient transform for swipe indicators
  const swipeGradient = useTransform(
    x,
    [-200, -100, 0, 100, 200],
    [
      'linear-gradient(to right, rgba(239, 68, 68, 0.2), transparent)',
      'linear-gradient(to right, rgba(239, 68, 68, 0.1), transparent)',
      'transparent',
      'linear-gradient(to left, rgba(34, 197, 94, 0.1), transparent)',
      'linear-gradient(to left, rgba(34, 197, 94, 0.2), transparent)',
    ],
  );

  const handleDragEnd = (
    _event: MouseEvent | TouchEvent | PointerEvent,
    info: { offset: { x: number; y: number } },
  ): void => {
    const threshold = 100;
    if (Math.abs(info.offset.x) > threshold) {
      const direction = info.offset.x > 0 ? 'right' : 'left';
      setExitDirection(direction);
      setTimeout(() => {
        onSwipe(
          direction,
          stories[currentIndex].id,
          stories[currentIndex].category,
        );
        setExitDirection(null);
      }, 200);
    }
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      tech: 'bg-tech',
      politics: 'bg-politics',
      business: 'bg-business',
      world: 'bg-world',
      culture: 'bg-culture',
    };
    return colors[category.toLowerCase()] || 'bg-primary';
  };

  return (
    <div ref={constraintsRef} className="relative h-[600px] w-full">
      {/* Stack of cards */}
      <AnimatePresence mode="wait">
        {stories.slice(currentIndex, currentIndex + 3).map((story, index) => (
          <motion.div
            key={story.id}
            className="absolute inset-0"
            initial={{ scale: 1 - index * 0.05, y: index * 10 }}
            animate={{
              scale: 1 - index * 0.05,
              y: index * 10,
              opacity: index === 0 ? 1 : 0.9 - index * 0.1,
              zIndex: stories.length - index,
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
            drag={index === 0 ? 'x' : false}
            dragConstraints={constraintsRef}
            dragElastic={0.2}
            onDragEnd={index === 0 ? handleDragEnd : undefined}
            style={index === 0 ? { x, rotate, opacity } : undefined}
          >
            <div className="h-full w-full cursor-grab rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl active:cursor-grabbing">
              {/* Category badge */}
              <div className="mb-4">
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${getCategoryColor(story.category)} border border-current border-opacity-20 bg-opacity-10 text-white`}
                >
                  {story.category}
                </span>
              </div>

              {/* Image placeholder */}
              {story.imageUrl && (
                <div className="mb-6 h-48 overflow-hidden rounded-lg bg-gray-800">
                  <img
                    src={story.imageUrl}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                </div>
              )}

              {/* Content */}
              <div className="space-y-4">
                <h3 className="font-serif text-2xl leading-tight text-white">
                  {story.headline}
                </h3>
                <p className="text-sm text-gray-400">{story.source}</p>
                <p className="leading-relaxed text-gray-300">
                  {story.previewText}
                </p>
              </div>

              {/* Swipe indicators */}
              <motion.div
                className="pointer-events-none absolute inset-0 rounded-2xl"
                style={{
                  background: index === 0 ? swipeGradient : 'transparent',
                }}
              />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Action hints */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 flex justify-between px-8 pb-8">
        <motion.div
          className="flex items-center gap-2 text-red-500"
          style={{ opacity: useTransform(x, [-100, 0], [1, 0]) }}
        >
          <svg
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
          <span className="text-sm font-medium">Not interested</span>
        </motion.div>
        <motion.div
          className="flex items-center gap-2 text-green-500"
          style={{ opacity: useTransform(x, [0, 100], [0, 1]) }}
        >
          <span className="text-sm font-medium">Interested</span>
          <svg
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
        </motion.div>
      </div>
    </div>
  );
}
