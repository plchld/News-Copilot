import { convertMarkdownToHtml } from '@/utils/markdown'

interface BiasIndicator {
  type: string
  description: string
  examples?: string[]
}

interface BiasData {
  political_lean?: string
  bias_score?: number
  indicators?: BiasIndicator[]
  explanation?: string
}

export default function BiasAnalysis({ data }: { data?: BiasData }) {
  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν υπάρχουν διαθέσιμα δεδομένα ανάλυσης μεροληψίας.</p>
      </div>
    )
  }
  
  const getBiasColor = (score?: number) => {
    if (!score) return 'gray'
    if (score < -0.6) return 'red'
    if (score < -0.2) return 'orange'
    if (score < 0.2) return 'gray'
    if (score < 0.6) return 'blue'
    return 'purple'
  }
  
  const biasColor = getBiasColor(data.bias_score)
  
  return (
    <div className="space-y-6">
      {data.political_lean && (
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-3">Πολιτική Τοποθέτηση</h3>
          <div className="inline-flex items-center gap-2">
            <span className="text-2xl">
              {data.political_lean}
            </span>
            {data.bias_score !== undefined && (
              <span className={`text-sm px-2 py-1 rounded bg-${biasColor}-100 text-${biasColor}-800`}>
                {data.bias_score > 0 ? '+' : ''}{data.bias_score.toFixed(2)}
              </span>
            )}
          </div>
        </div>
      )}
      
      {data.explanation && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(data.explanation) }} />
        </div>
      )}
      
      {data.indicators && data.indicators.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Δείκτες Μεροληψίας</h3>
          <div className="space-y-3">
            {data.indicators.map((indicator, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-800 mb-2">{indicator.type}</h4>
                <p className="text-gray-600 text-sm">{indicator.description}</p>
                {indicator.examples && indicator.examples.length > 0 && (
                  <div className="mt-2 text-sm text-gray-500">
                    <span className="font-medium">Παραδείγματα:</span>
                    <ul className="list-disc list-inside mt-1">
                      {indicator.examples.map((example, i) => (
                        <li key={i}>{example}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}