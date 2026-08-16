import { useState } from "react";
import { 
  LayoutDashboard, 
  FolderSync, 
  Sparkles, 
  History, 
  Settings, 
  Cpu, 
  Activity,
  ChevronRight,
  ShieldCheck
} from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "sync" | "optimizer" | "history" | "settings">("dashboard");
  const [ollamaStatus] = useState({ online: true, model: "qwen2.5:7b-instruct", vram: "4.8GB / 5.2GB" });

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background-deep text-text-primary">
      {/* Top Header Bar */}
      <header className="fixed top-0 left-0 right-0 h-12 border-b border-border-subtle bg-background-card/90 backdrop-blur flex items-center justify-between px-4 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded bg-legion-crimson flex items-center justify-center font-bold text-white tracking-wider shadow-[0_0_12px_rgba(225,29,72,0.6)]">
            M
          </div>
          <span className="font-mono font-bold tracking-tight text-lg text-white">MAXUME</span>
          <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-text-secondary border border-border-subtle">
            v0.1.0-alpha
          </span>
        </div>

        {/* Live Status Bar */}
        <div className="flex items-center space-x-6 text-xs font-mono">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-text-secondary">Ollama Local:</span>
            <span className="text-emerald-400 font-semibold">{ollamaStatus.model}</span>
            <span className="text-text-muted">({ollamaStatus.vram})</span>
          </div>

          <div className="h-3 w-px bg-border-subtle"></div>

          <div className="flex items-center space-x-2 text-text-secondary">
            <ShieldCheck className="w-3.5 h-3.5 text-legion-crimson" />
            <span>Local SSOT: <strong className="text-text-primary">Active</strong></span>
          </div>
        </div>
      </header>

      {/* Main Container below header */}
      <div className="flex flex-1 pt-12 h-full">
        {/* Left Tactical Navigation Sidebar */}
        <nav className="w-60 border-r border-border-subtle bg-background-card flex flex-col justify-between p-3">
          <div className="space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted px-3 py-2">
              Navigation
            </div>
            
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-medium transition-all ${
                activeTab === "dashboard"
                  ? "bg-legion-crimson text-white shadow-[0_0_15px_rgba(225,29,72,0.4)]"
                  : "text-text-secondary hover:text-white hover:bg-background-hover"
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>[H] Home Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab("sync")}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-medium transition-all ${
                activeTab === "sync"
                  ? "bg-legion-crimson text-white shadow-[0_0_15px_rgba(225,29,72,0.4)]"
                  : "text-text-secondary hover:text-white hover:bg-background-hover"
              }`}
            >
              <FolderSync className="w-4 h-4" />
              <span>[P] Projects Sync</span>
            </button>

            <button
              onClick={() => setActiveTab("optimizer")}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-medium transition-all ${
                activeTab === "optimizer"
                  ? "bg-legion-crimson text-white shadow-[0_0_15px_rgba(225,29,72,0.4)]"
                  : "text-text-secondary hover:text-white hover:bg-background-hover"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>[A] Apply & Optimize</span>
            </button>

            <button
              onClick={() => setActiveTab("history")}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-medium transition-all ${
                activeTab === "history"
                  ? "bg-legion-crimson text-white shadow-[0_0_15px_rgba(225,29,72,0.4)]"
                  : "text-text-secondary hover:text-white hover:bg-background-hover"
              }`}
            >
              <History className="w-4 h-4" />
              <span>[L] History Logs</span>
            </button>
          </div>

          {/* Bottom Settings & Quota summary */}
          <div className="pt-3 border-t border-border-subtle space-y-2">
            <button
              onClick={() => setActiveTab("settings")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded text-xs font-medium transition-all ${
                activeTab === "settings"
                  ? "bg-zinc-800 text-white"
                  : "text-text-secondary hover:text-white hover:bg-background-hover"
              }`}
            >
              <Settings className="w-4 h-4" />
              <span>[S] Engine Settings</span>
            </button>

            <div className="p-2.5 rounded bg-background-deep border border-border-subtle text-[11px] font-mono space-y-1">
              <div className="text-text-muted flex justify-between">
                <span>Free Tier Quotas:</span>
                <span className="text-emerald-400 font-bold">$0.00/mo</span>
              </div>
              <div className="text-[10px] text-text-secondary flex justify-between">
                <span>Gemini (OCR/Rerank):</span>
                <span>1000/1000</span>
              </div>
              <div className="text-[10px] text-text-secondary flex justify-between">
                <span>Groq (Writing LPU):</span>
                <span>14.4k/14.4k</span>
              </div>
              <div className="text-[10px] text-text-secondary flex justify-between">
                <span>Google CSE:</span>
                <span>100/100</span>
              </div>
            </div>
          </div>
        </nav>

        {/* Center Main Display Workspace */}
        <main className="flex-1 overflow-y-auto p-6 bg-background-deep">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-border-subtle pb-4">
              <div>
                <h1 className="text-2xl font-bold font-mono tracking-tight text-white flex items-center space-x-2">
                  <span>Local-First Job Application Assistant</span>
                </h1>
                <p className="text-xs text-text-secondary mt-1">
                  Zero operating cost • Grounded personalization • RTX 3060 VRAM Defense
                </p>
              </div>

              <button
                onClick={() => setActiveTab("optimizer")}
                className="px-4 py-2 rounded bg-legion-crimson hover:bg-legion-neon text-white font-medium text-xs tracking-wider uppercase font-mono shadow-[0_0_20px_rgba(225,29,72,0.5)] transition-all flex items-center space-x-2"
              >
                <span>Start New Job Optimization</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Quick Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-background-card border border-border-subtle">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-text-secondary uppercase">Local LLM Node</span>
                  <Cpu className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="mt-2 text-lg font-bold font-mono text-white">Qwen 2.5 7B</div>
                <div className="text-xs text-text-muted mt-1">Q4_K_M • Flash Attention On</div>
              </div>

              <div className="p-4 rounded-lg bg-background-card border border-border-subtle">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-text-secondary uppercase">Project Watcher SSOT</span>
                  <Activity className="w-4 h-4 text-legion-crimson" />
                </div>
                <div className="mt-2 text-lg font-bold font-mono text-white">Incremental Git Sync</div>
                <div className="text-xs text-text-muted mt-1">Ready to scan /projects</div>
              </div>

              <div className="p-4 rounded-lg bg-background-card border border-border-subtle">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-text-secondary uppercase">Hallucination Guard</span>
                  <ShieldCheck className="w-4 h-4 text-sky-400" />
                </div>
                <div className="mt-2 text-lg font-bold font-mono text-white">3-Stage Grounding</div>
                <div className="text-xs text-text-muted mt-1">Recency + Containment Check</div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
