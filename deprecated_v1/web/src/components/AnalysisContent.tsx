'use client'

import { useEffect } from 'react'
import { useAnalysisStore } from '@/lib/store'
import { analyzeArticle } from '@/lib/api-unified'
import { ANALYSIS_TYPES, PROGRESS_SEQUENCES } from '@/lib/constants'
import JargonAnalysis from './analysis/JargonAnalysis'
import ViewpointsAnalysis from './analysis/ViewpointsAnalysis'
import FactCheckAnalysis from './analysis/FactCheckAnalysis'
import BiasAnalysis from './analysis/BiasAnalysis'
import TimelineAnalysis from './analysis/TimelineAnalysis'
import ExpertAnalysis from './analysis/ExpertAnalysis'
import XPulseAnalysis from './analysis/XPulseAnalysis'
import LoadingSpinner from './LoadingSpinner'
import useProgressSequence from '@/hooks/useProgressSequence'

export default function AnalysisContent() {
  const {
    activeTab,
    currentArticleUrl,
    basicAnalysisData,
    deepAnalysisData,
    allAnalysisData,
    loadingAnalyses,
    setAllAnalysis,
    setDeepAnalysis,
    setAnalysisLoading,
    setError
  } = useAnalysisStore()
  
  const { message: progressMessage, start: startProgress, stop: stopProgress } = useProgressSequence()
  const loading = loadingAnalyses.has(activeTab)
  
  useEffect(() => {
    if (!currentArticleUrl || !activeTab) return
    
    // Check if data is already loaded in allAnalysisData (from selective analysis)
    if (allAnalysisData[activeTab]) {
      console.log(`[AnalysisContent] Data already exists for ${activeTab} in allAnalysisData`)
      return
    }
    
    // For legacy support - check basic and deep analysis data
    if (activeTab === ANALYSIS_TYPES.JARGON || activeTab === ANALYSIS_TYPES.VIEWPOINTS) {
      if (basicAnalysisData[activeTab as keyof typeof basicAnalysisData]) {
        console.log(`[AnalysisContent] Data already exists for ${activeTab} in basicAnalysisData`)
        return
      }
    } else {
      if (deepAnalysisData[activeTab]) {
        console.log(`[AnalysisContent] Data already exists for ${activeTab} in deepAnalysisData`)
        return
      }
    }
    
    // Load missing analysis if not loading already
    if (!loadingAnalyses.has(activeTab)) {
      console.log(`[AnalysisContent] Loading analysis for ${activeTab}`)
      loadDeepAnalysis()
    } else {
      console.log(`[AnalysisContent] Already loading, skipping loadDeepAnalysis for ${activeTab}`)
    }
  }, [activeTab, currentArticleUrl, allAnalysisData, deepAnalysisData, basicAnalysisData, loadingAnalyses])
  
  const loadDeepAnalysis = async () => {
    // Double-check data doesn't exist before loading
    if (allAnalysisData[activeTab] || 
        (activeTab === ANALYSIS_TYPES.JARGON && basicAnalysisData.jargon) ||
        (activeTab === ANALYSIS_TYPES.VIEWPOINTS && basicAnalysisData.viewpoints) ||
        deepAnalysisData[activeTab]) {
      console.log(`[AnalysisContent] Data found in loadDeepAnalysis, aborting API call for ${activeTab}`)
      return
    }
    
    // Check if already loading this analysis
    if (loadingAnalyses.has(activeTab)) {
      console.log(`[AnalysisContent] Already loading ${activeTab}, skipping duplicate request`)
      return
    }
    
    setAnalysisLoading(activeTab, true)
    startProgress(PROGRESS_SEQUENCES[activeTab] || [])
    
    try {
      // Use unified API to load single analysis type
      await analyzeArticle(currentArticleUrl, [activeTab], {
        onProgress: (message) => {
          // Progress messages are handled by useProgressSequence
          console.log(`[AnalysisContent] Progress: ${message}`)
        },
        onResult: (type, data) => {
          console.log(`[AnalysisContent] Received ${type} analysis:`, data)
          setAllAnalysis(type, data)
        },
        onError: (type, error) => {
          console.error(`[AnalysisContent] Error in ${type} analysis:`, error)
          setError(error)
        },
        onComplete: (response) => {
          console.log(`[AnalysisContent] Analysis complete:`, response)
        }
      })
    } catch (error) {
      let errorMessage = 'Σφάλμα στην ανάλυση'
      
      if (error instanceof Error) {
        errorMessage = error.message
      }
      
      console.error(`[AnalysisContent] Error loading ${activeTab} analysis:`, error)
      setError(errorMessage)
    } finally {
      console.log(`[AnalysisContent] Finally block - setting loading to false for ${activeTab}`)
      setAnalysisLoading(activeTab, false)
      stopProgress()
    }
  }
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <LoadingSpinner />
        {progressMessage && (
          <p className="mt-4 text-gray-600 animate-pulse">{progressMessage}</p>
        )}
      </div>
    )
  }
  
  // Get analysis data - prioritize allAnalysisData, fallback to legacy data
  const getAnalysisData = (type: typeof activeTab) => {
    if (allAnalysisData[type]) return allAnalysisData[type]
    if (type === ANALYSIS_TYPES.JARGON || type === ANALYSIS_TYPES.VIEWPOINTS) {
      return basicAnalysisData[type as keyof typeof basicAnalysisData]
    }
    return deepAnalysisData[type]
  }

  // Render appropriate analysis component
  switch (activeTab) {
    case ANALYSIS_TYPES.JARGON:
      return <JargonAnalysis data={getAnalysisData(activeTab)} />
    case ANALYSIS_TYPES.VIEWPOINTS:
      return <ViewpointsAnalysis data={getAnalysisData(activeTab)} />
    case ANALYSIS_TYPES.FACT_CHECK:
      return <FactCheckAnalysis data={getAnalysisData(activeTab)} />
    case ANALYSIS_TYPES.BIAS:
      return <BiasAnalysis data={getAnalysisData(activeTab)} />
    case ANALYSIS_TYPES.TIMELINE:
      return <TimelineAnalysis data={getAnalysisData(activeTab)} />
    case ANALYSIS_TYPES.EXPERT:
      return <ExpertAnalysis data={getAnalysisData(activeTab)} />
    case ANALYSIS_TYPES.X_PULSE:
      return <XPulseAnalysis data={getAnalysisData(activeTab)} />
    default:
      return null
  }
}