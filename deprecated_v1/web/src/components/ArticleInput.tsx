'use client'

import { useState } from 'react'
import { useAnalysisStore } from '@/lib/store'
import { analyzeArticle } from '@/lib/api-unified'
import { ANALYSIS_TYPES, SUPPORTED_SITES } from '@/lib/constants'
import type { AnalysisType } from '@/lib/constants'

export default function ArticleInput() {
  const [url, setUrl] = useState('')
  const [showSites, setShowSites] = useState(false)
  
  const {
    setArticleUrl,
    setAllAnalysis,
    markAnalysisComplete,
    setLoading,
    setError,
    setProgressMessage,
    resetAnalysis,
    selectedAnalysisTypes,
    toggleAnalysisType,
    isLoading,
    error,
    progressMessage
  } = useAnalysisStore()

  const handleAnalysis = async () => {
    if (!url.trim()) {
      setError('Παρακαλώ εισάγετε ένα URL άρθρου')
      return
    }

    if (selectedAnalysisTypes.size === 0) {
      setError('Παρακαλώ επιλέξτε τουλάχιστον έναν τύπο ανάλυσης')
      return
    }

    // Reset previous analysis
    resetAnalysis()
    setArticleUrl(url)
    setLoading(true)
    setError(null)

    try {
      await analyzeArticle(url, Array.from(selectedAnalysisTypes), {
        onProgress: (message) => setProgressMessage(message),
        onResult: (type, data) => {
          setAllAnalysis(type, data)
          markAnalysisComplete(type)
        },
        onError: (type, error) => {
          // You might want to track errors per analysis type
          console.error(`Error in ${type} analysis:`, error)
        },
        onComplete: (response) => {
          setLoading(false)
          setProgressMessage('✨ Η ανάλυση ολοκληρώθηκε!')
          setTimeout(() => setProgressMessage(null), 3000)
        }
      })
    } catch (error) {
      setLoading(false)
      setError(error instanceof Error ? error.message : 'Σφάλμα στην ανάλυση')
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-10">
      <div className="flex gap-4 mb-6">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleAnalysis()}
          placeholder="Επικολλήστε το URL του άρθρου εδώ..."
          className="input-primary flex-1"
          disabled={isLoading}
        />
        <button
          onClick={handleAnalysis}
          disabled={isLoading || selectedAnalysisTypes.size === 0}
          className="btn-primary whitespace-nowrap"
        >
          {isLoading ? 'Αναλύει...' : `Ανάλυση (${selectedAnalysisTypes.size} τύποι)`}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {progressMessage && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg mb-4 animate-pulse">
          {progressMessage}
        </div>
      )}

      {/* Analysis Type Selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Επιλέξτε τύπους ανάλυσης:</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(ANALYSIS_TYPES).map(([key, value]) => {
            const isSelected = selectedAnalysisTypes.has(value)
            const displayNames: Record<AnalysisType, string> = {
              'jargon': '🔤 Επεξήγηση Όρων',
              'viewpoints': '🌐 Εναλλακτικές Οπτικές',
              'fact-check': '🔍 Έλεγχος Γεγονότων',
              'bias': '⚖️ Ανάλυση Μεροληψίας',
              'timeline': '📅 Χρονολόγιο',
              'expert': '🎓 Απόψεις Ειδικών',
              'x-pulse': '🐦 Κοινωνικός Παλμός'
            }
            
            return (
              <button
                key={value}
                onClick={() => toggleAnalysisType(value)}
                disabled={isLoading}
                className={`
                  p-3 rounded-lg border text-sm font-medium transition-all
                  ${isSelected 
                    ? 'bg-blue-50 border-blue-200 text-blue-700 ring-2 ring-blue-200' 
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                  }
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                {displayNames[value]}
              </button>
            )
          })}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Επιλεγμένα: {selectedAnalysisTypes.size} από {Object.keys(ANALYSIS_TYPES).length}
        </p>
      </div>

      <div className="text-center">
        <button
          onClick={() => setShowSites(!showSites)}
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          {showSites ? 'Απόκρυψη' : 'Εμφάνιση'} υποστηριζόμενων ιστοσελίδων
        </button>
        
        {showSites && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Υποστηριζόμενες ιστοσελίδες:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUPPORTED_SITES.map(site => (
                <span key={site} className="text-xs bg-white px-2 py-1 rounded border border-gray-200">
                  {site}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}