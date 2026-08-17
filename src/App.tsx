import { useState, useEffect } from "react";
import { 
  LayoutDashboard, 
  FolderSync, 
  Sparkles, 
  History, 
  Settings, 
  ShieldCheck
} from "lucide-react";
import Dashboard from "./tabs/Dashboard";
import ProjectSync from "./tabs/ProjectSync";
import Optimizer from "./tabs/Optimizer";
import HistoryLogs from "./tabs/HistoryLogs";

export default function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "sync" | "optimizer" | "history" | "settings">("dashboard");
  const [ollamaStatus, setOllamaStatus] = useState({ online: false, model: "qwen2.5:7b-instruct", vram: "4.8GB / 5.2GB" });
  const [totalApps, setTotalApps] = useState<number>(0);
  const [quotas] = useState({
    gemini: { used: 0, total: 1000 },
    groq: { used: 0, total: 14400 },
  });

  useEffect(() => {
    // Check sidecar and Ollama status continuously
    const checkOllamaStatus = () => {
      fetch("http://127.0.0.1:8000/api/ollama/status")
        .then((r) => {
          if (!r.ok) throw new Error("Ollama endpoint error");
          return r.json();
        })
        .then((data) => {
          setOllamaStatus((prev) => ({
            ...prev,
            online: !!data.online,
          }));
        })
        .catch(() => {
          setOllamaStatus((prev) => ({
            ...prev,
            online: false,
          }));
        });
    };

    checkOllamaStatus();
    const interval = setInterval(checkOllamaStatus, 3000);

    // Check application count
    fetch("http://127.0.0.1:8000/api/applications")
      .then((r) => r.json())
      .then((data) => {
        setTotalApps(data.applications?.length || 0);
      })
      .catch(() => {});

    return () => clearInterval(interval);
  }, []);

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
            v1.0.0
          </span>
        </div>

        {/* Live Status Bar */}
        <div className="flex items-center space-x-6 text-xs font-mono">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${ollamaStatus.online ? "bg-emerald-400 opacity-75" : "bg-rose-400 opacity-75"}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${ollamaStatus.online ? "bg-emerald-500" : "bg-rose-500"}`}></span>
            </span>
            <span className="text-text-secondary">Ollama Local:</span>
            <span className={ollamaStatus.online ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
              {ollamaStatus.online ? ollamaStatus.model : "Offline"}
            </span>
            <span className="text-text-muted">
              ({ollamaStatus.online ? ollamaStatus.vram : "Service Disconnected"})
            </span>
          </div>

          <div className="h-3 w-px bg-border-subtle"></div>

          <div className="flex items-center space-x-2 text-text-secondary">
            <ShieldCheck className="w-3.5 h-3.5 text-legion-crimson" />
            <span>Local SSOT: <strong className="text-text-primary">Active</strong></span>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 pt-12 h-full">
        {/* Left Navigation Sidebar */}
        <nav className="w-60 border-r border-border-subtle bg-background-card flex flex-col justify-between p-3 flex-shrink-0">
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

          {/* Bottom Settings & Quota Summary */}
          <div className="pt-3 border-t border-border-subtle space-y-2">
            <button
              onClick={() => setActiveTab("optimizer")}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded text-xs font-medium text-text-secondary hover:text-white hover:bg-background-hover transition-all"
            >
              <Settings className="w-4 h-4" />
              <span>[S] Engine Settings</span>
            </button>

            <div className="p-2.5 rounded bg-background-deep border border-border-subtle text-[11px] font-mono space-y-1">
              <div className="text-text-muted flex justify-between">
                <span>Free Quota Spend:</span>
                <span className="text-emerald-400 font-bold">$0.00/mo</span>
              </div>
              <div className="text-[10px] text-text-secondary flex justify-between">
                <span>Gemini OCR:</span>
                <span>1000/1000</span>
              </div>
              <div className="text-[10px] text-text-secondary flex justify-between">
                <span>Groq LPU:</span>
                <span>14.4k/14.4k</span>
              </div>
              <div className="text-[10px] text-text-secondary flex justify-between">
                <span>News & Signals:</span>
                <span className="text-emerald-400 font-bold">Unlimited</span>
              </div>
            </div>
          </div>
        </nav>

        {/* Center Main Workspace with State Persistence */}
        <main className="flex-1 overflow-y-auto p-6 bg-background-deep">
          <div className={activeTab === "dashboard" ? "block" : "hidden"}>
            <Dashboard
              onNavigateToOptimizer={() => setActiveTab("optimizer")}
              totalApplications={totalApps}
              ollamaModel={ollamaStatus.model}
              ollamaVram={ollamaStatus.vram}
              ollamaOnline={ollamaStatus.online}
              quotas={quotas}
            />
          </div>

          <div className={activeTab === "sync" ? "block" : "hidden"}>
            <ProjectSync />
          </div>

          <div className={activeTab === "optimizer" ? "block" : "hidden"}>
            <Optimizer />
          </div>

          <div className={activeTab === "history" ? "block" : "hidden"}>
            <HistoryLogs />
          </div>
        </main>
      </div>
    </div>
  );
}
