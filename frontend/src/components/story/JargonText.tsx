'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface JargonTerm {
  word: string;
  explanation: string;
}

interface JargonTextProps {
  content: string;
  onJargonClick?: (term: JargonTerm) => void;
}

// Mock jargon detection - in real app this would be AI-powered
const detectJargon = (word: string): JargonTerm | null => {
  const jargonTerms: Record<string, string> = {
    'algorithm': 'A set of rules or instructions given to a computer to help it learn on its own',
    'blockchain': 'A distributed digital ledger that records transactions across multiple computers',
    'GDP': 'Gross Domestic Product - the total value of goods and services produced in a country',
    'inflation': 'The rate at which the general level of prices for goods and services is rising',
    'quantum': 'Relating to the smallest possible discrete unit of any physical property',
    'neural': 'Related to artificial networks that mimic the human brain for machine learning',
    'cryptocurrency': 'Digital or virtual currency secured by cryptography and blockchain technology',
  };

  const cleanWord = word.toLowerCase().replace(/[.,!?;:]/, '');
  if (jargonTerms[cleanWord]) {
    return {
      word: cleanWord,
      explanation: jargonTerms[cleanWord],
    };
  }
  return null;
};

export default function JargonText({ content, onJargonClick }: JargonTextProps) {
  const [hoveredTerm, setHoveredTerm] = useState<JargonTerm | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = (event: React.MouseEvent, term: JargonTerm) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setTooltipPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
    });
    setHoveredTerm(term);
  };

  const handleMouseLeave = () => {
    setHoveredTerm(null);
  };

  const renderContent = () => {
    return content.split(' ').map((word, i) => {
      const jargonTerm = detectJargon(word);
      if (jargonTerm) {
        return (
          <span key={i}>
            <button
              className="relative inline-block group transition-all duration-200"
              onMouseEnter={(e) => handleMouseEnter(e, jargonTerm)}
              onMouseLeave={handleMouseLeave}
              onClick={() => onJargonClick?.(jargonTerm)}
            >
              <span className="border-b border-dotted border-white/40 group-hover:border-white/60 group-hover:text-white/90 transition-colors">
                {word}
              </span>
            </button>
            {' '}
          </span>
        );
      }
      return word + ' ';
    });
  };

  return (
    <>
      <p className="text-white/80 leading-relaxed">{renderContent()}</p>
      
      {/* Tooltip */}
      <AnimatePresence>
        {hoveredTerm && (
          <motion.div
            ref={tooltipRef}
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            style={{
              position: 'fixed',
              left: tooltipPosition.x,
              top: tooltipPosition.y,
              transform: 'translateX(-50%) translateY(-100%)',
              zIndex: 1000,
            }}
            className="glass-premium rounded-lg p-3 max-w-xs shadow-2xl border border-white/10"
          >
            <h4 className="text-white font-medium text-sm mb-1">{hoveredTerm.word}</h4>
            <p className="text-white/70 text-xs leading-relaxed">{hoveredTerm.explanation}</p>
            <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-white/5 border-r border-b border-white/10 rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Modal for mobile/expanded jargon explanations
interface JargonModalProps {
  term: JargonTerm | null;
  onClose: () => void;
}

export function JargonModal({ term, onClose }: JargonModalProps) {
  if (!term) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end justify-center px-6 pb-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 20, opacity: 0 }}
        className="glass-premium rounded-2xl p-6 max-w-md w-full border border-white/[0.1] shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-lg font-medium text-white mb-2 capitalize">{term.word}</h3>
        <p className="text-white/70 text-sm leading-relaxed mb-4">
          {term.explanation}
        </p>
        <button
          onClick={onClose}
          className="w-full py-3 bg-white/10 hover:bg-white/15 rounded-lg text-sm font-medium transition-colors"
        >
          Got it
        </button>
      </motion.div>
    </motion.div>
  );
}