'use client';

import { ThemeToggle } from '@/components/ui/theme-toggle';

interface PageWrapperProps {
  children: React.ReactNode;
  showThemeToggle?: boolean;
  themeTogglePosition?: 'top-right' | 'top-left';
}

export function PageWrapper({ 
  children, 
  showThemeToggle = true,
  themeTogglePosition = 'top-right', 
}: PageWrapperProps) {
  return (
    <>
      {showThemeToggle && (
        <div className={`fixed ${themeTogglePosition === 'top-right' ? 'top-6 right-6' : 'top-6 left-6'} z-50`}>
          <ThemeToggle />
        </div>
      )}
      {children}
    </>
  );
}