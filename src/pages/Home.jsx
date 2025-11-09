import React, { useState, useEffect, useRef } from "react";
import { invokeLLM } from "@/api/geminiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import SummaryCard from "../components/pathway/SummaryCard";
import PathwayStep from "../components/pathway/PathwayStep";

export default function Home() {
  const [conversation, setConversation] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your ElevatePath career advisor. Tell me a bit about your interests — for example, what subjects or careers you’re curious about!",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pathway, setPathway] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  useEffect(() => {
    scrollToBottom();
  }, [conversation, pathway]);

  const handleSendMessage = async (message) => {
    const newConv = [
      ...conversation,
      { role: "user", content: message, timestamp: new Date().toISOString() },
    ];
    setConversation(newConv);
    setIsProcessing(true);

    try {
      const response = await invokeLLM({ prompt: message });
      console.log("AI response:", response);

      // if Gemini returns structured data, show cards
      if (response.pathway_data) {
        setPathway(response.pathway_data);

        setConversation([
          ...newConv,
          {
            role: "assistant",
            content:
              "Here’s a personalized academic pathway based on your interests!",
            timestamp: new Date().toISOString(),
          },
        ]);
      } else {
        setConversation([
          ...newConv,
          {
            role: "assistant",
            content:
              typeof response.output === "string"
                ? response.output
                : "I'm not sure yet — could you tell me a bit more?",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error:", error);
      setConversation([
        ...newConv,
        {
          role: "assistant",
          content:
            "Sorry, something went wrong while processing your request. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-white to-blue-50">
      <div className="max-w-5xl mx-auto px-4 py-12 md:py-20">
        {/* --- HEADER --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <div className="flex flex-row justify-center w-full mb-10">
            <img
              src="./ElevatePath_logo_flat.png"
              alt="ElevatePath Logo"
              className="h-30"
            />
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-4 tracking-tight">
            Find Your Academic Journey
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Chat with our AI advisor to create your personalized educational
            pathway.
          </p>
        </motion.div>

        {/* --- FEATURE CARDS --- */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            <Card className="h-full border-slate-200 shadow-lg hover:shadow-xl transition-shadow">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-amber-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">
                    Conversational AI
                  </h3>
                </div>
                <p className="text-slate-600 leading-relaxed">
                  Simply chat with our AI advisor about your goals — no forms,
                  just a natural conversation.
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <Card className="h-full border-slate-200 shadow-lg hover:shadow-xl transition-shadow">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">
                    Personalized Pathways
                  </h3>
                </div>
                <p className="text-slate-600 leading-relaxed">
                  Once ready, your pathway will appear automatically — showing
                  time, cost, and degree milestones.
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* --- CHAT BOX --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <Card className="border-slate-200 shadow-2xl">
            <CardContent className="p-6">
              <div className="h-[500px] flex flex-col">
                {/* Chat messages */}
                <div className="flex-1 overflow-y-auto mb-4 space-y-2 pr-2">
                  {conversation.map((msg, i) => (
                    <ChatMessage key={i} message={msg} />
                  ))}
                  {isProcessing && (
                    <div className="flex gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center flex-shrink-0">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{
                            duration: 1,
                            repeat: Infinity,
                            ease: "linear",
                          }}
                        >
                          <Sparkles className="w-5 h-5 text-amber-400" />
                        </motion.div>
                      </div>
                      <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                        <p className="text-slate-600">Thinking...</p>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input field */}
                <div className="border-t border-slate-200 pt-4">
                  <ChatInput
                    onSend={handleSendMessage}
                    disabled={isProcessing}
                    placeholder="Tell me about your educational goals..."
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* --- GENERATED PATHWAY BELOW CHAT --- */}
        {pathway && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="mt-12 space-y-8"
          >
            <PathwayStep phase={pathway.mdc_phase} index={0} totalPhases={3} />
            <PathwayStep phase={pathway.fiu_phase} index={1} totalPhases={3} />
            {pathway.advanced_phase?.masters && (
              <PathwayStep
                phase={pathway.advanced_phase.masters}
                index={2}
                totalPhases={3}
              />
            )}
            {pathway.total_summary && (
              <SummaryCard summary={pathway.total_summary} />
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
