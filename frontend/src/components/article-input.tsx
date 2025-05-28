"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useProcessArticle } from "@/lib/hooks/use-articles";
import { Loader2, Link } from "lucide-react";

export function ArticleInput() {
  const [url, setUrl] = useState("");
  const { mutate: processArticle, isPending } = useProcessArticle();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      processArticle(url);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4">Analyze Article</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
            Article URL
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
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
        
        <Button type="submit" disabled={isPending || !url.trim()} className="w-full">
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            "Analyze Article"
          )}
        </Button>
      </form>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Supported analyses:</strong> Jargon explanation, Alternative viewpoints,
          Fact checking, Bias detection, Timeline extraction, Expert opinions, and X Pulse
        </p>
      </div>
    </div>
  );
}