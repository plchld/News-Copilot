'use client';

import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/contexts/theme-context';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  console.log('ThemeToggle rendered with theme:', theme, 'mounted:', mounted);

  // Show a placeholder during SSR/hydration
  if (!mounted) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--text-muted)]">Loading...</span>
        <div className="relative w-14 h-7 rounded-full bg-black/5 border border-black/10" />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--text-muted)]">Theme: {theme}</span>
      <button
        onClick={() => {
          console.log('Theme toggle clicked! Current theme:', theme);
          toggleTheme();
        }}
        className="relative w-14 h-7 rounded-full bg-black/5 dark:bg-white/10 border border-black/10 dark:border-white/10 transition-colors duration-300 z-50 cursor-pointer"
        aria-label="Toggle theme"
        type="button"
      >
        <motion.div
          className="absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white dark:bg-black shadow-sm flex items-center justify-center pointer-events-none"
          animate={{
            x: theme === 'light' ? 0 : 26,
          }}
          transition={{
            type: "spring",
            stiffness: 500,
            damping: 30
          }}
        >
          {theme === 'light' ? (
            <Sun className="w-3.5 h-3.5 text-amber-600" />
          ) : (
            <Moon className="w-3.5 h-3.5 text-white" />
          )}
        </motion.div>
      </button>
    </div>
  );
}