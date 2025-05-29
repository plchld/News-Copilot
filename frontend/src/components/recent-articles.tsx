'use client';

import { useQuery } from '@tanstack/react-query';
import { apiHelpers } from '@/lib/api/client';
import { formatDate, truncateText } from '@/lib/utils';
import { Article } from '@/types';
import { Loader2, ExternalLink, Calendar, User } from 'lucide-react';

export function RecentArticles() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['articles'],
    queryFn: async () => {
      const response = await apiHelpers.get<{ results: Article[] }>(
        '/articles?limit=20',
      );
      return response.data.results;
    },
  });

  if (isLoading) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="py-12 text-center">
          <p className="text-red-600">Error loading articles</p>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="py-12 text-center">
          <p className="text-gray-500">No articles found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Recent Articles</h2>

      <div className="space-y-4">
        {data.map((article) => (
          <div
            key={article.id}
            className="rounded-lg border p-4 transition-colors hover:bg-gray-50"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="mb-1 font-medium text-gray-900">
                  {article.title}
                </h3>

                <p className="mb-2 text-sm text-gray-600">
                  {truncateText(article.content, 150)}
                </p>

                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(article.created_at)}
                  </span>
                  {article.author && (
                    <span className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {article.author}
                    </span>
                  )}
                  <span className="rounded bg-gray-100 px-2 py-1">
                    {article.source_name}
                  </span>
                  {article.is_enriched && (
                    <span className="rounded bg-green-100 px-2 py-1 text-green-700">
                      Analyzed
                    </span>
                  )}
                </div>
              </div>

              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-700"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
