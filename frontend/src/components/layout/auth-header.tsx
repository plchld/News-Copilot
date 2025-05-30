'use client';

import { useAuth } from '@/contexts/auth-context';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import Link from 'next/link';

interface AuthHeaderProps {
  title?: string;
  subtitle?: string;
  showThemeToggle?: boolean;
}

export function AuthHeader({ 
  title = 'News Copilot', 
  subtitle, 
  showThemeToggle = true,
}: AuthHeaderProps) {
  const { user, logout, isAdmin } = useAuth();

  return (
    <header className="fixed inset-x-0 top-0 z-50 glass-premium border-b border-[var(--border-primary)]">
      <div className="mx-auto max-w-6xl px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            {subtitle && (
              <p className="text-sm text-[var(--text-muted)]">{subtitle}</p>
            )}
            <Link href="/" className="text-xl font-serif text-[var(--text-primary)] hover:opacity-80">
              {title}
            </Link>
          </div>
          
          <div className="flex items-center gap-4">
            {user && (
              <>
                {isAdmin && (
                  <Link 
                    href="/admin" 
                    className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  >
                    Admin
                  </Link>
                )}
                <span className="text-sm text-[var(--text-muted)]">
                  {user.email}
                </span>
                <button
                  onClick={logout}
                  className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  Logout
                </button>
              </>
            )}
            {!user && (
              <Link 
                href="/login" 
                className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                Login
              </Link>
            )}
            {showThemeToggle && <ThemeToggle />}
          </div>
        </div>
      </div>
    </header>
  );
}