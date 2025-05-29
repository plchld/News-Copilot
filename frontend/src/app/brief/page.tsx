'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export default function BriefLandingPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <main className="min-h-screen overflow-hidden">
      {/* Ambient background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="ambient-orb ambient-orb-blue w-[1000px] h-[1000px] -top-1/2 -right-1/2" />
        <div className="ambient-orb ambient-orb-violet w-[800px] h-[800px] -bottom-1/2 -left-1/2" />
      </div>

      {/* Theme toggle in top right */}
      <div className="absolute top-6 right-6 z-20">
        <ThemeToggle />
      </div>

      {/* Hero section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 py-20">
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          {/* Accent text */}
          <motion.p
            className="intro-text mb-12 no-select animate-fade-up animation-delay-100"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: mounted ? 1 : 0, y: mounted ? 0 : 20 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            Introducing News Copilot
          </motion.p>

          {/* Main headline with dramatic scale */}
          <div className="animate-float">
            <motion.h1
              className="headline mb-8"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: mounted ? 1 : 0, y: mounted ? 0 : 30 }}
              transition={{ duration: 1, delay: 0.3 }}
            >
              <span className="headline-hero block animate-fade-up animation-delay-200">
                Νέα.
              </span>
              <span className="headline-large block mt-4 animate-fade-up animation-delay-400">
                που επιτέλους σέβονται
              </span>
              <span className="headline-large block animate-fade-up animation-delay-600">
                τον χρόνο σου.
              </span>
            </motion.h1>
          </div>

          {/* Tagline with better spacing */}
          <motion.p className="tagline mt-16 animate-fade-up animation-delay-800">
            5 stories. 5 minutes. No noise.
          </motion.p>
          <motion.p className="text-base text-[var(--text-secondary)] mt-6 animate-fade-up animation-delay-900 max-w-lg mx-auto leading-relaxed">
            A finite daily brief that goes as deep as you need. From surface summary to full context—on demand.
          </motion.p>

          {/* CTA Button with more breathing room */}
          <motion.div
            className="mt-20 animate-fade-up animation-delay-1000"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: mounted ? 1 : 0, y: mounted ? 0 : 20 }}
            transition={{ duration: 0.8, delay: 1.2 }}
          >
            <Link href="/brief/onboarding" className="button-editorial">
              Begin Reading
            </Link>
          </motion.div>

          {/* Premium feature indicators */}
          <motion.div className="flex flex-wrap items-center justify-center gap-10 mt-24 animate-fade-up animation-delay-1200">
            <span className="feature-premium animate-fade-up animation-delay-1300">
              Unbiased context
            </span>
            <span className="feature-premium animate-fade-up animation-delay-1400">
              Depth on demand
            </span>
            <span className="feature-premium animate-fade-up animation-delay-1500">
              Finite by design
            </span>
          </motion.div>
        </div>
      </section>
    </main>
  );
}
