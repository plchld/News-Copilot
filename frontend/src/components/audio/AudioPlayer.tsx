'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, SkipForward, SkipBack, Volume2, VolumeX } from 'lucide-react';

interface Story {
  id: string;
  headline: string;
  duration?: number; // in seconds
}

interface AudioPlayerProps {
  stories: Story[];
  currentIndex: number;
  onStoryChange: (index: number) => void;
  isVisible?: boolean;
}

export default function AudioPlayer({ 
  stories, 
  currentIndex, 
  onStoryChange,
  isVisible = true, 
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(1);
  // Volume control removed for now
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const currentStory = stories[currentIndex];
  const duration = currentStory?.duration || 180; // Default 3 minutes

  // Simulate audio progress
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentTime((prev) => {
        const newTime = prev + speed;
        setProgress((newTime / duration) * 100);
        
        if (newTime >= duration) {
          // Auto-advance to next story
          if (currentIndex < stories.length - 1) {
            onStoryChange(currentIndex + 1);
            setCurrentTime(0);
            setProgress(0);
          } else {
            setIsPlaying(false);
            setCurrentTime(0);
            setProgress(0);
          }
          return 0;
        }
        return newTime;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, speed, duration, currentIndex, stories.length, onStoryChange]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSpeedChange = () => {
    const speeds = [1, 1.25, 1.5, 2];
    const currentSpeedIndex = speeds.indexOf(speed);
    const nextSpeed = speeds[(currentSpeedIndex + 1) % speeds.length];
    setSpeed(nextSpeed);
  };

  const handleVolumeToggle = () => {
    setIsMuted(!isMuted);
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const newProgress = (clickX / rect.width) * 100;
    setProgress(newProgress);
    setCurrentTime((newProgress / 100) * duration);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      className="fixed bottom-0 inset-x-0 z-30 glass-premium border-t border-white/[0.05]"
    >
      <div className="max-w-4xl mx-auto px-6 py-4">
        {/* Progress bars for all stories */}
        <div className="flex gap-1 mb-4">
          {stories.map((_, i) => (
            <div
              key={i}
              className={`
                flex-1 h-1 rounded-full overflow-hidden transition-all duration-300
                ${i < currentIndex ? 'bg-white/40' : 'bg-white/10'}
              `}
            >
              {i === currentIndex && (
                <motion.div
                  className="h-full bg-gradient-to-r from-white/60 to-white/80 rounded-full"
                  style={{ width: `${progress}%` }}
                  transition={{ duration: 0.1 }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Main controls */}
        <div className="flex items-center gap-4">
          {/* Skip back */}
          <button
            onClick={() => currentIndex > 0 && onStoryChange(currentIndex - 1)}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={currentIndex === 0}
          >
            <SkipBack className="w-4 h-4" />
          </button>

          {/* Play/pause */}
          <button
            onClick={handlePlayPause}
            className="w-12 h-12 bg-white/10 hover:bg-white/15 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>

          {/* Skip forward */}
          <button
            onClick={() => currentIndex < stories.length - 1 && onStoryChange(currentIndex + 1)}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={currentIndex >= stories.length - 1}
          >
            <SkipForward className="w-4 h-4" />
          </button>

          {/* Story info */}
          <div className="flex-1 min-w-0 mx-4">
            <h4 className="text-white/90 font-medium truncate text-sm">
              {currentStory?.headline}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-white/40 text-xs">
                Story {currentIndex + 1} of {stories.length}
              </p>
              <span className="text-white/20">•</span>
              <p className="text-white/40 text-xs">
                {formatTime(currentTime)} / {formatTime(duration)}
              </p>
            </div>
          </div>

          {/* Secondary controls */}
          <div className="flex items-center gap-2">
            {/* Volume */}
            <button
              onClick={handleVolumeToggle}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              {isMuted ? (
                <VolumeX className="w-4 h-4" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>

            {/* Speed control */}
            <button
              onClick={handleSpeedChange}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/15 rounded-lg text-xs font-medium transition-colors"
            >
              {speed}x
            </button>
          </div>
        </div>

        {/* Progress bar (clickable) */}
        <div 
          className="mt-3 h-1 bg-white/10 rounded-full cursor-pointer"
          onClick={handleProgressClick}
        >
          <motion.div
            className="h-full bg-gradient-to-r from-white/60 to-white/80 rounded-full"
            style={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
      </div>
    </motion.div>
  );
}