'use client';

import { motion } from 'framer-motion';
import { TrendingUp, HelpCircle, AlertCircle, BarChart2 } from 'lucide-react';

interface SocialPulseViewProps {
  socialPulse: {
    trendingLevel: 'low' | 'medium' | 'high';
    topQuestion?: string;
    misconception?: string;
    sentiment?: {
      concerned: number;
      supportive: number;
      neutral: number;
    };
  };
}

export default function SocialPulseView({ socialPulse }: SocialPulseViewProps) {
  const getTrendingColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-red-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

  const mockSentiment = socialPulse.sentiment || {
    concerned: 45,
    supportive: 30,
    neutral: 25,
  };

  return (
    <div className="space-y-6">
      {/* Trending level */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-lg p-6"
      >
        <div className="mb-2 flex items-center gap-3">
          <TrendingUp
            className={`h-5 w-5 ${getTrendingColor(socialPulse.trendingLevel)}`}
          />
          <h3 className="font-medium text-white">Trending Level</h3>
        </div>
        <p
          className={`text-2xl font-bold ${getTrendingColor(socialPulse.trendingLevel)} capitalize`}
        >
          {socialPulse.trendingLevel}
        </p>
        <p className="mt-1 text-sm text-gray-400">
          This story is generating{' '}
          {socialPulse.trendingLevel === 'high'
            ? 'significant'
            : socialPulse.trendingLevel === 'medium'
              ? 'moderate'
              : 'limited'}{' '}
          discussion online
        </p>
      </motion.div>

      {/* Top question */}
      {socialPulse.topQuestion && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-lg p-6"
        >
          <div className="mb-3 flex items-center gap-3">
            <HelpCircle className="h-5 w-5 text-blue-400" />
            <h3 className="font-medium text-white">Top Question People Ask</h3>
          </div>
          <p className="text-lg text-gray-300">"{socialPulse.topQuestion}"</p>
        </motion.div>
      )}

      {/* Common misconception */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass rounded-lg p-6"
      >
        <div className="mb-3 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-400" />
          <h3 className="font-medium text-white">Common Misconception</h3>
        </div>
        <p className="mb-3 text-gray-300">
          "This only applies to large tech companies"
        </p>
        <details className="group">
          <summary className="cursor-pointer text-sm text-blue-400 transition-colors hover:text-blue-300">
            Why this is incorrect
          </summary>
          <p className="mt-2 text-sm text-gray-400">
            The regulations apply to any company processing personal data above
            certain thresholds, including many medium-sized businesses and
            startups.
          </p>
        </details>
      </motion.div>

      {/* Sentiment snapshot */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass rounded-lg p-6"
      >
        <div className="mb-4 flex items-center gap-3">
          <BarChart2 className="h-5 w-5 text-purple-400" />
          <h3 className="font-medium text-white">Sentiment Snapshot</h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="mb-1 flex justify-between">
              <span className="text-sm text-gray-400">Concerned</span>
              <span className="text-sm text-gray-300">
                {mockSentiment.concerned}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-gray-800">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${mockSentiment.concerned}%` }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="h-full bg-red-500"
              />
            </div>
          </div>
          <div>
            <div className="mb-1 flex justify-between">
              <span className="text-sm text-gray-400">Supportive</span>
              <span className="text-sm text-gray-300">
                {mockSentiment.supportive}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-gray-800">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${mockSentiment.supportive}%` }}
                transition={{ duration: 0.5, delay: 0.5 }}
                className="h-full bg-green-500"
              />
            </div>
          </div>
          <div>
            <div className="mb-1 flex justify-between">
              <span className="text-sm text-gray-400">Neutral</span>
              <span className="text-sm text-gray-300">
                {mockSentiment.neutral}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-gray-800">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${mockSentiment.neutral}%` }}
                transition={{ duration: 0.5, delay: 0.6 }}
                className="h-full bg-gray-500"
              />
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
