
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { invokeLLM } from "@/api/geminiClient";
import * as store from "@/api/localPathwayStore";
import { useQuery } from "@tanstack/react-query";
import { createPageUrl } from "@/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, ArrowRight, Clock, DollarSign, Loader2, BookOpen } from "lucide-react";
import { motion } from "framer-motion";
import { format } from "date-fns";

export default function MyPathways() {
  const navigate = useNavigate();

  const { data: pathways, isLoading } = useQuery({
    queryKey: ["savedPathways"],
    queryFn: () => store.listPathways("-created_date"),
    initialData: [],
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600 font-medium">Loading your pathways...</p>
        </div>
      </div>
    );
  }

  const getLastUserMessage = (conversation) => {
    if (!conversation || conversation.length === 0) return "No messages yet";
    const userMessages = conversation.filter(msg => msg.role === "user");
    if (userMessages.length === 0) return "Pathway created";
    return userMessages[userMessages.length - 1].content;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="max-w-6xl mx-auto px-4 py-8 md:py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-2 tracking-tight">
                My Pathways
              </h1>
              <p className="text-lg text-slate-600">
                Your saved academic journeys
              </p>
            </div>

            <Button
              onClick={() => navigate(createPageUrl("Home"))}
              className="flex flex-row text-white items-center justify-center bg-gradient-to-r from-blue-900 to-blue-700 hover:from-blue-800 hover:to-blue-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create New Pathway
            </Button>
          </div>
        </motion.div>

        {pathways.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
          >
            <Card className="border-slate-200 shadow-lg">
              <CardContent className="p-12 text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center mx-auto mb-6">
                  <BookOpen className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-3">
                  No pathways yet
                </h3>
                <p className="text-slate-600 mb-6 max-w-md mx-auto">
                  Start your academic journey by creating your first personalized pathway
                </p>
                <div className="flex flex-row justify-center w-full">
                  <Button
                    onClick={() => navigate(createPageUrl("Home"))}
                    size="lg"
                    className="flex flex-row text-white items-center justify-center bg-gradient-to-r from-blue-900 to-blue-700 hover:from-blue-800 hover:to-blue-600"
                  >
                    <Plus className="w-5 h-5 mr-2" />
                    Create Your First Pathway
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {pathways.map((pathway, index) => (
              <motion.div
                key={pathway.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
              >
                <Card className="h-full border-slate-200 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 to-blue-400" />
                  
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {pathway.current_education && pathway.target_education ? (
                          <div className="flex flex-wrap gap-2 mb-3">
                            <Badge className="bg-blue-100 text-blue-900 border-blue-200">
                              {pathway.current_education}
                            </Badge>
                            <span className="text-slate-400">→</span>
                            <Badge className="bg-green-100 text-green-900 border-green-200">
                              {pathway.target_education}
                            </Badge>
                          </div>
                        ) : (
                          <Badge className="mb-3 bg-slate-100 text-slate-700">
                            In Progress
                          </Badge>
                        )}
                        <CardTitle className="text-2xl font-bold text-slate-900 group-hover:text-blue-900 transition-colors">
                          {pathway.career_goal || "New Pathway"}
                        </CardTitle>
                        <p className="text-sm text-slate-500 mt-2">
                          Created {format(new Date(pathway.created_date), "MMM d, yyyy")}
                        </p>
                        <p className="text-xs text-slate-400 mt-1 italic line-clamp-1">
                          "{getLastUserMessage(pathway.conversation)}"
                        </p>
                        {(pathway.two_year_college || pathway.four_year_college) && (
                          <div className="mt-2 text-xs text-slate-600">
                            {pathway.two_year_college && <div>2Y: {pathway.two_year_college}</div>}
                            {pathway.four_year_college && <div>4Y: {pathway.four_year_college}</div>}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {pathway.pathway_data?.total_summary && (
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-50">
                          <Clock className="w-4 h-4 text-blue-600" />
                          <div>
                            <p className="text-xs text-slate-500">Duration</p>
                            <p className="text-sm font-semibold text-slate-900">
                              {pathway.pathway_data.total_summary.total_years} years
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-50">
                          <DollarSign className="w-4 h-4 text-green-600" />
                          <div>
                            <p className="text-xs text-slate-500">Est. Cost</p>
                            <p className="text-sm font-semibold text-slate-900">
                              ${pathway.pathway_data.total_summary.total_cost?.toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    <Button
                      onClick={() =>
                        navigate(createPageUrl("PathwayResults") + `?id=${pathway.id}`)
                      }
                      className="w-full bg-slate-900 hover:bg-slate-800 group"
                    >
                      {pathway.pathway_data ? 'View & Update' : 'Continue Chat'}
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
