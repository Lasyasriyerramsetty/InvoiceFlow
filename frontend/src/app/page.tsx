"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  AlertOctagon,
  Zap,
  DollarSign,
  Search,
  Bot,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Sidebar from "@/components/Sidebar";
import CopilotPanel from "@/components/CopilotPanel";
import { apiUrl } from "@/lib/api";

interface VendorScore {
  vendor_id: string;
  name: string;
  trust_score: number;
  contract_health: number;
}

// Consistent currency formatting to avoid hydration errors
const formatCurrency = (value: number) => {
  const integerPart = Math.floor(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const decimalPart = (value % 1).toFixed(2).substring(1);
  return `$${integerPart}${decimalPart}`;
};

export default function Dashboard() {
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: kpis, isLoading } = useQuery({
    queryKey: ["dashboardKPIs"],
    queryFn: async () => {
      const res = await fetch(apiUrl("dashboard/kpis"));
      if (!res.ok) throw new Error("Failed to fetch dashboard KPIs");
      return res.json();
    },
    retry: 1,
    refetchInterval: 15000,
  });

  const mockKPIs = {
    total_invoices_count: 362,
    total_invoice_value: 2948500.0,
    pending_approvals: 18,
    auto_approvals: 294,
    fraud_alerts: 4,
    savings_generated: 58970.0,
    avg_approval_time_hours: 14.2,
    manual_approvals: 50,
    exception_breakdown: {
      price_mismatch: 6,
      missing_po: 4,
      duplicate_invoice: 1,
      policy_violation: 5,
      fraud_indicators: 2,
    },
    monthly_trend: [
      { month: "Jan", invoices: 120, exceptions: 12, auto_approved: 88, savings: 12400 },
      { month: "Feb", invoices: 145, exceptions: 15, auto_approved: 110, savings: 16200 },
      { month: "Mar", invoices: 180, exceptions: 22, auto_approved: 130, savings: 19800 },
      { month: "Apr", invoices: 210, exceptions: 18, auto_approved: 165, savings: 24500 },
      { month: "May", invoices: 240, exceptions: 28, auto_approved: 182, savings: 29800 },
      { month: "Jun", invoices: 295, exceptions: 32, auto_approved: 220, savings: 36400 },
      { month: "Jul", invoices: 362, exceptions: 18, auto_approved: 294, savings: 58970 },
    ],
    risk_heatmap: [
      { department: "Finance", category: "Price", risk: 85, count: 6 },
      { department: "Procurement", category: "PO", risk: 65, count: 4 },
      { department: "IT", category: "Tax", risk: 20, count: 1 },
      { department: "Operations", category: "Compliance", risk: 45, count: 3 },
      { department: "Legal", category: "Fraud", risk: 95, count: 2 },
      { department: "HR", category: "Vendor", risk: 10, count: 0 },
    ],
    vendor_scores: [
      { vendor_id: "1", name: "Global Tech Solutions", trust_score: 95, contract_health: 98 },
      { vendor_id: "2", name: "Orion Logistics", trust_score: 88, contract_health: 75 },
      { vendor_id: "3", name: "Acme Corporation Pvt Ltd", trust_score: 82, contract_health: 88 },
      { vendor_id: "4", name: "Vertex Systems Inc", trust_score: 42, contract_health: 55 },
    ],
  };

  const activeKPIs = kpis || mockKPIs;

  const statCards = [
    {
      title: "Total Invoices Value",
      value: formatCurrency(activeKPIs.total_invoice_value),
      subtitle: `${activeKPIs.total_invoices_count} documents ingested`,
      icon: DollarSign,
      color: "text-sky-600",
      bg: "status-info",
    },
    {
      title: "Auto-Approvals",
      value: `${((activeKPIs.auto_approvals / activeKPIs.total_invoices_count) * 100).toFixed(1)}%`,
      subtitle: `${activeKPIs.auto_approvals} touchless processes`,
      icon: Zap,
      color: "text-amber-600",
      bg: "status-warning",
    },
    {
      title: "Pending Exceptions",
      value: `${activeKPIs.pending_approvals}`,
      subtitle: "Requires manual action",
      icon: AlertOctagon,
      color: "text-rose-600",
      bg: "status-error",
    },
    {
      title: "Savings Generated",
      value: formatCurrency(activeKPIs.savings_generated),
      subtitle: "2.0% variance detection recovery",
      icon: TrendingUp,
      color: "text-emerald-600",
      bg: "status-success",
    },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-900 dark:text-slate-100 font-sans">
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-x-hidden">
        {/* Top bar with Search and Copilot Button */}
        <header className="h-16 border-b border-slate-200 dark:border-slate-700 px-8 flex items-center justify-between bg-white/80 dark:bg-slate-900/80 sticky top-0 backdrop-blur-md z-10">
          <div className="relative w-96">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Global Search (Press ⌘K)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsCopilotOpen(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white shadow-md hover:shadow-lg transition-all status-indicator"
            >
              <Bot className="w-4 h-4" />
              Ask Copilot
            </button>
            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 flex items-center justify-center text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer">
              AC
            </div>
          </div>
        </header>

        {/* Dashboard Panels */}
        <div className="p-8 space-y-8 flex-1">
          {/* Headline */}
          <div className="flex flex-col gap-1.5">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Financial Command Center</h2>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Autonomous multi-agent invoice processing, 3-way PO matching, and anomaly inspection.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {statCards.map((card, idx) => {
              const Icon = card.icon;
              return (
                <div
                  key={idx}
                  className={`p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-enterprise hover:shadow-md transition-all ${card.bg}`}
                >
                  <div className="flex justify-between items-start">
                    <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">{card.title}</span>
                    <div className={`p-2 rounded-lg ${card.bg} ${card.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="mt-4">
                    <h3 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{card.value}</h3>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">{card.subtitle}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Charts & Trends panel */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Trend Chart */}
            <div className="lg:col-span-2 p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-enterprise">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Processing Performance Trends</h3>
                  <p className="text-[10px] text-slate-600 dark:text-slate-400">Autonomous approvals vs flagged exceptions</p>
                </div>
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
                    <span className="w-2.5 h-1 bg-sky-500 rounded"></span> Invoices
                  </span>
                  <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
                    <span className="w-2.5 h-1 bg-emerald-500 rounded"></span> Savings
                  </span>
                  <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
                    <span className="w-2.5 h-1 bg-rose-500 rounded"></span> Exceptions
                  </span>
                </div>
              </div>

              <div className="flex-1 w-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={activeKPIs.monthly_trend} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                    <defs>
                      <linearGradient id="colorInvoices" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "8px", fontSize: "11px" }}
                    />
                    <Area
                      type="monotone"
                      dataKey="invoices"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorInvoices)"
                    />
                    <Area type="monotone" dataKey="exceptions" stroke="#f43f5e" strokeWidth={1.5} fillOpacity={0} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Exception breakdown list */}
            <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-enterprise flex flex-col h-[350px]">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-1">Exception Category Audit</h3>
              <p className="text-[10px] text-slate-600 dark:text-slate-400 mb-6">Categorized audit matches for current queue</p>

              <div className="flex-1 overflow-y-auto space-y-4">
                {Object.entries(activeKPIs.exception_breakdown).map(([category, count]) => {
                  const countNum = typeof count === "number" ? count : 0;
                  const percentage = activeKPIs.pending_approvals > 0 ? (countNum / activeKPIs.pending_approvals) * 100 : 0;
                  const label = category.replace("_", " ").toUpperCase();
                  const barColor =
                    category === "duplicate_invoice" || category === "fraud_indicators"
                      ? "bg-rose-500"
                      : "bg-amber-500";

                  return (
                    <div key={category} className="space-y-1.5">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">{label}</span>
                        <span className="text-slate-900 dark:text-slate-100 font-semibold">{countNum}</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div className={`h-full ${barColor}`} style={{ width: `${percentage}%` }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Lower Panel: Heatmap and Vendors */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Risk Heatmap */}
            <div className="lg:col-span-2 p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-enterprise">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-1">Department Exception Heatmap</h3>
              <p className="text-[10px] text-slate-600 dark:text-slate-400 mb-6">Risk scoring by department activity</p>

              <div className="grid grid-cols-7 gap-2 text-center text-[10px]">
                <div className="font-semibold text-slate-500 dark:text-slate-400 text-left pt-2">DEPT</div>
                <div className="font-medium text-slate-600 dark:text-slate-400 py-1 rounded bg-slate-100 dark:bg-slate-700">Price</div>
                <div className="font-medium text-slate-600 dark:text-slate-400 py-1 rounded bg-slate-100 dark:bg-slate-700">Tax</div>
                <div className="font-medium text-slate-600 dark:text-slate-400 py-1 rounded bg-slate-100 dark:bg-slate-700">PO</div>
                <div className="font-medium text-slate-600 dark:text-slate-400 py-1 rounded bg-slate-100 dark:bg-slate-700">Vendor</div>
                <div className="font-medium text-slate-600 dark:text-slate-400 py-1 rounded bg-slate-100 dark:bg-slate-700">Fraud</div>
                <div className="font-medium text-slate-600 dark:text-slate-400 py-1 rounded bg-slate-100 dark:bg-slate-700">Compliance</div>

                {["Finance", "Procurement", "IT", "Operations", "Legal"].map((dept) => {
                  return (
                    <React.Fragment key={dept}>
                      <div className="text-slate-600 dark:text-slate-400 text-left py-2 font-medium">{dept}</div>
                      {["Price", "Tax", "PO", "Vendor", "Fraud", "Compliance"].map((cat) => {
                        const cell = activeKPIs.risk_heatmap.find(
                          (h: { department: string; category: string; risk: number; count: number }) => h.department === dept && h.category === cat
                        ) || { risk: 10, count: 0 };

                        let cellBg = "bg-slate-100 dark:bg-slate-700 text-slate-500";
                        if (cell.risk > 80) cellBg = "bg-rose-100 dark:bg-rose-900/30 border border-rose-300 dark:border-rose-700 text-rose-700 dark:text-rose-300";
                        else if (cell.risk > 50) cellBg = "bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300";
                        else if (cell.risk > 20) cellBg = "bg-sky-100 dark:bg-sky-900/30 border border-sky-300 dark:border-sky-700 text-sky-700 dark:text-sky-300";

                        return (
                          <div
                            key={cat}
                            className={`py-2 rounded-lg flex flex-col justify-center items-center font-semibold transition-all ${cellBg}`}
                            title={`${dept} - ${cat}: Risk score ${cell.risk}%`}
                          >
                            <span>{cell.risk}</span>
                          </div>
                        );
                      })}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>

            {/* Vendor Scoreboard */}
            <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-enterprise flex flex-col">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-1">Vendor Network Rankings</h3>
              <p className="text-[10px] text-slate-600 dark:text-slate-400 mb-6">Trust ratings and compliance checks</p>

              <div className="flex-1 overflow-y-auto space-y-4">
                {activeKPIs.vendor_scores.map((vendor: VendorScore) => {
                  const isLow = vendor.trust_score < 60;
                  return (
                    <div key={vendor.vendor_id} className="flex justify-between items-center text-xs">
                      <div>
                        <p className="font-semibold text-slate-800 dark:text-slate-200">{vendor.name}</p>
                        <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Contract Health: {vendor.contract_health}%</p>
                      </div>
                      <div className="text-right">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            isLow ? "bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-700" : "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700"
                          }`}
                        >
                          {vendor.trust_score} Trust
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Floating AI Copilot Panel */}
      <CopilotPanel
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        contextData={{
          invoice: { total_amount: 114165.0, status: "pending_approval" },
        }}
      />
    </div>
  );
}