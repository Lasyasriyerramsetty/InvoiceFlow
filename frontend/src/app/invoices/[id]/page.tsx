"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { FileText, AlertOctagon, Shield, CheckCircle2, Clock, DollarSign, Bot } from "lucide-react";
import Link from "next/link";
import CopilotPanel from "@/components/CopilotPanel";
import { apiUrl } from "@/lib/api";

interface InvoiceDetail {
  id: string;
  invoice_number: string;
  vendor: { id: string; name: string } | null;
  status: string;
  total_amount: number;
  currency: string;
  risk_score: number;
  fraud_score: number;
  health_score: number;
  compliance_score: number;
  auto_approved: boolean;
  ai_summary: string;
  extracted_data: {
    invoice_number: string;
    vendor_name: string;
    invoice_date: string;
    due_date: string;
    subtotal: number;
    tax_amount: number;
    payment_terms: string;
    gst_number: string;
    line_items: Array<{
      line_number: number;
      description: string;
      quantity: number;
      unit_price: number;
      total_amount: number;
    }>;
  };
  exceptions: Array<{
    id: string;
    category: string;
    severity: string;
    title: string;
    description: string;
    reasoning: string;
    confidence: number;
    suggested_resolution: string;
    financial_impact: number;
  }>;
  agent_insights: Array<{
    agent: string;
    confidence: number;
    summary: string;
    reasoning?: string;
  }>;
  approvals: Array<{
    role: string;
    department: string;
    status: string;
    reason: string;
  }>;
}

export default function InvoiceDetailPage() {
  const params = useParams();
  const invoiceId = params.id as string;
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  const { data: invoice, isLoading } = useQuery<InvoiceDetail>({
    queryKey: ["invoice", invoiceId],
    queryFn: async () => {
      const res = await fetch(apiUrl(`invoices/${invoiceId}`));
      if (!res.ok) throw new Error("Failed to fetch invoice");
      return res.json();
    },
  });

  if (isLoading || !invoice) {
    return (
      <div className="flex min-h-screen bg-zinc-950 text-zinc-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-zinc-400">Loading invoice...</div>
        </div>
      </div>
    );
  }

  const getRiskColor = (risk: number) => {
    if (risk >= 80) return "text-rose-400";
    if (risk >= 50) return "text-amber-400";
    return "text-emerald-400";
  };

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-50">
      <div className="flex-1 flex flex-col">
        <header className="h-16 border-b border-zinc-900 px-6 flex items-center justify-between sticky top-0 bg-zinc-950/80 backdrop-blur-md">
          <h1 className="text-xl font-semibold tracking-tight">Invoice: {invoice.invoice_number}</h1>
          <button
            onClick={() => setIsCopilotOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold transition-colors"
          >
            <Bot className="w-4 h-4" />
            Ask Copilot
          </button>
        </header>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <p className="text-[10px] text-zinc-500">Total Amount</p>
              <p className="text-2xl font-bold text-zinc-100">
                {invoice.currency} {invoice.total_amount.toLocaleString()}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <p className="text-[10px] text-zinc-500">Risk Score</p>
              <p className={`text-2xl font-bold ${getRiskColor(invoice.risk_score)}`}>{invoice.risk_score}</p>
            </div>
            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <p className="text-[10px] text-zinc-500">Fraud Score</p>
              <p className={`text-2xl font-bold ${getRiskColor(invoice.fraud_score)}`}>{invoice.fraud_score}</p>
            </div>
            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <p className="text-[10px] text-zinc-500">Status</p>
              <p className="text-2xl font-bold text-zinc-100 capitalize">{invoice.status.replace("_", " ")}</p>
            </div>
          </div>

          {invoice.exceptions.length > 0 && (
            <div className="p-5 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 text-rose-400" />
                Detected Exceptions ({invoice.exceptions.length})
              </h2>
              <div className="space-y-3">
                {invoice.exceptions.map((exc) => (
                  <div key={exc.id} className="p-4 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-zinc-200">{exc.title}</h3>
                        <p className="text-xs text-zinc-400 mt-1">{exc.description}</p>
                        <p className="text-[10px] text-zinc-500 mt-2">
                          <span className="text-indigo-400">Reasoning:</span> {exc.reasoning}
                        </p>
                      </div>
                      <span className="text-[10px] px-2 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        {exc.severity}
                      </span>
                    </div>
                    {exc.suggested_resolution && (
                      <div className="mt-3 p-2.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                        <p className="text-[10px] text-indigo-300">
                          <span className="font-semibold">Recommendation:</span> {exc.suggested_resolution}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {invoice.extracted_data && (
            <div className="p-5 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                Extracted Line Items
              </h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-zinc-800/80">
                    <th className="text-left py-2 text-zinc-400">#</th>
                    <th className="text-left py-2 text-zinc-400">Description</th>
                    <th className="text-right py-2 text-zinc-400">Qty</th>
                    <th className="text-right py-2 text-zinc-400">Unit Price</th>
                    <th className="text-right py-2 text-zinc-400">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.extracted_data.line_items.map((item) => (
                    <tr key={item.line_number} className="border-b border-zinc-800/40">
                      <td className="py-2 text-zinc-500">{item.line_number}</td>
                      <td className="py-2 text-zinc-200">{item.description}</td>
                      <td className="py-2 text-right text-zinc-500">{item.quantity}</td>
                      <td className="py-2 text-right text-zinc-200 font-mono">{item.unit_price}</td>
                      <td className="py-2 text-right text-zinc-100 font-mono font-semibold">{item.total_amount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {invoice.agent_insights.length > 0 && (
            <div className="p-5 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                AI Agent Insights
              </h2>
              <div className="space-y-3">
                {invoice.agent_insights.map((insight, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-indigo-400">{insight.agent}</span>
                      <span className="text-[10px] text-zinc-500">{(insight.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                    <p className="text-xs text-zinc-300">{insight.reasoning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <CopilotPanel
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        invoiceId={invoiceId}
        contextData={{ invoice }}
      />
    </div>
  );
}