import { convertMarkdownToHtml } from '@/utils/markdown'

interface FactCheckData {
  markdown_content?: string
  // Legacy structure support
  claims?: any[]
  overall_credibility?: string
}

export default function FactCheckAnalysis({ data }: { data?: FactCheckData }) {
  // If we have markdown content, render it directly
  if (data?.markdown_content) {
    return (
      <div className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-h2:text-xl prose-h3:text-lg prose-strong:text-gray-900 prose-ul:list-disc prose-ul:pl-5">
        <div 
          dangerouslySetInnerHTML={{ 
            __html: convertMarkdownToHtml(data.markdown_content) 
          }} 
        />
      </div>
    )
  }
  
  // Legacy support for structured data
  if (!data?.claims?.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν βρέθηκαν ισχυρισμοί προς έλεγχο.</p>
      </div>
    )
  }
  
  // Legacy rendering code would go here if needed
  return (
    <div className="text-center py-8 text-gray-500">
      <p>Μορφή δεδομένων μη υποστηριζόμενη.</p>
    </div>
  )
}