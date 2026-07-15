"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, Search, Filter, FileText, AlertOctagon, CheckCircle2, Clock } from "lucide-react";

interface Invoice {
  id: string;
  invoice_number: string;
  vendor_name: string | null;
  status: string;
  total_amount: number;
  currency: string;
  risk_score: number;
  fraud_score: number;
  health_score: number;
  auto_approved: boolean;
  created_at: string;
}

export default function InvoicesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: invoices, isLoading } = useQuery<Invoice[]>({
    queryKey: ["invoices", statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status_filter", statusFilter);
      const res = await fetch(`/api/v1/invoices?${params}`);
      if (!res.ok) throw new Error("Failed to fetch invoices");
      return res.json();
    },
  });

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
      pending_approval: "bg-amber-500/10 text-amber-400 border-amber-500/30",
      exception: "bg-rose-500/10 text-rose-400 border-rose-500/30",
      rejected: "bg-zinc-700 text-zinc-400 border-zinc-700",
      paid: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium border ${
          styles[status] || "bg-zinc-800 text-zinc-400"
        }`}
      >
        {status.replace("_", " ").toUpperCase()}
      </span>
    );
  };

  const riskIndicator = (risk: number) => {
    if (risk >= 80) return "text-rose-400";
    if (risk >= 50) return "text-amber-400";
    return "text-emerald-400";
  };

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-50">
      <div className="flex-1 flex flex-col">
        <header className="h-16 border-b border-zinc-900 px-6 flex items-center justify-between sticky top-0 bg-zinc-950/80 backdrop-blur-md">
          <h1 className="text-xl font-semibold tracking-tight">Invoice Processing Queue</h1>
          <Link
            href="/upload"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Upload Invoice
          </Link>
        </header>

        <div className="p-6 flex-1">
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search invoice number or vendor..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="flex items-center gap-2">
              {["all", "pending_approval", "approved", "exception"].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status === "all" ? null : status)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    (statusFilter === status) || (!statusFilter && status === "all")
                      ? "bg-indigo-600 text-white"
                      : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {status === "all" ? "All" : status.replace("_", " ").replace(/^\w/, (c) => c.toUpperCase())}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-xl bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800/80">
                  <th className="text-left px-4 py-3 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Invoice
                  </th>
                  <th className="text-left px-4 py-3 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Vendor
                  </th>
                  <th className="text-right px-4 py-3 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="text-center px-4 py-3 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Risk
                  </th>
                  <th className="text-center px-4 py-3 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-right px-4 py-3 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                      Loading invoices...
                    </td>
                  </tr>
                ) : (invoices || []).length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                      No invoices found
                    </td>
                  </tr>
                ) : (
                  (invoices || []).map((inv) => (
                    <tr key={inv.id} className="border-b border-zinc-800/40 hover:bg-zinc-900/60 transition-colors">
                      <td className="px-4 py-3">
                        <Link href={`/invoices/${inv.id}`} className="font-medium text-zinc-200 hover:text-indigo-400">
                          {inv.invoice_number}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-zinc-400">{inv.vendor_name || "—"}</td>
                      <td className="px-4 py-3 text-right font-mono text-zinc-200">
                        {inv.currency} {inv.total_amount.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-semibold ${riskIndicator(inv.risk_score)}`}>
                          {inv.risk_score}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">{statusBadge(inv.status)}</td>
                      <td className="px-4 py-3 text-right text-zinc-500">
                        {new Date(inv.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}