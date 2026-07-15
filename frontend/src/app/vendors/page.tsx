"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, Shield, TrendingUp, TrendingDown, AlertOctagon } from "lucide-react";
import { apiUrl } from "@/lib/api";

interface Vendor {
  vendor_id: string;
  name: string;
  trust_score: number;
  contract_health: number;
}

export default function VendorsPage() {
  const { data: vendors, isLoading } = useQuery<Vendor[]>({
    queryKey: ["vendorScores"],
    queryFn: async () => {
      const res = await fetch(apiUrl("dashboard/kpis"));
      if (!res.ok) throw new Error("Failed to fetch vendors");
      const kpis = await res.json();
      return kpis.vendor_scores || [];
    },
  });

  const getTrustColor = (score: number) => {
    if (score >= 90) return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
    if (score >= 70) return "text-amber-400 border-amber-500/30 bg-amber-500/10";
    return "text-rose-400 border-rose-500/30 bg-rose-500/10";
  };

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-50">
      <div className="flex-1 flex flex-col">
        <header className="h-16 border-b border-zinc-900 px-6 flex items-center sticky top-0 bg-zinc-950/80 backdrop-blur-md">
          <h1 className="text-xl font-semibold tracking-tight">Vendor Network Analytics</h1>
        </header>

        <div className="p-6 flex-1">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {isLoading ? (
              <div className="col-span-3 text-center text-zinc-500">Loading vendor data...</div>
            ) : (
              (vendors || []).map((vendor) => (
                <div key={vendor.vendor_id} className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-zinc-200">{vendor.name}</h3>
                      <p className="text-[10px] text-zinc-500">Vendor ID: {vendor.vendor_id}</p>
                    </div>
                    <div className={`p-2 rounded-lg ${getTrustColor(vendor.trust_score)}`}>
                      <Shield className="w-4 h-4" />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-zinc-400">Trust Score</span>
                        <span className="font-semibold text-zinc-200">{vendor.trust_score}/100</span>
                      </div>
                      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500"
                          style={{ width: `${vendor.trust_score}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-zinc-400">Contract Health</span>
                        <span className="font-semibold text-zinc-200">{vendor.contract_health}/100</span>
                      </div>
                      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500"
                          style={{ width: `${vendor.contract_health}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-zinc-800">
                    <p className="text-[10px] text-zinc-500">
                      {vendor.trust_score < 60
                        ? "⚠️ Vendor requires additional scrutiny"
                        : vendor.trust_score >= 90
                        ? "✅ Trusted vendor - auto-approval eligible"
                        : "📋 Standard review process"}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}