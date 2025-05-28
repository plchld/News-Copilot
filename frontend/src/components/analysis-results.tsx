"use client";

import { useAnalysisStore } from "@/lib/stores/analysis-store";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BookOpen, 
  Eye, 
  CheckCircle, 
  Scale, 
  Calendar, 
  GraduationCap, 
  TrendingUp 
} from "lucide-react";

export function AnalysisResults() {
  const { currentAnalysis, isLoading } = useAnalysisStore();

  if (!currentAnalysis && !isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">
            Analysis results will appear here after processing an article
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4">Analysis Results</h2>
      
      <Tabs defaultValue="jargon" className="w-full">
        <TabsList className="grid grid-cols-4 lg:grid-cols-7 gap-1">
          <TabsTrigger value="jargon" className="flex items-center gap-1 text-xs">
            <BookOpen className="h-3 w-3" />
            <span className="hidden lg:inline">Jargon</span>
          </TabsTrigger>
          <TabsTrigger value="viewpoints" className="flex items-center gap-1 text-xs">
            <Eye className="h-3 w-3" />
            <span className="hidden lg:inline">Views</span>
          </TabsTrigger>
          <TabsTrigger value="fact_check" className="flex items-center gap-1 text-xs">
            <CheckCircle className="h-3 w-3" />
            <span className="hidden lg:inline">Facts</span>
          </TabsTrigger>
          <TabsTrigger value="bias" className="flex items-center gap-1 text-xs">
            <Scale className="h-3 w-3" />
            <span className="hidden lg:inline">Bias</span>
          </TabsTrigger>
          <TabsTrigger value="timeline" className="flex items-center gap-1 text-xs">
            <Calendar className="h-3 w-3" />
            <span className="hidden lg:inline">Timeline</span>
          </TabsTrigger>
          <TabsTrigger value="expert" className="flex items-center gap-1 text-xs">
            <GraduationCap className="h-3 w-3" />
            <span className="hidden lg:inline">Experts</span>
          </TabsTrigger>
          <TabsTrigger value="x_pulse" className="flex items-center gap-1 text-xs">
            <TrendingUp className="h-3 w-3" />
            <span className="hidden lg:inline">X Pulse</span>
          </TabsTrigger>
        </TabsList>

        <div className="mt-4">
          <TabsContent value="jargon">
            <div className="space-y-3">
              <h3 className="font-medium">Technical Terms Explained</h3>
              <p className="text-sm text-gray-600">
                Analysis will appear here...
              </p>
            </div>
          </TabsContent>
          
          {/* Add other tab contents similarly */}
        </div>
      </Tabs>
    </div>
  );
}