'use client'

import { useState, useEffect, useRef } from 'react'
import { useAnalysisStore } from '@/lib/store'
import { analyzeArticle } from '@/lib/api'
import { SUPPORTED_SITES, ANALYSIS_TYPES, AnalysisType } from '@/lib/constants'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

const ANALYSIS_OPTIONS = [
  {
    id: 'jargon',
    name: 'Επεξήγηση Όρων',
    description: 'Εξήγηση δύσκολων όρων και ακρωνυμίων',
    icon: '🔤',
    types: [ANALYSIS_TYPES.JARGON],
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  },
  {
    id: 'viewpoints',
    name: 'Εναλλακτικές Οπτικές',
    description: 'Διαφορετικές απόψεις και προοπτικές',
    icon: '💭',
    types: [ANALYSIS_TYPES.VIEWPOINTS],
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200'
  },
  {
    id: 'fact-check',
    name: 'Έλεγχος Γεγονότων',
    description: 'Επαλήθευση ισχυρισμών & στοιχείων',
    icon: '✓',
    types: [ANALYSIS_TYPES.FACT_CHECK],
    color: 'from-green-500 to-emerald-500',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  {
    id: 'bias',
    name: 'Ανάλυση Μεροληψίας',
    description: 'Εντοπισμός προκαταλήψεων & τάσεων',
    icon: '⚖️',
    types: [ANALYSIS_TYPES.BIAS],
    color: 'from-orange-500 to-red-500',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200'
  },
  {
    id: 'timeline',
    name: 'Χρονολόγιο',
    description: 'Ιστορικό πλαίσιο & εξέλιξη',
    icon: '📅',
    types: [ANALYSIS_TYPES.TIMELINE],
    color: 'from-indigo-500 to-purple-500',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200'
  },
  {
    id: 'expert',
    name: 'Απόψεις Ειδικών',
    description: 'Γνώμες & δηλώσεις ειδημόνων',
    icon: '🎓',
    types: [ANALYSIS_TYPES.EXPERT],
    color: 'from-teal-500 to-blue-500',
    bgColor: 'bg-teal-50',
    borderColor: 'border-teal-200'
  },
  {
    id: 'social',
    name: 'Κοινωνικός Παλμός',
    description: 'Αντιδράσεις στα social media',
    icon: '🐦',
    types: [ANALYSIS_TYPES.X_PULSE],
    color: 'from-cyan-500 to-teal-500',
    bgColor: 'bg-cyan-50',
    borderColor: 'border-cyan-200'
  }
]

export default function ModularAnalysisInput() {
  const [url, setUrl] = useState('')
  const [selectedAnalysis, setSelectedAnalysis] = useState<string[]>(['jargon'])
  const [showSites, setShowSites] = useState(false)
  const [step, setStep] = useState<'input' | 'select' | 'analyzing'>('input')
  const analysisRef = useRef<any>(null)
  
  const {
    setArticleUrl,
    setAnalysisResult,
    markAnalysisComplete,
    setLoading,
    setError,
    setProgressMessage,
    resetAnalysis,
    isLoading,
    error,
    progressMessage
  } = useAnalysisStore()

  // Cleanup function for component unmount
  useEffect(() => {
    return () => {
      if (analysisRef.current && typeof analysisRef.current.cleanup === 'function') {
        analysisRef.current.cleanup()
      }
    }
  }, [])

  const handleCancel = () => {
    if (analysisRef.current && typeof analysisRef.current.cleanup === 'function') {
      analysisRef.current.cleanup()
    }
    setLoading(false)
    setStep('input')
    setProgressMessage(null)
    setError(null)
  }

  const handleUrlSubmit = () => {
    if (!url.trim()) {
      setError('Παρακαλώ εισάγετε ένα URL άρθρου')
      return
    }
    setError(null)
    setStep('select')
  }

  const handleAnalysisStart = async () => {
    resetAnalysis()
    setArticleUrl(url)
    setLoading(true)
    setError(null)
    setStep('analyzing')

    try {
      // Get the analysis types from selected options
      const analysisTypes: AnalysisType[] = selectedAnalysis.flatMap(optionId => {
        const option = ANALYSIS_OPTIONS.find(opt => opt.id === optionId)
        return option ? option.types : []
      })

      analysisRef.current = analyzeArticle(url, analysisTypes, {
        onProgress: (status: string) => setProgressMessage(status),
        onResult: ({ type, data }: { type: AnalysisType; data: any }) => {
          // Store result using unified method
          setAnalysisResult(type, data)
          markAnalysisComplete(type)
        },
        onError: (errorMsg: string) => {
          setError(errorMsg)
          setLoading(false)
          setStep('input')
        },
        onComplete: () => {
          setLoading(false)
          setProgressMessage('✨ Όλες οι αναλύσεις ολοκληρώθηκαν!')
          setTimeout(() => {
            setProgressMessage(null)
            setStep('input') // Return to input step when complete
          }, 3000)
        }
      })
      
      await analysisRef.current
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Σφάλμα στην ανάλυση'
      setError(errorMsg)
      setLoading(false)
      setStep('input')
    }
  }

  const toggleAnalysis = (analysisId: string) => {
    setSelectedAnalysis(prev => 
      prev.includes(analysisId) 
        ? prev.filter(id => id !== analysisId)
        : [...prev, analysisId]
    )
  }

  if (step === 'analyzing') {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-3xl shadow-2xl p-8 mb-10"
      >
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Ανάλυση σε εξέλιξη...</h3>
          {progressMessage && (
            <p className="text-blue-600 animate-pulse mb-4">{progressMessage}</p>
          )}
          
          <button
            onClick={handleCancel}
            className="mt-4 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            Ακύρωση
          </button>
        </div>
        
        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <div className="flex items-start space-x-2">
              <span className="text-red-500 mt-0.5">⚠️</span>
              <div>
                <p className="font-medium">Σφάλμα ανάλυσης</p>
                <p className="text-sm mt-1">{error}</p>
                <button
                  onClick={() => setStep('input')}
                  className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Επιστροφή για νέα προσπάθεια
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-3xl shadow-2xl overflow-hidden mb-10"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">News Copilot</h2>
        <p className="text-blue-100">Αναλύστε άρθρα με τεχνητή νοημοσύνη</p>
      </div>

      <div className="p-8">
        <AnimatePresence mode="wait">
          {step === 'input' && (
            <motion.div
              key="input"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL Άρθρου
                </label>
                <div className="flex gap-3">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleUrlSubmit()}
                    placeholder="https://example.com/article..."
                    className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all duration-200"
                  />
                  <button
                    onClick={handleUrlSubmit}
                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all duration-300 hover:scale-105"
                  >
                    Συνέχεια →
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <div className="text-center">
                <button
                  onClick={() => setShowSites(!showSites)}
                  className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                >
                  {showSites ? 'Απόκρυψη' : 'Εμφάνιση'} υποστηριζόμενων ιστοσελίδων
                </button>
                
                <AnimatePresence>
                  {showSites && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-4 p-4 bg-gray-50 rounded-lg overflow-hidden"
                    >
                      <p className="text-sm text-gray-600 mb-2">Υποστηριζόμενες ιστοσελίδες:</p>
                      <div className="flex flex-wrap gap-2 justify-center">
                        {SUPPORTED_SITES.map(site => (
                          <span key={site} className="text-xs bg-white px-2 py-1 rounded border border-gray-200">
                            {site}
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}

          {step === 'select' && (
            <motion.div
              key="select"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">Επιλέξτε Τύπο Ανάλυσης</h3>
                  <p className="text-sm text-gray-600">Μπορείτε να επιλέξετε πολλαπλές αναλύσεις</p>
                </div>
                <button
                  onClick={() => setStep('input')}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                >
                  ← Πίσω
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {ANALYSIS_OPTIONS.map((option) => (
                  <motion.div
                    key={option.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={clsx(
                      'relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-200',
                      selectedAnalysis.includes(option.id)
                        ? `${option.borderColor} ${option.bgColor} shadow-lg`
                        : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                    )}
                    onClick={() => toggleAnalysis(option.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={clsx(
                        'w-10 h-10 rounded-lg flex items-center justify-center text-lg',
                        selectedAnalysis.includes(option.id)
                          ? `bg-gradient-to-r ${option.color} text-white`
                          : 'bg-gray-200 text-gray-600'
                      )}>
                        {option.icon}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800 text-sm">{option.name}</h4>
                        <p className="text-xs text-gray-600 mt-1">{option.description}</p>
                      </div>
                    </div>
                    
                    {selectedAnalysis.includes(option.id) && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute top-2 right-2 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center"
                      >
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </div>

              <div className="flex justify-center pt-4">
                <button
                  onClick={handleAnalysisStart}
                  disabled={selectedAnalysis.length === 0}
                  className="px-8 py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                >
                  Ξεκίνα Ανάλυση ({selectedAnalysis.length})
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
} 