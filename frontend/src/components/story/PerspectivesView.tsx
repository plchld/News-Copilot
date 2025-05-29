'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface NewsSource {
  id: string;
  name: string;
  position: number; // 0-100 percentage on spectrum
  analysis: string;
}

interface PerspectivesData {
  sources: NewsSource[];
  progressiveQuote: string;
  conservativeQuote: string;
  progressiveTerms: string[];
  conservativeTerms: string[];
}

interface PerspectivesViewProps {
  perspectives: PerspectivesData;
}

export default function PerspectivesView({ perspectives }: PerspectivesViewProps) {
  const [selectedSource, setSelectedSource] = useState<NewsSource | null>(null);

  return (
    <div>
      <div className="mb-8">
        <h3 className="text-lg font-medium text-white mb-2">Different Angles</h3>
        <p className="text-white/60 text-sm">
          How various sources frame this story
        </p>
      </div>

      {/* Spectrum visualization */}
      <div className="relative h-20 mb-12">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-red-500/10 rounded-lg" />

        {/* Spectrum line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/10" />

        {/* Source positions */}
        {perspectives.sources.map((source, i) => (
          <motion.button
            key={source.id}
            className="absolute top-1/2 -translate-y-1/2"
            style={{ left: `${source.position}%` }}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setSelectedSource(source)}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
          >
            <div className={`
              w-3 h-3 rounded-full bg-white shadow-lg transition-all duration-300
              ${selectedSource?.id === source.id ? 'ring-4 ring-white/20 scale-125' : 'hover:scale-110'}
            `} />
            <span className="absolute top-6 left-1/2 -translate-x-1/2 text-xs text-white/60 whitespace-nowrap">
              {source.name}
            </span>
          </motion.button>
        ))}

        {/* Labels */}
        <span className="absolute left-0 top-0 text-xs text-blue-400/80 font-medium">Progressive</span>
        <span className="absolute right-0 top-0 text-xs text-red-400/80 font-medium">Conservative</span>
      </div>

      {/* Key differences */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <motion.div 
          className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h4 className="text-sm font-medium text-blue-400 mb-2">Progressive framing</h4>
          <p className="text-white/70 text-sm italic mb-2">"{perspectives.progressiveQuote}"</p>
          <p className="text-white/50 text-xs">
            Key terms: {perspectives.progressiveTerms.join(', ')}
          </p>
        </motion.div>

        <motion.div 
          className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h4 className="text-sm font-medium text-red-400 mb-2">Conservative framing</h4>
          <p className="text-white/70 text-sm italic mb-2">"{perspectives.conservativeQuote}"</p>
          <p className="text-white/50 text-xs">
            Key terms: {perspectives.conservativeTerms.join(', ')}
          </p>
        </motion.div>
      </div>

      {/* Selected source details */}
      {selectedSource && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="p-4 glass-subtle-premium rounded-lg"
        >
          <h4 className="font-medium text-white mb-2">{selectedSource.name}'s Coverage</h4>
          <p className="text-white/70 text-sm leading-relaxed">{selectedSource.analysis}</p>
        </motion.div>
      )}
    </div>
  );
}