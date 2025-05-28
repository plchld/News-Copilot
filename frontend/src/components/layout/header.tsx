"use client";

import { useAuthStore } from "@/lib/stores/auth-store";
import { Button } from "@/components/ui/button";
import { User, LogOut } from "lucide-react";

export function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
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
                    <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs">
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