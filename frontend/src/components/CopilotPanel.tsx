"use client";

import React, { useState, useEffect, useRef } from "react";
import { Bot, X, Send, Sparkles, AlertCircle, Quote } from "lucide-react";
import { apiUrl } from "@/lib/api";

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  invoiceId?: string;
  contextData?: any;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
  confidence?: number;
  evidence?: string[];
  citations?: string[];
  intent?: string;
}

export default function CopilotPanel({
  isOpen,
  onClose,
  invoiceId,
  contextData,
}: CopilotPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hello! I am your AP Exception Assistant. You can ask me questions about this invoice, matched PO numbers, payment terms, or policy violations.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      text: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    try {
      const response = await fetch(apiUrl("copilot/ask"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer mock_token`, // In real app, attach token
        },
        body: JSON.stringify({
          question: input,
          invoice_id: invoiceId || null,
          context: contextData || {},
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${Date.now()}-ai`,
            role: "assistant",
            text: data.answer,
            timestamp: new Date(),
            confidence: data.confidence,
            evidence: data.evidence,
            citations: data.citations,
            intent: data.intent,
          },
        ]);
      } else {
        throw new Error("API call failed");
      }
    } catch (err) {
      // Offline / Mock Fallback if backend is not running or has no connection
      setTimeout(() => {
        let answer = "I am currently running in offline mock mode. Let me analyze the invoice data: ";
        let confidence = 0.85;
        let evidence: string[] = [];
        let citations: string[] = [];

        const promptLower = input.toLowerCase();
        if (promptLower.includes("why rejected") || promptLower.includes("exception") || promptLower.includes("issue")) {
          answer = "Invoice was flagged because the billed Cloud Services License price of ₹467.50 exceeds the contractually locked limit of ₹425.00 (+10% variance). Under PROC-001, any variance exceeding 3% must be routed for manual Procurement validation.";
          evidence = ["Billed Price: ₹467.50", "Contract Limit: ₹425.00", "Variance: 10%"];
          citations = ["Contract Clause 4.2", "Procurement SOP PROC-001"];
        } else if (promptLower.includes("duplicate")) {
          answer = "Invoice INV-OR-7711 is a duplicate. We detected a paid invoice with the exact same number, amount (€10,115.00), and vendor from June 15, 2026. Payment has been blocked to avoid double-payment loss.";
          evidence = ["Match ID: INV-OR-7711", "Past Payment: 2026-06-15"];
          citations = ["Anti-Fraud Policy FIN-009"];
        } else if (promptLower.includes("explain") || promptLower.includes("summary")) {
          answer = `Invoice INV-2024-1456 is from Acme Corporation Pvt Ltd for a total of ₹114,165.00 (Subtotal ₹96,750.00 + 18% GST). It contains 3 line items. The invoice has been flagged due to unit price mismatches on Cloud Services and Annual Maintenance.`;
          evidence = ["Subtotal: ₹96,750.00", "Tax: ₹17,415.00 (18% GST)"];
          citations = ["Invoice Document OCR"];
        } else if (promptLower.includes("esg") || promptLower.includes("carbon")) {
          answer = "Acme Corporation has an ESG score of 78/100, which is compliant. Carbon impact tracking reports an estimated 0.12 MT CO2e for the cloud computing resources supplied under this SLA. Recommended next action: proceed with green procurement offset credits.";
          confidence = 0.92;
          evidence = ["ESG Rating: 78/100", "CO2e footprint: 0.12 MT"];
        } else {
          answer = `I analyzed the context. The active invoice contains total amount of ${contextData?.invoice?.total_amount || "₹114,165"} and is currently under status: ${contextData?.invoice?.status || "pending_approval"}. Let me know if I should verify specific contract clauses for you.`;
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${Date.now()}-ai`,
            role: "assistant",
            text: answer,
            timestamp: new Date(),
            confidence,
            evidence,
            citations,
          },
        ]);
      }, 800);
    } finally {
      setIsSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 border-l border-zinc-800 bg-zinc-950/90 backdrop-blur-xl flex flex-col z-50 shadow-2xl animate-in slide-in-from-right duration-300">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-semibold text-sm text-zinc-100">AI Invoice Copilot</h2>
            <span className="text-[10px] text-zinc-500 font-medium">Ready to assist</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col max-w-[85%] ${
              msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
            }`}
          >
            <div
              className={`p-3 rounded-2xl text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-tr-none"
                  : "bg-zinc-900 text-zinc-200 border border-zinc-800/80 rounded-tl-none"
              }`}
            >
              {msg.text}
            </div>

            {/* AI Insights & Reasoning Attachments */}
            {msg.role === "assistant" && msg.confidence && (
              <div className="w-full mt-2 p-2.5 rounded-xl bg-zinc-950/60 border border-zinc-900 space-y-2 text-[10px]">
                {/* Confidence Bar */}
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Confidence Score:</span>
                  <span className="font-semibold text-indigo-400">
                    {(msg.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500"
                    style={{ width: `${msg.confidence * 100}%` }}
                  ></div>
                </div>

                {/* Evidence */}
                {msg.evidence && msg.evidence.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-zinc-500 font-medium">Evidence Found:</span>
                    <ul className="list-disc pl-3 text-zinc-300 space-y-0.5">
                      {msg.evidence.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="pt-1.5 border-t border-zinc-900 flex flex-wrap gap-1">
                    {msg.citations.map((cit, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-zinc-900 text-[9px] text-zinc-400 border border-zinc-800/80"
                      >
                        <Quote className="w-2 h-2 text-indigo-400" />
                        {cit}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            <span className="text-[9px] text-zinc-600 mt-1 px-1">
              {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        ))}

        {isSending && (
          <div className="flex items-center gap-2 text-xs text-zinc-500 italic p-1">
            <Bot className="w-4 h-4 animate-bounce text-indigo-400" />
            AI Agent is reading documentation and reasoning...
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-4 border-t border-zinc-800 bg-zinc-950">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask AI Copilot..."
            className="w-full bg-zinc-900 text-xs text-zinc-100 placeholder-zinc-500 rounded-xl pl-3 pr-10 py-3 border border-zinc-800 focus:outline-none focus:border-zinc-700 transition-colors"
          />
          <button
            type="submit"
            className="absolute right-2 p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-[9px] text-zinc-600 text-center mt-2">
          Agent utilizes semantic vector indexes and hybrid search results.
        </p>
      </form>
    </div>
  );
}
