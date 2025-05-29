'use client';

import { motion } from 'framer-motion';
import { TrendingUp, HelpCircle, AlertCircle } from 'lucide-react';

interface Misconception {
  claim: string;
  correction: string;
}

interface SocialData {
  trendingLevel: 'high' | 'medium' | 'low';
  trendingDescription: string;
  topQuestion?: string;
  questionAnswer?: string;
  misconception?: Misconception;
  sentiment?: Record<string, number>;
}

interface SocialPulseViewProps {
  socialData: SocialData;
}

export default function SocialPulseView({ socialData }: SocialPulseViewProps) {
  const getTrendingColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getTrendingBg = (level: string) => {
    switch (level) {
      case 'high': return 'bg-orange-500/20';
      case 'medium': return 'bg-yellow-500/20';
      default: return 'bg-gray-500/20';
    }
  };

  const getTrendingTitle = (level: string) => {
    switch (level) {
      case 'high': return 'Highly Trending';
      case 'medium': return 'Moderately Trending';
      default: return 'Limited Discussion';
    }
  };

  return (
    <div className="space-y-8">
      {/* Trending level */}
      <motion.div 
        className="flex items-center gap-4 p-4 glass-subtle-premium rounded-lg"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className={`
          w-12 h-12 rounded-lg flex items-center justify-center
          ${getTrendingBg(socialData.trendingLevel)}
        `}>
          <TrendingUp className={`w-6 h-6 ${getTrendingColor(socialData.trendingLevel)}`} />
        </div>
        <div>
          <h4 className="text-white font-medium">
            {getTrendingTitle(socialData.trendingLevel)}
          </h4>
          <p className="text-white/60 text-sm">{socialData.trendingDescription}</p>
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
                      ease: "easeOut",
                      delay: 0.5 + index * 0.1 
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