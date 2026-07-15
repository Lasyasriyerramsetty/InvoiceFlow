"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  UploadCloud,
  Users,
  Settings,
  ShieldAlert,
  Bot,
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Invoices", href: "/invoices", icon: FileText },
    { name: "Upload Center", href: "/upload", icon: UploadCloud },
    { name: "Vendor Analytics", href: "/vendors", icon: Users },
  ];

  return (
    <aside className="w-64 border-r border-zinc-800 bg-zinc-950/80 backdrop-blur-md flex flex-col h-screen sticky top-0">
      {/* Platform Title */}
      <div className="p-6 border-b border-zinc-900">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
            AP
          </div>
          <div>
            <h1 className="font-semibold text-sm leading-none text-zinc-100">
              Antigravity Finance
            </h1>
            <span className="text-[10px] text-zinc-500 font-medium tracking-wide uppercase">
              Exception Agent v1.0
            </span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-zinc-900 text-white shadow-sm ring-1 ring-zinc-800"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-blue-500" : ""}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* System Status / Copilot shortcut */}
      <div className="p-4 border-t border-zinc-900 space-y-3">
        <div className="p-3.5 rounded-xl bg-zinc-900/50 border border-zinc-800/60 flex items-start gap-3">
          <Bot className="w-5 h-5 text-indigo-400 mt-0.5 shrink-0 animate-pulse" />
          <div>
            <p className="text-xs font-semibold text-zinc-200">AI Copilot Active</p>
            <p className="text-[10px] text-zinc-500 mt-0.5 leading-normal">
              Ask questions about billing exceptions in real time.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-zinc-500 px-2">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Agent Engine: online
          </div>
          <span className="font-mono text-[10px]">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}
