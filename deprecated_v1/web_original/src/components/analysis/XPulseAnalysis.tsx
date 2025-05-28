import { convertMarkdownToHtml } from '@/utils/markdown'

interface XPulseData {
  summary?: string
  sentiment?: {
    overall: 'positive' | 'negative' | 'mixed' | 'neutral'
    breakdown?: Record<string, number>
  }
  key_voices?: Array<{
    username: string
    stance: string
    influence?: string
  }>
  trending_points?: string[]
  misinformation?: Array<{
    claim: string
    reality: string
  }>
}

const SENTIMENT_STYLES = {
  positive: 'bg-green-100 text-green-800',
  negative: 'bg-red-100 text-red-800',
  mixed: 'bg-yellow-100 text-yellow-800',
  neutral: 'bg-gray-100 text-gray-800',
}

const SENTIMENT_LABELS = {
  positive: 'Θετικό',
  negative: 'Αρνητικό',
  mixed: 'Μικτό',
  neutral: 'Ουδέτερο',
}

export default function XPulseAnalysis({ data }: { data?: XPulseData }) {
  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν υπάρχουν διαθέσιμα δεδομένα από το X/Twitter.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {data.summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(data.summary) }} />
        </div>
      )}
      
      {data.sentiment && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-800 mb-3">Συναίσθημα Κοινού</h3>
          <div className="flex items-center gap-4 mb-3">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${SENTIMENT_STYLES[data.sentiment.overall]}`}>
              {SENTIMENT_LABELS[data.sentiment.overall]}
            </span>
          </div>
          {data.sentiment.breakdown && (
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(data.sentiment.breakdown).map(([sentiment, percentage]) => (
                <div key={sentiment} className="flex justify-between">
                  <span className="text-gray-600">{sentiment}:</span>
                  <span className="font-medium">{percentage}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {data.key_voices && data.key_voices.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-800 mb-3">Κύριες Φωνές</h3>
          <div className="space-y-2">
            {data.key_voices.map((voice, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-medium text-primary-600">@{voice.username}</span>
                    <p className="text-sm text-gray-600 mt-1">{voice.stance}</p>
                  </div>
                  {voice.influence && (
                    <span className="text-xs text-gray-500">{voice.influence}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {data.trending_points && data.trending_points.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-800 mb-3">Τάσεις Συζήτησης</h3>
          <ul className="space-y-2">
            {data.trending_points.map((point, index) => (
              <li key={index} className="flex items-start">
                <span className="text-primary-500 mr-2">•</span>
                <span className="text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {data.misinformation && data.misinformation.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="font-semibold text-red-900 mb-3">⚠️ Παραπληροφόρηση</h3>
          <div className="space-y-3">
            {data.misinformation.map((item, index) => (
              <div key={index}>
                <p className="text-sm text-red-800">
                  <span className="font-medium">Ισχυρισμός:</span> {item.claim}
                </p>
                <p className="text-sm text-green-800 mt-1">
                  <span className="font-medium">Πραγματικότητα:</span> {item.reality}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}