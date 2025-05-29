'use client';

import { useAuthStore } from '@/lib/stores/auth-store';
import { Button } from '@/components/ui/button';
import { User, LogOut } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="border-b bg-white shadow-sm">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              News Copilot
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <User className="h-4 w-4" />
                  <span>{user.username}</span>
                  {user.is_premium && (
                    <span className="rounded bg-primary-100 px-2 py-1 text-xs text-primary-700">
                      Premium
                    </span>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="flex items-center gap-2"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </>
            ) : (
              <Button variant="primary" size="sm">
                Login
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
