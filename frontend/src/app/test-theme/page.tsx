'use client';

import { useState, useEffect } from 'react';

export default function TestThemePage() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('app-theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.className = savedTheme;
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.className = newTheme;
    localStorage.setItem('app-theme', newTheme);
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen p-8">
      <h1 className="text-3xl font-bold mb-4">Theme Test Page</h1>
      <p className="mb-4">Current theme: {theme}</p>
      <button
        onClick={toggleTheme}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Toggle Theme (currently: {theme})
      </button>
      
      <div className="mt-8 space-y-4">
        <div className="p-4 glass-premium rounded">
          <h2 className="text-xl font-semibold">Glass Premium Box</h2>
          <p>This should change appearance based on theme</p>
        </div>
        
        <div className="space-y-2">
          <p className="text-[var(--text-primary)]">Primary text color</p>
          <p className="text-[var(--text-secondary)]">Secondary text color</p>
          <p className="text-[var(--text-tertiary)]">Tertiary text color</p>
          <p className="text-[var(--text-muted)]">Muted text color</p>
        </div>
      </div>
    </div>
  );
}