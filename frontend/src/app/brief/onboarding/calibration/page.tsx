'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

interface CategoryPreference {
  name: string;
  value: number;
  color: string;
}

export default function CalibrationPage() {
  const router = useRouter();
  const [preferences, setPreferences] = useState<CategoryPreference[]>([
    { name: 'Technology', value: 0.8, color: 'bg-tech' },
    { name: 'Business', value: 0.6, color: 'bg-business' },
    { name: 'World', value: 0.7, color: 'bg-world' },
    { name: 'Politics', value: 0.3, color: 'bg-politics' },
    { name: 'Culture', value: 0.5, color: 'bg-culture' },
  ]);

  const adjustPreference = (index: number, delta: number) => {
    const newPreferences = [...preferences];
    newPreferences[index].value = Math.max(
      0,
      Math.min(1, newPreferences[index].value + delta),
    );
    setPreferences(newPreferences);
  };

  const handleContinue = () => {
    // In a real app, save preferences
    router.push('/brief/daily');
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-black">
      <div className="relative z-10 flex min-h-screen flex-col">
        {/* Header */}
        <header className="p-6">
          <div className="mx-auto max-w-4xl">
            <h2 className="font-serif text-2xl text-white">
              Here&apos;s what we learned about you
            </h2>
            <p className="mt-2 text-gray-400">
              Adjust these preferences to fine-tune your daily brief
            </p>
          </div>
        </header>

        {/* Preferences visualization */}
        <div className="flex-1 px-6 py-12">
          <div className="mx-auto max-w-4xl">
            <div className="grid gap-8">
              {preferences.map((pref, index) => (
                <motion.div
                  key={pref.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass rounded-xl p-6"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-medium text-white">
                      {pref.name}
                    </h3>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => adjustPreference(index, -0.1)}
                        className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-white/20"
                      >
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M20 12H4"
                          />
                        </svg>
                      </button>
                      <span className="w-12 text-center text-sm text-gray-400">
                        {Math.round(pref.value * 100)}%
                      </span>
                      <button
                        onClick={() => adjustPreference(index, 0.1)}
                        className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-white/20"
                      >
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 4v16m8-8H4"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div className="relative h-2 overflow-hidden rounded-full bg-gray-800">
                    <motion.div
                      className={`absolute inset-y-0 left-0 ${pref.color} rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${pref.value * 100}%` }}
                      transition={{
                        type: 'spring',
                        stiffness: 300,
                        damping: 30,
                      }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Additional preferences */}
            <div className="mt-12 grid gap-6">
              <div className="glass rounded-xl p-6">
                <h3 className="mb-4 text-lg font-medium text-white">
                  Reading time preference
                </h3>
                <div className="flex gap-3">
                  {['5 min', '10 min', '15 min'].map((time) => (
                    <button
                      key={time}
                      className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 transition-all hover:border-white/20 hover:bg-white/10"
                    >
                      {time}
                    </button>
                  ))}
                </div>
              </div>

              <div className="glass rounded-xl p-6">
                <h3 className="mb-4 text-lg font-medium text-white">
                  Depth preference
                </h3>
                <div className="flex gap-3">
                  {['Headlines only', 'Summaries', 'Full analysis'].map(
                    (depth) => (
                      <button
                        key={depth}
                        className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm transition-all hover:border-white/20 hover:bg-white/10"
                      >
                        {depth}
                      </button>
                    ),
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Continue button */}
        <div className="p-6">
          <div className="mx-auto max-w-4xl">
            <button
              onClick={handleContinue}
              className="w-full rounded-full bg-primary px-8 py-4 text-lg font-medium text-white transition-colors hover:bg-primary/90"
            >
              Start my daily brief
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
