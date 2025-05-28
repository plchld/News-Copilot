'use client'

import { useAnalysisStore } from '@/lib/store'
import { ANALYSIS_TYPES, AnalysisType } from '@/lib/constants'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

const ANALYSIS_CONFIGS = {
  [ANALYSIS_TYPES.JARGON]: {
    title: 'Επεξήγηση Όρων',
    icon: '🔤',
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  },
  [ANALYSIS_TYPES.VIEWPOINTS]: {
    title: 'Εναλλακτικές Οπτικές',
    icon: '💭',
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200'
  },
  [ANALYSIS_TYPES.FACT_CHECK]: {
    title: 'Έλεγχος Γεγονότων',
    icon: '✓',
    color: 'from-green-500 to-emerald-500',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  [ANALYSIS_TYPES.BIAS]: {
    title: 'Ανάλυση Μεροληψίας',
    icon: '⚖️',
    color: 'from-orange-500 to-red-500',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200'
  },
  [ANALYSIS_TYPES.TIMELINE]: {
    title: 'Χρονολόγιο',
    icon: '📅',
    color: 'from-indigo-500 to-purple-500',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200'
  },
  [ANALYSIS_TYPES.EXPERT]: {
    title: 'Απόψεις Ειδικών',
    icon: '🎓',
    color: 'from-teal-500 to-blue-500',
    bgColor: 'bg-teal-50',
    borderColor: 'border-teal-200'
  },
  [ANALYSIS_TYPES.X_PULSE]: {
    title: 'Κοινωνικός Παλμός',
    icon: '🐦',
    color: 'from-cyan-500 to-blue-500',
    bgColor: 'bg-cyan-50',
    borderColor: 'border-cyan-200'
  }
}

interface AnalysisCardProps {
  type: AnalysisType
  data: any
  isActive: boolean
  onClick: () => void
}

function AnalysisCard({ type, data, isActive, onClick }: AnalysisCardProps) {
  const config = ANALYSIS_CONFIGS[type]
  
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ scale: 1.02 }}
      className={clsx(
        'cursor-pointer rounded-xl border-2 transition-all duration-200',
        isActive 
          ? `${config.borderColor} ${config.bgColor} shadow-lg` 
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
      )}
      onClick={onClick}
    >
      <div className="p-4">
        <div className="flex items-center space-x-3 mb-3">
          <div className={clsx(
            'w-10 h-10 rounded-lg flex items-center justify-center text-lg',
            isActive 
              ? `bg-gradient-to-r ${config.color} text-white`
              : 'bg-gray-100 text-gray-600'
          )}>
            {config.icon}
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">{config.title}</h3>
            <p className="text-sm text-gray-600">
              {data ? 'Ανάλυση ολοκληρώθηκε' : 'Σε αναμονή...'}
            </p>
          </div>
          {data && (
            <div className="ml-auto">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
          )}
        </div>
        
        {isActive && data && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-200 pt-3 mt-3"
          >
            <AnalysisContent type={type} data={data} />
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

interface AnalysisContentProps {
  type: AnalysisType
  data: any
}

function AnalysisContent({ type, data }: AnalysisContentProps) {
  // Handle markdown content from the unified API
  if (data?.markdown_content) {
    return (
      <div className="prose prose-sm max-w-none">
        <div 
          className="text-sm text-gray-700 whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ 
            __html: data.markdown_content.replace(/\n/g, '<br/>') 
          }}
        />
      </div>
    )
  }
  
  // Legacy format support for structured data
  if (type === ANALYSIS_TYPES.JARGON && data?.terms) {
    return (
      <div className="space-y-3">
        <h4 className="font-medium text-gray-800 mb-2">Δύσκολοι Όροι:</h4>
        {data.terms.map((term: any, index: number) => (
          <div key={index} className="bg-white rounded-lg p-3 border border-gray-100">
            <div className="font-medium text-blue-700 mb-1">{term.term}</div>
            <div className="text-sm text-gray-600">{term.explanation}</div>
          </div>
        ))}
      </div>
    )
  }
  
  if (type === ANALYSIS_TYPES.VIEWPOINTS && data?.viewpoints) {
    return (
      <div className="space-y-3">
        <h4 className="font-medium text-gray-800 mb-2">Εναλλακτικές Οπτικές:</h4>
        {data.viewpoints.map((viewpoint: any, index: number) => (
          <div key={index} className="bg-white rounded-lg p-3 border border-gray-100">
            <div className="font-medium text-purple-700 mb-1">{viewpoint.source}</div>
            <div className="text-sm text-gray-600">{viewpoint.perspective}</div>
          </div>
        ))}
      </div>
    )
  }
  
  // Fallback for other analysis types or unknown formats
  return (
    <div className="text-sm text-gray-600">
      <div className="bg-gray-50 rounded p-3 max-h-64 overflow-y-auto">
        <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  )
}

export default function ModularAnalysisResults() {
  const { 
    currentArticleUrl, 
    analysisData, 
    completedAnalyses,
    activeTab,
    setActiveTab,
    isLoading
  } = useAnalysisStore()
  
  if (!currentArticleUrl) return null
  
  const availableAnalyses = Array.from(completedAnalyses)
  
  // Don't show anything if analysis is still loading and no results yet
  if (isLoading && availableAnalyses.length === 0) {
    return null
  }
  
  // Don't show if no analyses are completed and not loading
  if (availableAnalyses.length === 0) {
    return null
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Αποτελέσματα Ανάλυσης</h2>
        <div className="text-sm text-gray-600">
          {availableAnalyses.length} ανάλυση{availableAnalyses.length !== 1 ? 'ς' : ''} ολοκληρώθηκε
          {isLoading && <span className="ml-2 text-blue-600">• Συνεχίζεται...</span>}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {availableAnalyses.map((analysisType) => (
            <AnalysisCard
              key={analysisType}
              type={analysisType as AnalysisType}
              data={analysisData[analysisType]}
              isActive={activeTab === analysisType}
              onClick={() => setActiveTab(analysisType as AnalysisType)}
            />
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  )
} 