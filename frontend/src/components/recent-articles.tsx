"use client";

import { useQuery } from "@tanstack/react-query";
import { apiHelpers } from "@/lib/api/client";
import { formatDate, truncateText } from "@/lib/utils";
import { Article } from "@/types";
import { Loader2, ExternalLink, Calendar, User } from "lucide-react";

export function RecentArticles() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["articles"],
    queryFn: async () => {
      const response = await apiHelpers.getArticles({ limit: 20 });
      return response.data.results as Article[];
    },
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading articles</p>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">No articles found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4">Recent Articles</h2>
      
      <div className="space-y-4">
        {data.map((article) => (
          <div
            key={article.id}
            className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 mb-1">
                  {article.title}
                </h3>
                
                <p className="text-sm text-gray-600 mb-2">
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
                  <span className="px-2 py-1 bg-gray-100 rounded">
                    {article.source_name}
                  </span>
                  {article.is_enriched && (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
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