import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { invokeLLM } from "@/api/geminiClient";
import * as store from "@/api/localPathwayStore";
import { createPageUrl } from "@/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Compass, Sparkles, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";

const AVAILABLE_COLLEGES = {
  twoYear: [
    "Miami Dade College (MDC)",
    "Broward College",
    "Palm Beach State College",
    "Valencia College",
    "Seminole State College",
    "St. Petersburg College",
    "Hillsborough Community College",
    "Santa Fe College",
    "Tallahassee Community College",
    "State College of Florida"
  ],
  fourYear: [
    "Florida International University (FIU)",
    "University of Florida (UF)",
    "Florida State University (FSU)",
    "University of Central Florida (UCF)",
    "University of South Florida (USF)",
    "Florida Atlantic University (FAU)",
    "University of Miami (UM)",
    "University of North Florida (UNF)",
    "Florida Gulf Coast University (FGCU)",
    "Florida A&M University (FAMU)"
  ]
};

export default function Home() {
  const navigate = useNavigate();
  const [conversation, setConversation] = useState([
    {
      role: "assistant",
      content: "Hi! I'm your ElevatePath career advisor. I'll help you create a personalized educational plan to achieve your career goals.\n\nTo get started, tell me:\n- • What career are you interested in?\n- • What's your current education level?\n- • What degree level do you want to achieve?\n- • Which colleges are you interested in?\n\nFeel free to share as much or as little as you want, and I'll ask follow-up questions!",
      timestamp: new Date().toISOString()
    }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedInfo, setExtractedInfo] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSendMessage = async (userMessage) => {
    const newConversation = [
      ...conversation,
      {
        role: "user",
        content: userMessage,
        timestamp: new Date().toISOString()
      }
    ];
    setConversation(newConversation);
    setIsProcessing(true);

    try {
      // First, extract information from the conversation
      const extractionPrompt = `You are an academic advisor assistant. Analyze the following conversation and extract the user's educational pathway information.

Conversation history:
${newConversation.map(msg => `${msg.role}: ${msg.content}`).join('\n')}

Extract the following information if mentioned:
- career_goal: The job/career they want
- current_education: Their current education level (High School Diploma/GED, Some College Credits, Associate Degree, Bachelor's Degree, Master's Degree)
- target_education: The education level they want to achieve
- two_year_college: Any 2-year college they mentioned from Florida
- four_year_college: Any 4-year university they mentioned from Florida

If the user mentions wanting to change something from a previous response, update that field accordingly.

Available Florida 2-year colleges: ${AVAILABLE_COLLEGES.twoYear.join(', ')}
Available Florida 4-year universities: ${AVAILABLE_COLLEGES.fourYear.join(', ')}

Return only the extracted information. If information is not mentioned or unclear, omit that field.`;

      const extractedData = await await invokeLLM({
        prompt: extractionPrompt,
        response_json_schema: {
          type: "object",
          properties: {
            career_goal: { type: "string" },
            current_education: { type: "string" },
            target_education: { type: "string" },
            two_year_college: { type: "string" },
            four_year_college: { type: "string" }
          }
        }
      });

      // Merge with existing extracted info
      const updatedInfo = { ...extractedInfo, ...extractedData };
      setExtractedInfo(updatedInfo);

      // Determine if we have enough information to generate a pathway
      const hasCareer = updatedInfo.career_goal;
      const hasCurrent = updatedInfo.current_education;
      const hasTarget = updatedInfo.target_education;

      // Check if colleges are needed and present
      const educationLevels = {
        "High School Diploma/GED": 1,
        "Some College Credits": 2,
        "Associate Degree": 3,
        "Bachelor's Degree": 4,
        "Master's Degree": 5
      };

      const currentOrder = educationLevels[updatedInfo.current_education] || 0;
      const targetOrder = educationLevels[updatedInfo.target_education] || 0;
      
      const needsTwoYear = currentOrder < 3 && targetOrder >= 3;
      const needsFourYear = targetOrder >= 4;
      
      const hasTwoYearIfNeeded = !needsTwoYear || updatedInfo.two_year_college;
      const hasFourYearIfNeeded = !needsFourYear || updatedInfo.four_year_college;

      let assistantResponse;
      let shouldGeneratePathway = false;

      if (hasCareer && hasCurrent && hasTarget && hasTwoYearIfNeeded && hasFourYearIfNeeded) {
        // We have all information - generate pathway
        shouldGeneratePathway = true;
        assistantResponse = "Perfect! I have all the information I need. Let me generate your personalized academic pathway...";
      } else {
        // Ask for missing information
        const responsePrompt = `You are a friendly academic advisor. Based on the conversation and the information we've gathered so far, respond to the user's message naturally.

Current information gathered:
${Object.entries(updatedInfo).map(([key, value]) => `- ${key}: ${value}`).join('\n') || 'None yet'}

Missing information:
${!hasCareer ? '- Career goal' : ''}
${!hasCurrent ? '- Current education level' : ''}
${!hasTarget ? '- Target education level' : ''}
${needsTwoYear && !updatedInfo.two_year_college ? '- 2-year college preference' : ''}
${needsFourYear && !updatedInfo.four_year_college ? '- 4-year university preference' : ''}

User's latest message: "${userMessage}"

Respond naturally and ask for ONE piece of missing information. Be conversational and encouraging. If they mentioned wanting to change something, acknowledge that change positively.

Available Florida 2-year colleges: ${AVAILABLE_COLLEGES.twoYear.join(', ')}
Available Florida 4-year universities: ${AVAILABLE_COLLEGES.fourYear.join(', ')}`;

        assistantResponse = await await invokeLLM({
          prompt: responsePrompt
        });
      }

      const updatedConversation = [
        ...newConversation,
        {
          role: "assistant",
          content: assistantResponse,
          timestamp: new Date().toISOString()
        }
      ];
      setConversation(updatedConversation);

      if (shouldGeneratePathway) {
        // Generate the pathway
        await generatePathway(updatedInfo, updatedConversation);
      }
    } catch (error) {
      console.error("Error processing message:", error);
      setConversation([
        ...newConversation,
        {
          role: "assistant",
          content: "I apologize, but I encountered an error processing your message. Please try again.",
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const generatePathway = async (info, conversationHistory) => {
    try {
      const educationLevels = {
        "High School Diploma/GED": 1,
        "Some College Credits": 2,
        "Associate Degree": 3,
        "Bachelor's Degree": 4,
        "Master's Degree": 5
      };

      const currentOrder = educationLevels[info.current_education];
      const targetOrder = educationLevels[info.target_education];

      let prompt = `You are an academic pathway advisor for Florida colleges. Create a detailed educational pathway for someone who wants to become a ${info.career_goal}.

Current education level: ${info.current_education}
Target education level: ${info.target_education}
`;

      if (info.two_year_college) {
        prompt += `2-year college: ${info.two_year_college}\n`;
      }
      if (info.four_year_college) {
        prompt += `4-year college: ${info.four_year_college}\n`;
      }

      prompt += `\nIMPORTANT: The user ALREADY HAS "${info.current_education}". DO NOT include this degree in the pathway. Start from the NEXT degree level they need to achieve "${info.target_education}".

Generate ONLY the educational steps needed between their current level and target level:
`;

      if (currentOrder < 3 && targetOrder >= 3) {
        prompt += `\n1. Associate's Degree phase at ${info.two_year_college}:
   - Use actual courses offered at ${info.two_year_college}
   - Include 5-8 relevant courses with real course codes from this college
   - Duration in semesters
   - Estimated total cost (use realistic tuition: ~$3,000-4,000/year for 2-year colleges)
   - Total credits required (typically 60 for Associate's)`;
      }

      if (currentOrder < 4 && targetOrder >= 4) {
        prompt += `\n2. Bachelor's Degree phase at ${info.four_year_college}:
   - Use actual courses offered at ${info.four_year_college}
   - Include 5-8 relevant courses with real course codes from this college
   - If transferring from Associate's, specify transfer credits (typically 60)
   - Duration in semesters for remaining coursework
   - Estimated total cost (use realistic tuition: FIU ~$6,500/year, UF/FSU ~$6,400/year, Private ~$35,000+/year)
   - Remaining credits needed (typically 60 more for Bachelor's = 120 total)`;
      }

      if (currentOrder < 5 && targetOrder >= 5) {
        prompt += `\n3. Master's Degree phase at ${info.four_year_college}:
   - Use actual graduate programs offered at ${info.four_year_college}
   - Duration in years (typically 2 years)
   - Estimated total cost (use realistic tuition: ~$15,000-20,000/year for public, ~$40,000+/year for private)
   - Total credits required (typically 30-36)`;
      }

      prompt += `\n\nFor EACH course, use realistic course codes and names that would actually be offered at these specific colleges.

Also provide:
- Total time from current level to target level
- Total cost estimate for the entire pathway
- Brief career outlook (2-3 sentences about ${info.career_goal} job prospects, salary range, and growth in Florida)

Be specific, realistic, and use actual course naming conventions from Florida colleges.`;

      const pathwayData = await await invokeLLM({
        prompt: prompt,
        response_json_schema: {
          type: "object",
          properties: {
            mdc_phase: {
              type: "object",
              properties: {
                degree_name: { type: "string" },
                courses: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      code: { type: "string" },
                      name: { type: "string" },
                      credits: { type: "number" }
                    }
                  }
                },
                duration_semesters: { type: "number" },
                total_cost: { type: "number" },
                total_credits: { type: "number" }
              }
            },
            fiu_phase: {
              type: "object",
              properties: {
                degree_name: { type: "string" },
                transfer_credits: { type: "number" },
                required_courses: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      code: { type: "string" },
                      name: { type: "string" },
                      credits: { type: "number" }
                    }
                  }
                },
                duration_semesters: { type: "number" },
                total_cost: { type: "number" },
                remaining_credits: { type: "number" }
              }
            },
            advanced_phase: {
              type: "object",
              properties: {
                masters: {
                  type: "object",
                  properties: {
                    degree_name: { type: "string" },
                    duration_years: { type: "number" },
                    total_cost: { type: "number" },
                    total_credits: { type: "number" }
                  }
                },
                phd: {
                  type: "object",
                  properties: {
                    degree_name: { type: "string" },
                    duration_years: { type: "number" },
                    funding_available: { type: "boolean" }
                  }
                }
              }
            },
            total_summary: {
              type: "object",
              properties: {
                total_years: { type: "number" },
                total_cost: { type: "number" },
                career_outlook: { type: "string" }
              }
            }
          }
        }
      });

      const savedPathway = await store.createPathway({
        career_goal: info.career_goal,
        current_education: info.current_education,
        target_education: info.target_education,
        two_year_college: info.two_year_college,
        four_year_college: info.four_year_college,
        conversation: conversationHistory,
        pathway_data: pathwayData
      });

      navigate(createPageUrl("PathwayResults") + `?id=${savedPathway.id}`);
    } catch (error) {
      console.error("Error generating pathway:", error);
      setConversation([
        ...conversationHistory,
        {
          role: "assistant",
          content: "I apologize, but I encountered an error while generating your pathway. Please try starting over.",
          timestamp: new Date().toISOString()
        }
      ]);
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-purple-900 via-blue-50 to-white">
      <div className="max-w-5xl mx-auto px-4 py-12 md:py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <div className="flex flex-row justify-center w-full mb-10">
            <img src="./ElevatePath_logo_flat.png" alt="ElevatePath Logo" className="h-30" />
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-4 tracking-tight">
            Find Your Academic Journey
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Chat with our AI advisor to create your personalized educational pathway
          </p>
        </motion.div>

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
                  <h3 className="text-lg font-semibold text-slate-900">Conversational AI</h3>
                </div>
                <p className="text-slate-600 leading-relaxed">
                  Simply chat with our AI advisor about your goals. No forms to fill out - just have a natural conversation!
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
                  <h3 className="text-lg font-semibold text-slate-900">Easy Updates</h3>
                </div>
                <p className="text-slate-600 leading-relaxed">
                  Changed your mind? Just tell the AI what you want to update and your pathway will adjust automatically.
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <Card className="border-slate-200 shadow-2xl">
            <CardContent className="p-6">
              <div className="h-[500px] flex flex-col">
                <div className="flex-1 overflow-y-auto mb-4 space-y-2 pr-2">
                  {conversation.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                  ))}
                  {isProcessing && (
                    <div className="flex gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center flex-shrink-0">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
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
      </div>
    </div>
  );
}