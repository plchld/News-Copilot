'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to brief
    router.push('/brief');
  }, [router]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="text-center">
        <div className="animate-pulse">
          <div className="w-8 h-8 bg-white/20 rounded-full mx-auto mb-4" />
          <p className="text-white/60 text-sm">Loading...</p>
        </div>
      </div>
    </div>
  );
}