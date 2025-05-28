'use client'

import { useAnalysisStore } from '@/lib/store'
import { AnalysisType, ANALYSIS_TYPES } from '@/lib/constants'
import clsx from 'clsx'

const TAB_LABELS: Record<AnalysisType, string> = {
  [ANALYSIS_TYPES.JARGON]: '🔤 Επεξήγηση Όρων',
  [ANALYSIS_TYPES.VIEWPOINTS]: '💭 Εναλλακτικές Οπτικές',
  [ANALYSIS_TYPES.FACT_CHECK]: '✓ Γεγονότα',
  [ANALYSIS_TYPES.BIAS]: '⚖️ Μεροληψία',
  [ANALYSIS_TYPES.TIMELINE]: '📅 Χρονολόγιο',
  [ANALYSIS_TYPES.EXPERT]: '🎓 Ειδικοί',
  [ANALYSIS_TYPES.X_PULSE]: '🐦 X Παλμός',
}

export default function AnalysisTabs() {
  const { activeTab, setActiveTab, currentArticleUrl, completedAnalyses } = useAnalysisStore()
  
  if (!currentArticleUrl) return null
  
  const tabs = Object.values(ANALYSIS_TYPES)
  const basicTabs = [ANALYSIS_TYPES.JARGON, ANALYSIS_TYPES.VIEWPOINTS]
  
  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="flex flex-wrap border-b border-gray-200">
        {tabs.map((tab) => {
          const isBasicTab = basicTabs.includes(tab as typeof basicTabs[number])
          const isAvailable = isBasicTab ? completedAnalyses.has(tab) : true
          
          return (
            <button
              key={tab}
              onClick={() => isAvailable && setActiveTab(tab)}
              disabled={!isAvailable}
              className={clsx(
                'flex-1 px-4 py-3 text-sm font-medium transition-all duration-200',
                'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed',
                {
                  'tab-active': activeTab === tab,
                  'text-gray-600': activeTab !== tab,
                }
              )}
            >
              {TAB_LABELS[tab]}
              {isBasicTab && completedAnalyses.has(tab) && (
                <span className="ml-1 text-green-500">✓</span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}