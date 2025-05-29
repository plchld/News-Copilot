'use client';

import { motion } from 'framer-motion';
import { format } from 'date-fns';

interface TimelineEvent {
  date: string;
  event: string;
  description: string;
}

interface TimelineViewProps {
  timeline: TimelineEvent[];
}

export default function TimelineView({ timeline }: TimelineViewProps) {
  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute bottom-0 left-8 top-0 w-0.5 bg-gray-700" />

      {/* Timeline events */}
      <div className="space-y-8">
        {timeline.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="relative pl-16"
          >
            {/* Timeline dot */}
            <div className="absolute left-6 h-4 w-4 rounded-full border-4 border-gray-900 bg-primary" />

            {/* Event content */}
            <div className="glass rounded-lg p-6">
              <time className="text-sm text-gray-400">
                {format(new Date(item.date), 'MMM d, yyyy')}
              </time>
              <h3 className="mb-2 mt-1 text-lg font-medium text-white">
                {item.event}
              </h3>
              <p className="text-gray-300">{item.description}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
