import { convertMarkdownToHtml } from '@/utils/markdown'

interface TimelineEvent {
  date: string
  event: string
  significance?: string
  source?: string
}

interface TimelineData {
  events?: TimelineEvent[]
  context?: string
}

export default function TimelineAnalysis({ data }: { data?: TimelineData }) {
  if (!data?.events?.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Δεν βρέθηκαν χρονολογικά γεγονότα για αυτό το θέμα.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {data.context && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(data.context) }} />
        </div>
      )}
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>
        
        <div className="space-y-6">
          {data.events.map((event, index) => (
            <div key={index} className="relative flex items-start">
              {/* Timeline dot */}
              <div className="absolute left-8 w-4 h-4 bg-primary-500 rounded-full -translate-x-1/2 mt-1.5 z-10"></div>
              
              {/* Content */}
              <div className="ml-16 flex-1">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <time className="text-sm font-semibold text-primary-600">
                      {event.date}
                    </time>
                    {event.source && (
                      <span className="text-xs text-gray-500">{event.source}</span>
                    )}
                  </div>
                  
                  <h3 className="font-medium text-gray-800 mb-1">
                    {event.event}
                  </h3>
                  
                  {event.significance && (
                    <p className="text-sm text-gray-600 mt-2">
                      <span className="font-medium">Σημασία:</span> {event.significance}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}