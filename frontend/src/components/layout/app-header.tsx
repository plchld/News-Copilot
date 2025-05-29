'use client';

import { ThemeToggle } from '@/components/ui/theme-toggle';

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  showThemeToggle?: boolean;
  children?: React.ReactNode;
}

export function AppHeader({ 
  title, 
  subtitle, 
  showThemeToggle = true,
  children 
}: AppHeaderProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-50 glass-premium border-b border-[var(--border-primary)]">
      <div className="mx-auto max-w-4xl px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            {subtitle && (
              <p className="text-sm text-[var(--text-muted)]">{subtitle}</p>
            )}
            {title && (
              <h1 className="text-xl font-serif text-[var(--text-primary)]">{title}</h1>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            {showThemeToggle && <ThemeToggle />}
            {children}
          </div>
        </div>
      </div>
    </header>
  );
}