import { convertMarkdownToHtml } from '@/utils/markdown'

interface Viewpoint {
  perspective: string
  reasoning: string
  sources?: string[]
}

interface ViewpointsData {
  markdown_content?: string
  topic_analysis?: string
  alternative_perspectives?: string
}

export default function ViewpointsAnalysis({ data }: { data?: ViewpointsData }) {
  // If we have markdown content, render it directly
  if (data?.markdown_content) {
    return (
      <div className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-h2:text-xl prose-h3:text-lg prose-strong:text-gray-900">
        <div 
          dangerouslySetInnerHTML={{ 
            __html: convertMarkdownToHtml(data.markdown_content) 
          }} 
        />
      </div>
    )
  }
  
  // Legacy structured data support
  if (!data || (!data.topic_analysis && !data.alternative_perspectives)) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν βρέθηκαν εναλλακτικές οπτικές για αυτό το άρθρο.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6 p-4">
      {data.topic_analysis && (
        <div className="mb-6">
          <h3 className="font-semibold text-xl text-gray-800 mb-3 border-b pb-2">
            Ανάλυση Θέματος
          </h3>
          <div
            className="text-gray-700 prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(data.topic_analysis) }}
          />
        </div>
      )}

      {data.alternative_perspectives && (
        <div>
          <div
            className="text-gray-700 prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(data.alternative_perspectives) }}
          />
        </div>
      )}
    </div>
  )
}