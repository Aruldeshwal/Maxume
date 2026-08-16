import React from "react";
import { Cpu, Activity, ShieldCheck, ChevronRight, FolderCheck, Sparkles, Layers } from "lucide-react";
import QuotaRing from "../components/QuotaRing";

interface DashboardProps {
  onNavigateToOptimizer: () => void;
  totalApplications: number;
  ollamaModel: string;
  ollamaVram: string;
  ollamaOnline: boolean;
  quotas: {
    gemini: { used: number; total: number };
    groq: { used: number; total: number };
    google_cse: { used: number; total: number };
  };
}

export const Dashboard: React.FC<DashboardProps> = ({
  onNavigateToOptimizer,
  totalApplications,
  ollamaModel,
  ollamaVram,
  ollamaOnline,
  quotas,
}) => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Banner CTA */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-background-card via-[#1A1A1A] to-background-card border border-border-subtle flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-legion-crimson text-white tracking-wider uppercase">
              Tactical Workspace
            </span>
            <span className="text-xs text-text-muted font-mono">• Zero Operating Cost Stack</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-white tracking-tight">
            Maxume Job Application Assistant
          </h1>
          <p className="text-xs text-text-secondary max-w-xl leading-relaxed">
            Local-first AI engine pairing Ollama local inference with zero-cost cloud APIs. 
            Automates project indexing, DOCX paragraph rebuilding, and grounded personalization.
          </p>
        </div>

        <button
          onClick={onNavigateToOptimizer}
          className="px-5 py-3 rounded-lg bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs tracking-wider uppercase shadow-[0_0_20px_rgba(225,29,72,0.5)] transition-all flex items-center space-x-2 flex-shrink-0 group"
        >
          <Sparkles className="w-4 h-4 text-white group-hover:rotate-12 transition-transform" />
          <span>Start New Job Optimization</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Hardware & System Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Local LLM Card */}
        <div className="p-4 rounded-lg bg-background-card border border-border-subtle hover:border-border-strong transition-all space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono text-text-secondary uppercase">Local Ollama Engine</span>
            <div className="flex items-center space-x-1.5">
              <span className={`h-2 w-2 rounded-full ${ollamaOnline ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`} />
              <span className="text-[10px] font-mono text-text-muted">{ollamaOnline ? "ONLINE" : "OFFLINE"}</span>
            </div>
          </div>
          <div className="text-base font-bold font-mono text-white flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>{ollamaModel || "qwen2.5:7b-instruct"}</span>
          </div>
          <div className="text-xs text-text-secondary flex justify-between font-mono pt-1 border-t border-border-subtle/60">
            <span>VRAM Allocation:</span>
            <span className="text-emerald-400 font-semibold">{ollamaVram || "4.8GB / 5.2GB"}</span>
          </div>
        </div>

        {/* Project Watcher SSOT Card */}
        <div className="p-4 rounded-lg bg-background-card border border-border-subtle hover:border-border-strong transition-all space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono text-text-secondary uppercase">Project SSOT Manager</span>
            <Activity className="w-4 h-4 text-legion-crimson" />
          </div>
          <div className="text-base font-bold font-mono text-white flex items-center space-x-2">
            <Layers className="w-4 h-4 text-legion-crimson" />
            <span>Incremental Git Sync</span>
          </div>
          <div className="text-xs text-text-secondary flex justify-between font-mono pt-1 border-t border-border-subtle/60">
            <span>Tracking Mode:</span>
            <span className="text-text-primary font-semibold">Commit Signature Hashing</span>
          </div>
        </div>

        {/* Total Applications Compiled Card */}
        <div className="p-4 rounded-lg bg-background-card border border-border-subtle hover:border-border-strong transition-all space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono text-text-secondary uppercase">Compiled Applications</span>
            <FolderCheck className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {totalApplications} <span className="text-xs font-normal text-text-muted">packs</span>
          </div>
          <div className="text-xs text-text-secondary flex justify-between font-mono pt-1 border-t border-border-subtle/60">
            <span>Output Directory:</span>
            <span className="text-sky-400 font-semibold truncate max-w-[150px]">./output/</span>
          </div>
        </div>
      </div>

      {/* Free Tier Quotas Section */}
      <div className="p-5 rounded-xl bg-background-card border border-border-subtle space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div className="space-y-0.5">
            <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              Free Tier Quota Telemetry ($0.00 / Month)
            </h2>
            <p className="text-[11px] text-text-secondary">
              Zero-cost developer endpoints monitored with Token-Bucket rate limiting.
            </p>
          </div>
          <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40 text-emerald-400 text-[11px] font-mono font-bold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Total Spend: $0.00</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuotaRing
            label="Gemini 2.5 Flash-Lite"
            current={quotas.gemini.used}
            total={quotas.gemini.total}
            unit="req/day"
          />
          <QuotaRing
            label="Groq Llama 3.3 70B"
            current={quotas.groq.used}
            total={quotas.groq.total}
            unit="req/day"
          />
          <QuotaRing
            label="Google Custom Search"
            current={quotas.google_cse.used}
            total={quotas.google_cse.total}
            unit="queries/day"
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
