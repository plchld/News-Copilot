import { convertMarkdownToHtml } from '@/utils/markdown'

interface ExpertOpinion {
  expert: string
  credentials?: string
  opinion: string
  date?: string
  source?: string
}

interface ExpertData {
  opinions?: ExpertOpinion[]
  consensus?: string
}

export default function ExpertAnalysis({ data }: { data?: ExpertData }) {
  if (!data?.opinions?.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν βρέθηκαν απόψεις ειδικών για αυτό το θέμα.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {data.consensus && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">Συναίνεση Ειδικών</h3>
          <div 
            className="text-green-800"
            dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(data.consensus) }}
          />
        </div>
      )}
      
      <div className="space-y-4">
        {data.opinions.map((opinion, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="mb-3">
              <h3 className="font-semibold text-lg text-gray-800">
                {opinion.expert}
              </h3>
              {opinion.credentials && (
                <p className="text-sm text-gray-600">{opinion.credentials}</p>
              )}
            </div>
            
            <blockquote className="border-l-4 border-primary-400 pl-4 py-2">
              <div 
                className="text-gray-700"
                dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(opinion.opinion) }}
              />
            </blockquote>
            
            <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
              {opinion.date && <span>{opinion.date}</span>}
              {opinion.source && <span>{opinion.source}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}