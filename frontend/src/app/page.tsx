"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { ArticleInput } from "@/components/article-input";
import { AnalysisResults } from "@/components/analysis-results";
import { RecentArticles } from "@/components/recent-articles";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"analyze" | "library">("analyze");

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            News Copilot
          </h1>
          <p className="text-gray-600">
            AI-powered analysis for Greek news articles
          </p>
        </div>

        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab("analyze")}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "analyze"
                ? "bg-primary-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-100"
            }`}
          >
            Analyze Article
          </button>
          <button
            onClick={() => setActiveTab("library")}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "library"
                ? "bg-primary-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-100"
            }`}
          >
            Article Library
          </button>
        </div>

        {activeTab === "analyze" ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <ArticleInput />
            </div>
            <div>
              <AnalysisResults />
            </div>
          </div>
        ) : (
          <RecentArticles />
        )}
      </main>
    </div>
  );
}