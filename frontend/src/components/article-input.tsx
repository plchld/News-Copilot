'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useProcessArticle } from '@/lib/hooks/use-articles';
import { Loader2, Link } from 'lucide-react';

export function ArticleInput() {
  const [url, setUrl] = useState('');
  const { mutate: processArticle, isPending } = useProcessArticle();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      processArticle(url);
    }
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Analyze Article</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="url"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Article URL
          </label>
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Link className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.gr/article"
              className="input pl-10"
              required
              disabled={isPending}
            />
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Paste a URL from any Greek news website
          </p>
        </div>

        <Button
          type="submit"
          disabled={isPending || !url.trim()}
          className="w-full"
        >
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            'Analyze Article'
          )}
        </Button>
      </form>

      <div className="mt-6 rounded-lg bg-blue-50 p-4">
        <p className="text-sm text-blue-800">
          <strong>Supported analyses:</strong> Jargon explanation, Alternative
          viewpoints, Fact checking, Bias detection, Timeline extraction, Expert
          opinions, and X Pulse
        </p>
      </div>
    </div>
  );
}
