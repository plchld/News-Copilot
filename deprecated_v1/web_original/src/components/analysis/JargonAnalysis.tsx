import { convertMarkdownToHtml } from '@/utils/markdown'

interface Term {
  term: string
  explanation: string
  sources?: string[]
}

interface JargonData {
  markdown_content?: string
  terms?: Term[]
}

export default function JargonAnalysis({ data }: { data?: JargonData }) {
  // If we have markdown content, render it directly
  if (data?.markdown_content) {
    return (
      <div className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-h2:text-xl prose-strong:text-gray-900">
        <div 
          dangerouslySetInnerHTML={{ 
            __html: convertMarkdownToHtml(data.markdown_content) 
          }} 
        />
      </div>
    )
  }
  
  // Legacy structured data support
  if (!data?.terms?.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν βρέθηκαν όροι προς εξήγηση σε αυτό το άρθρο.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      {data.terms.map((term, index) => (
        <div key={index} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
          <h3 className="font-semibold text-lg text-gray-800 mb-2">
            {term.term}
          </h3>
          <div 
            className="text-gray-600"
            dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(term.explanation) }}
          />
          {term.sources && term.sources.length > 0 && (
            <div className="mt-2 text-sm text-gray-500">
              <span className="font-medium">Πηγές:</span>{' '}
              {term.sources.join(', ')}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}