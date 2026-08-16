import React, { useEffect, useRef } from "react";
import { Terminal, ShieldCheck } from "lucide-react";

export interface LogLine {
  id: string;
  timestamp: string;
  stage: string;
  message: string;
  level?: "info" | "success" | "warning" | "error";
}

interface TerminalLogProps {
  logs: LogLine[];
  isRunning?: boolean;
}

export const TerminalLog: React.FC<TerminalLogProps> = ({ logs, isRunning = false }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const getStageColor = (stage: string) => {
    switch (stage.toLowerCase()) {
      case "research":
        return "text-sky-400";
      case "gemini":
      case "ocr":
        return "text-indigo-400";
      case "ollama":
        return "text-emerald-400";
      case "groq":
        return "text-amber-400";
      case "completed":
        return "text-emerald-400 font-bold";
      default:
        return "text-legion-crimson";
    }
  };

  return (
    <div className="rounded-lg border border-border-subtle bg-background-deep flex flex-col h-64 overflow-hidden font-mono shadow-inner">
      {/* Terminal Header */}
      <div className="h-8 bg-background-card border-b border-border-subtle flex items-center justify-between px-3 text-xs">
        <div className="flex items-center space-x-2">
          <Terminal className="w-3.5 h-3.5 text-legion-crimson" />
          <span className="text-text-secondary text-[11px]">Execution Stream Logs</span>
          {isRunning && (
            <span className="flex items-center space-x-1 text-[10px] text-emerald-400 font-semibold animate-pulse">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
              <span>RUNNING</span>
            </span>
          )}
        </div>
        <div className="flex items-center space-x-1 text-text-muted text-[10px]">
          <ShieldCheck className="w-3 h-3 text-sky-400" />
          <span>Hallucination Guard Active</span>
        </div>
      </div>

      {/* Terminal Stream Body */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5 text-xs text-text-primary" data-testid="terminal-log-content">
        {logs.length === 0 ? (
          <div className="text-text-muted text-xs italic py-4 text-center">
            Ready to execute job optimization pipeline...
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="flex items-start space-x-2 leading-relaxed font-mono">
              <span className="text-text-muted text-[10px] select-none flex-shrink-0">
                [{log.timestamp}]
              </span>
              <span className={`text-[11px] font-semibold flex-shrink-0 ${getStageColor(log.stage)}`}>
                [{log.stage}]
              </span>
              <span className="text-[11px] text-text-primary break-all">
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default TerminalLog;
