'use client';

import { motion } from 'framer-motion';
import { TrendingUp, HelpCircle, AlertCircle } from 'lucide-react';

// Misconception interface now inline in SocialData

interface SocialData {
  topQuestion: string;
  questionAnswer: string;
  misconception: {
    claim: string;
    correction: string;
  };
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

interface SocialPulseViewProps {
  socialData: SocialData;
}

export default function SocialPulseView({ socialData }: SocialPulseViewProps) {
  const getTotalSentiment = () => {
    return socialData.sentiment.positive + socialData.sentiment.neutral + socialData.sentiment.negative;
  };

  const getPercentage = (value: number) => {
    return Math.round((value / getTotalSentiment()) * 100);
  };

  return (
    <div className="space-y-8">
      {/* Sentiment Distribution */}
      <motion.div 
        className="p-4 glass-subtle-premium rounded-lg"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center gap-3 mb-4">
          <TrendingUp className="w-5 h-5 text-white/60" />
          <h4 className="text-white font-medium">Public Sentiment</h4>
        </div>
        
        <div className="space-y-3">
          {Object.entries(socialData.sentiment).map(([type, value], index) => {
            const percentage = getPercentage(value);
            return (
              <div key={type} className="flex items-center gap-3">
                <span className="text-white/60 text-sm w-20 capitalize">{type}</span>
                <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ 
                      duration: 0.8, 
                      ease: 'easeOut',
                      delay: 0.5 + index * 0.1, 
                    }}
                    className={`h-full rounded-full ${
                      type === 'positive' ? 'bg-green-500/60' :
                      type === 'negative' ? 'bg-red-500/60' :
                      'bg-gray-500/60'
                    }`}
                  />
                </div>
                <span className="text-white/40 text-sm w-10 text-right">{percentage}%</span>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Top question */}
      {socialData.topQuestion && (
        <motion.div 
          className="p-4 glass-subtle-premium rounded-lg border border-white/[0.05]"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-white/40 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-white/40 mb-1">Most asked question</p>
              <p className="text-white/90 font-medium mb-2">{socialData.topQuestion}</p>
              {socialData.questionAnswer && (
                <p className="text-white/60 text-sm leading-relaxed">{socialData.questionAnswer}</p>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Common misconception */}
      {socialData.misconception && (
        <motion.div 
          className="p-4 bg-red-500/5 rounded-lg border border-red-500/20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-red-400 mb-1 font-medium">Common misconception</p>
              <p className="text-white/90 mb-2 font-medium">{socialData.misconception.claim}</p>
              <p className="text-white/60 text-sm leading-relaxed">{socialData.misconception.correction}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Sentiment snapshot */}
      {socialData.sentiment && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <p className="text-xs text-white/40 mb-3 font-medium">General sentiment</p>
          <div className="space-y-2">
            {Object.entries(socialData.sentiment).map(([label, percentage], index) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-white/60 text-sm w-20 capitalize">{label}</span>
                <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ 
                      duration: 0.8, 
                      ease: 'easeOut',
                      delay: 0.5 + index * 0.1, 
                    }}
                    className="h-full bg-gradient-to-r from-white/20 to-white/40 rounded-full"
                  />
                </div>
                <span className="text-white/40 text-sm w-10 text-right">{percentage}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}