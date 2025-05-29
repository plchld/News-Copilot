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
      <section className="relative min-h-screen flex items-center justify-center px-6">
        <div className="relative z-10 max-w-5xl mx-auto text-center">
          {/* Accent text */}
          <motion.p
            className="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)] mb-8 no-select"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: mounted ? 1 : 0, y: mounted ? 0 : 20 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            Introducing a new way to stay informed
          </motion.p>

          {/* Premium headline with staggered animation */}
          <h1 className="headline text-4xl md:text-6xl lg:text-8xl xl:text-9xl">
            <motion.span
              className="block animate-fade-up animation-delay-200"
              style={{ fontSize: 'clamp(3rem, 8vw, 7rem)' }}
            >
              Finally.
            </motion.span>
            <motion.span
              className="block animate-fade-up animation-delay-400"
              style={{ fontSize: 'clamp(3rem, 8vw, 7rem)' }}
            >
              News that respects
            </motion.span>
            <motion.span
              className="block animate-fade-up animation-delay-600"
              style={{ fontSize: 'clamp(3rem, 8vw, 7rem)' }}
            >
              your time.
            </motion.span>
          </h1>

          {/* Premium tagline */}
          <motion.p className="tagline text-lg md:text-xl mt-8 animate-fade-up animation-delay-800">
            5 stories. 5 minutes. No noise.
          </motion.p>
          <motion.p className="text-sm text-[var(--text-tertiary)] mt-3 animate-fade-up animation-delay-900 max-w-lg mx-auto">
            A finite daily brief that goes as deep as you need. From surface summary to full context—on demand.
          </motion.p>

          {/* Premium CTA button */}
          <motion.div className="mt-16 animate-fade-up animation-delay-1000">
            <Link
              href="/brief/onboarding"
              className="glass-button-premium no-select group"
            >
              <span className="relative z-10">Start Your Brief</span>
              <div className="shine" />
            </Link>
          </motion.div>

          {/* Philosophy indicators */}
          <motion.div className="flex flex-wrap items-center justify-center gap-8 mt-20 text-xs text-[var(--text-muted)] animate-fade-up animation-delay-1000">
            <span className="flex items-center gap-2 no-select">
              <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]" />
              Curated intelligence
            </span>
            <span className="flex items-center gap-2 no-select">
              <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]" />
              Progressive depth
            </span>
            <span className="flex items-center gap-2 no-select">
              <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]" />
              Finite by design
            </span>
          </motion.div>
        </div>

        {/* Subtle scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-fade-up animation-delay-1000"
          animate={{
            y: [0, 10, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          <div className="w-[1px] h-16 bg-gradient-to-b from-[var(--text-muted)] to-transparent" />
        </motion.div>
      </section>
    </main>
  );
}
