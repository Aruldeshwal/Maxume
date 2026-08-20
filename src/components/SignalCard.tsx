import React from "react";
import { ExternalLink, Info, Sparkles, Building2, Newspaper, GitBranch, Target, Compass } from "lucide-react";

export interface SignalItemData {
  signal_type: string;
  headline: string;
  source_url: string;
  source_tier: number;
  published_at?: string | null;
  guard_check_passed?: boolean;
}

export interface SignalCardProps {
  status: "FOUND" | "NO_SIGNALS_FOUND" | "Not Attempted";
  signals?: SignalItemData[];
  companyName: string;
  companySummary?: string;
  industryDomain?: string;
  technicalPriorities?: string[];
}

export const SignalCard: React.FC<SignalCardProps> = ({
  status,
  signals = [],
  companyName,
  companySummary,
  industryDomain,
  technicalPriorities = []
}) => {
  if (status === "Not Attempted") {
    return (
      <div className="p-3 rounded-lg border border-border-subtle bg-background-deep text-text-muted text-xs font-mono">
        Personalization research not run for this application.
      </div>
    );
  }

  if (status === "NO_SIGNALS_FOUND" && !companySummary && technicalPriorities.length === 0) {
    return (
      <div 
        data-testid="signal-none-found"
        className="p-3.5 rounded-lg border border-slate-700/60 bg-slate-900/40 text-slate-300 space-y-2 transition-all shadow-sm"
      >
        <div className="flex items-center space-x-2 text-status-info">
          <Info className="w-4 h-4 text-[#64748B] flex-shrink-0" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
            Informational Notice
          </span>
        </div>
        <p className="text-xs text-[#CBD5E1] leading-relaxed">
          No recent public signal found for <strong className="text-white">{companyName || "this company"}</strong> in the last 90 days. 
          Your cover letter was written on your background and the role alone.
        </p>
      </div>
    );
  }

  const getTierBadge = (tier: number) => {
    switch (tier) {
      case 1:
        return (
          <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-950/80 text-rose-300 border border-rose-800/60">
            <Building2 className="w-2.5 h-2.5" />
            <span>Tier 1: Official Domain</span>
          </span>
        );
      case 3:
        return (
          <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-950/80 text-purple-300 border border-purple-800/60">
            <GitBranch className="w-2.5 h-2.5" />
            <span>Tier 3: GitHub Org</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-blue-950/80 text-blue-300 border border-blue-800/60">
            <Newspaper className="w-2.5 h-2.5" />
            <span>Tier 2: Tech Press</span>
          </span>
        );
    }
  };

  return (
    <div data-testid="signal-found-container" className="space-y-3">
      {/* 1. Header with Guard Verification */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1.5 text-xs font-bold text-white uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5 text-legion-crimson" />
          <span>Company Intelligence Dossier</span>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
          Guard Verified
        </span>
      </div>

      {/* 2. Company Product & Mission Summary */}
      {(companySummary || industryDomain) && (
        <div className="p-3 rounded-lg bg-background-card border border-border-subtle space-y-2">
          <div className="flex items-center justify-between flex-wrap gap-1">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-white">
              <Compass className="w-3.5 h-3.5 text-sky-400" />
              <span>{companyName}</span>
            </div>
            {industryDomain && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950/60 text-sky-300 border border-sky-800/50">
                {industryDomain}
              </span>
            )}
          </div>
          {companySummary && (
            <p className="text-[11px] text-text-secondary leading-relaxed font-sans">
              {companySummary}
            </p>
          )}
        </div>
      )}

      {/* 3. Identified Technical Challenges & Priorities */}
      {technicalPriorities && technicalPriorities.length > 0 && (
        <div className="p-3 rounded-lg bg-background-card border border-border-subtle space-y-2">
          <div className="flex items-center space-x-1.5 text-[11px] font-bold text-zinc-300 font-mono uppercase">
            <Target className="w-3 h-3 text-amber-400" />
            <span>Target Technical Priorities</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {technicalPriorities.map((tp, i) => (
              <span
                key={i}
                className="text-[10px] font-mono px-2 py-1 rounded bg-zinc-900 border border-border-subtle text-text-primary leading-tight"
              >
                ⚡ {tp}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 4. Verified Press / Milestone Signals */}
      {signals.length > 0 && (
        <div className="space-y-2">
          <div className="text-[11px] font-bold text-zinc-400 uppercase font-mono px-1">
            Grounded Company Signals ({signals.length})
          </div>
          {signals.map((signal, idx) => {
            let domain = "";
            try {
              domain = new URL(signal.source_url).hostname.replace("www.", "");
            } catch {
              domain = signal.source_url;
            }

            return (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-background-card border border-border-subtle hover:border-legion-crimson/60 transition-all space-y-1.5 group"
              >
                <div className="flex items-center justify-between">
                  {getTierBadge(signal.source_tier)}
                  {signal.published_at && (
                    <span className="text-[10px] font-mono text-text-muted">
                      {signal.published_at}
                    </span>
                  )}
                </div>

                <p className="text-xs text-text-primary font-medium leading-snug">
                  {signal.headline}
                </p>

                <a
                  href={signal.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center space-x-1 text-[11px] text-text-secondary hover:text-legion-crimson transition-colors font-mono"
                >
                  <span>{domain}</span>
                  <ExternalLink className="w-2.5 h-2.5 opacity-70 group-hover:opacity-100" />
                </a>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SignalCard;
