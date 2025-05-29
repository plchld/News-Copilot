'use client';

import { motion } from 'framer-motion';

interface Perspective {
  source: string;
  stance: 'supportive' | 'concerned' | 'neutral';
  quote: string;
}

interface PerspectivesViewProps {
  perspectives: Perspective[];
}

export default function PerspectivesView({
  perspectives,
}: PerspectivesViewProps) {
  const getStanceColor = (stance: string) => {
    switch (stance) {
      case 'supportive':
        return 'bg-green-500/10 border-green-500/20 text-green-400';
      case 'concerned':
        return 'bg-red-500/10 border-red-500/20 text-red-400';
      case 'neutral':
        return 'bg-gray-500/10 border-gray-500/20 text-gray-400';
      default:
        return 'bg-gray-500/10 border-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Spectrum visualization */}
      <div className="glass mb-8 rounded-lg p-6">
        <h3 className="mb-4 text-sm font-medium text-gray-400">
          Opinion Spectrum
        </h3>
        <div className="relative h-2 rounded-full bg-gradient-to-r from-red-500/20 via-gray-500/20 to-green-500/20">
          {perspectives.map((perspective, index) => {
            const position =
              perspective.stance === 'concerned'
                ? 20
                : perspective.stance === 'supportive'
                  ? 80
                  : 50;
            return (
              <motion.div
                key={index}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1, type: 'spring' }}
                className="absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full border-2 border-gray-900 bg-white"
                style={{ left: `${position}%` }}
              />
            );
          })}
        </div>
        <div className="mt-2 flex justify-between text-xs text-gray-500">
          <span>Conservative</span>
          <span>Liberal</span>
        </div>
      </div>

      {/* Perspective cards */}
      <div className="grid gap-4">
        {perspectives.map((perspective, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass rounded-lg p-6"
          >
            <div className="mb-3 flex items-start justify-between">
              <h3 className="font-medium text-white">{perspective.source}</h3>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${getStanceColor(perspective.stance)} border`}
              >
                {perspective.stance}
              </span>
            </div>
            <blockquote className="italic text-gray-300">
              "{perspective.quote}"
            </blockquote>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
