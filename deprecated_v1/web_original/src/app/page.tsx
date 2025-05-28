'use client'

import Header from '@/components/Header'
import ModularAnalysisInput from '@/components/ModularAnalysisInput'
import ModularAnalysisResults from '@/components/ModularAnalysisResults'
import { useAnalysisStore } from '@/lib/store'

export default function Home() {
  const { currentArticleUrl } = useAnalysisStore()
  
  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 max-w-6xl">
        <Header />
        <ModularAnalysisInput />
        {currentArticleUrl && (
          <div className="pb-10">
            <ModularAnalysisResults />
          </div>
        )}
      </div>
    </div>
  )
}