'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import type { TimelineEvent } from '@/types/story';

interface TimelineData {
  events: TimelineEvent[];
}

interface TimelineViewProps {
  timeline: TimelineData;
}

export default function TimelineView({ timeline }: TimelineViewProps) {
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  return (
    <div className="relative">
      {/* Timeline header */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-white mb-2">Story Evolution</h3>
        <p className="text-white/60 text-sm">
          How this story developed over time
        </p>
      </div>

      {/* Timeline visualization */}
      <div className="relative">
        {/* Base line */}
        <div className="absolute left-8 top-0 bottom-0 w-px bg-white/10" />

        {/* Events */}
        <div className="space-y-8">
          {timeline.events.map((event, i) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="relative flex items-start gap-4"
            >
              {/* Timeline dot */}
              <button
                onClick={() => setSelectedEvent(event)}
                className={`
                  relative z-10 w-4 h-4 rounded-full border-2 transition-all duration-300
                  ${selectedEvent?.id === event.id 
                    ? 'bg-white border-white scale-125' 
                    : 'bg-black border-white/40 hover:border-white/60'}
                `}
              >
                {/* Pulse effect for major events */}
                {event.isMajor && (
                  <span className="absolute inset-0 rounded-full bg-white/20 animate-ping" />
                )}
              </button>

              {/* Event content */}
              <div className="flex-1">
                <p className="text-xs text-white/40 mb-1">{event.date}</p>
                <h4 className="text-white/90 font-medium mb-1">{event.title}</h4>
                <p className="text-white/60 text-sm">{event.summary}</p>

                {/* Expanded details */}
                {selectedEvent?.id === event.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 p-4 glass-subtle-premium rounded-lg"
                  >
                    <p className="text-white/70 text-sm leading-relaxed">{event.details}</p>
                  </motion.div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}