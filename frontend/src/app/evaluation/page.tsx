"use client";

import { useEffect, useState } from "react";

interface BusinessMetrics {
  total_invoices_processed: number;
  straight_through_rate: number;
  exception_rate: number;
  auto_approved_count: number;
  manual_review_count: number;
  total_savings: number;
  avg_processing_time_ms: number;
  po_match_rate: number;
  contract_match_rate: number;
  fraud_detected: number;
  duplicate_prevented: number;
}

interface AgentMetric {
  total_executions: number;
  success_rate: number;
  avg_duration_ms: number;
  avg_confidence: number;
  tool_call_success_rate: number;
}

interface EvalSummary {
  total_traces: number;
  avg_pipeline_latency_ms: number;
  business_metrics: BusinessMetrics;
  agent_metrics: Record<string, AgentMetric>;
  top_tools: Array<{ tool: string; count: number }>;
}

export default function EvaluationDashboard() {
  const [data, setData] = useState<EvalSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/evaluation/summary")
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-slate-600">Loading evaluation metrics...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-slate-600">No evaluation data available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Evaluation Dashboard
        </h1>
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Agent performance, tool usage, and business impact metrics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Invoices"
          value={data.business_metrics.total_invoices_processed.toString()}
          subtitle="Processed"
          icon="📥"
        />
        <MetricCard
          title="Straight-Through Rate"
          value={`${data.business_metrics.straight_through_rate.toFixed(1)}%`}
          subtitle="Auto-approved"
          icon="⚡"
        />
        <MetricCard
          title="Exception Rate"
          value={`${data.business_metrics.exception_rate.toFixed(1)}%`}
          subtitle="Flagged"
          icon="⚠️"
        />
        <MetricCard
          title="Avg Processing Time"
          value={`${data.avg_pipeline_latency_ms.toFixed(0)}ms`}
          subtitle="Pipeline latency"
          icon="⏱️"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Business Metrics
          </h2>
          <div className="space-y-3 text-sm">
            <Row label="Auto-Approved" value={data.business_metrics.auto_approved_count.toString()} />
            <Row label="Manual Review" value={data.business_metrics.manual_review_count.toString()} />
            <Row label="Total Savings" value={`$${data.business_metrics.total_savings.toFixed(2)}`} />
            <Row label="PO Match Rate" value={`${data.business_metrics.po_match_rate.toFixed(1)}%`} />
            <Row label="Contract Match Rate" value={`${data.business_metrics.contract_match_rate.toFixed(1)}%`} />
            <Row label="Fraud Detected" value={data.business_metrics.fraud_detected.toString()} />
            <Row label="Duplicates Prevented" value={data.business_metrics.duplicate_prevented.toString()} />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Agent Performance
          </h2>
          <div className="space-y-4">
            {Object.entries(data.agent_metrics).map(([name, metrics]) => (
              <div key={name} className="border rounded-lg p-3">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 capitalize">
                      {name.replace(/_/g, " ")}
                    </p>
                    <p className="text-[10px] text-slate-500">
                      {metrics.total_executions} executions • {metrics.avg_duration_ms.toFixed(0)}ms avg
                    </p>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      metrics.success_rate >= 95
                        ? "bg-emerald-100 text-emerald-700"
                        : metrics.success_rate >= 80
                        ? "bg-amber-100 text-amber-700"
                        : "bg-rose-100 text-rose-700"
                    }`}
                  >
                    {metrics.success_rate.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-indigo-500 h-1.5 rounded-full"
                    style={{ width: `${metrics.success_rate}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-500 mt-1">
                  Confidence: {(metrics.avg_confidence * 100).toFixed(0)}% • Tools:{" "}
                  {metrics.tool_call_success_rate.toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
          Top Tools Used
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {data.top_tools.map((item) => (
            <div
              key={item.tool}
              className="border rounded-lg p-3 flex items-center justify-between"
            >
              <div>
                <p className="text-xs font-medium text-slate-900 dark:text-slate-100 capitalize">
                  {item.tool.split(".")[1]?.replace(/_/g, " ") ?? item.tool}
                </p>
                <p className="text-[10px] text-slate-500">
                  {item.tool.split(".")[0]?.replace(/_/g, " ")}
                </p>
              </div>
              <span className="text-lg font-bold text-indigo-600">{item.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      <div className="flex justify-between items-start">
        <span className="text-xs text-slate-600 dark:text-slate-400">{title}</span>
        <span className="text-lg">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">{value}</p>
      <p className="text-[10px] text-slate-500">{subtitle}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center pb-2 border-b last:border-0">
      <span className="text-slate-600 dark:text-slate-400">{label}</span>
      <span className="font-semibold text-slate-900 dark:text-slate-100">{value}</span>
    </div>
  );
}