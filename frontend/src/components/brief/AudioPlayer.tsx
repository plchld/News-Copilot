'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, SkipForward, X } from 'lucide-react';

interface Story {
  id: string;
  headline: string;
  summary: string;
  readTime: number;
  category: string;
}

interface AudioPlayerProps {
  stories: Story[];
  onClose: () => void;
}

export default function AudioPlayer({ stories, onClose }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStoryIndex, setCurrentStoryIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const currentStory = stories[currentStoryIndex];

  // Simulate audio progress
  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            if (currentStoryIndex < stories.length - 1) {
              setCurrentStoryIndex(currentStoryIndex + 1);
              return 0;
            } else {
              setIsPlaying(false);
              return 100;
            }
          }
          return prev + 1;
        });
      }, 100);
      return () => clearInterval(interval);
    }
    return undefined;
  }, [isPlaying, currentStoryIndex, stories.length]);

  const handleSkip = (): void => {
    if (currentStoryIndex < stories.length - 1) {
      setCurrentStoryIndex(currentStoryIndex + 1);
      setProgress(0);
    }
  };

  return (
    <motion.div
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      exit={{ y: 100 }}
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-800 bg-gray-900 p-4"
    >
      <div className="mx-auto max-w-4xl">
        <div className="flex items-center gap-4">
          {/* Play/Pause button */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex h-12 w-12 items-center justify-center rounded-full bg-primary transition-colors hover:bg-primary/90"
          >
            {isPlaying ? (
              <Pause className="h-5 w-5" />
            ) : (
              <Play className="ml-0.5 h-5 w-5" />
            )}
          </button>

          {/* Story info */}
          <div className="min-w-0 flex-1">
            <p className="text-sm text-gray-400">
              Story {currentStoryIndex + 1} of {stories.length}
            </p>
            <h3 className="truncate font-medium text-white">
              {currentStory.headline}
            </h3>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleSkip}
              disabled={currentStoryIndex >= stories.length - 1}
              className="rounded-lg p-2 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <SkipForward className="h-5 w-5" />
            </button>
            <button className="rounded-lg bg-white/10 px-3 py-1 text-sm transition-colors hover:bg-white/20">
              1.5x
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-2 transition-colors hover:bg-white/10"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-gray-800">
          <motion.div
            className="h-full bg-primary"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </motion.div>
  );
}
