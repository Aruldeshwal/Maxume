import React, { useState } from "react";
import { User, ExternalLink, MessageSquare, Check, Copy, Mail, Search, Github, Send, ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";

export interface ContactData {
  id?: number;
  employee_name: string;
  employee_tagline?: string;
  profile_url: string;
  company_domain?: string;
  mx_status?: boolean;
  mx_provider?: string;
  email_primary?: string;
  email_alternatives?: string[] | string;
  google_dork_url?: string;
  github_search_url?: string;
  twitter_search_url?: string;
  referral_message_draft?: string;
  referral_status?: string;
}

interface ContactCardProps {
  contact: ContactData;
  companyName?: string;
  onGenerateReferral?: (contact: ContactData) => void;
  isGenerating?: boolean;
}

export const ContactCard: React.FC<ContactCardProps> = ({
  contact,
  companyName = "Company",
  onGenerateReferral,
  isGenerating = false,
}) => {
  const [copiedPitch, setCopiedPitch] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [showPatterns, setShowPatterns] = useState(false);

  const handleCopyPitch = () => {
    if (contact.referral_message_draft) {
      navigator.clipboard.writeText(contact.referral_message_draft);
      setCopiedPitch(true);
      setTimeout(() => setCopiedPitch(false), 2000);
    }
  };

  const handleCopyEmail = (emailStr: string) => {
    navigator.clipboard.writeText(emailStr);
    setCopiedEmail(emailStr);
    setTimeout(() => setCopiedEmail(null), 2000);
  };

  const alternatives: string[] = Array.isArray(contact.email_alternatives)
    ? contact.email_alternatives
    : typeof contact.email_alternatives === "string" && contact.email_alternatives.startsWith("[")
    ? JSON.parse(contact.email_alternatives)
    : [];

  const mailtoUrl = contact.email_primary
    ? `mailto:${contact.email_primary}?subject=${encodeURIComponent(
        `Referral Inquiry: Software Engineering at ${companyName} - Arul Deshwal`
      )}&body=${encodeURIComponent(
        contact.referral_message_draft ||
          `Hi ${contact.employee_name},\n\nI hope you're having a great week! I came across your profile and noticed your engineering work at ${companyName}...`
      )}`
    : undefined;

  return (
    <div className="p-3.5 rounded-lg bg-background-card border border-border-subtle hover:border-border-strong transition-all space-y-3">
      {/* 1. Header: Name, Tagline, Profile Link & MX Badge */}
      <div className="flex items-start justify-between space-x-3">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="w-8 h-8 rounded-full bg-zinc-800 border border-border-subtle flex items-center justify-center text-text-secondary flex-shrink-0">
            <User className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="min-w-0">
            <div className="text-xs font-bold text-white tracking-tight truncate">{contact.employee_name}</div>
            <div className="text-[11px] text-text-secondary leading-snug line-clamp-2">
              {contact.employee_tagline || `Professional at ${companyName}`}
            </div>
          </div>
        </div>

        <a
          href={contact.profile_url}
          target="_blank"
          rel="noreferrer"
          className="p-1.5 rounded bg-zinc-800/80 hover:bg-zinc-700 text-blue-400 hover:text-blue-300 transition-colors flex-shrink-0 flex items-center space-x-1"
          title="Open Verified LinkedIn Profile"
        >
          <span className="text-[10px] font-mono font-semibold">in</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* 2. Live DNS Mail Server Verification Badge */}
      {contact.mx_provider && (
        <div className="flex items-center justify-between px-2 py-1 rounded bg-emerald-950/40 border border-emerald-800/40 text-[10px] font-mono text-emerald-400">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>DNS MX Active: <strong>{contact.mx_provider}</strong></span>
          </div>
          <span className="text-[9px] text-emerald-300/80">Deliverable Server</span>
        </div>
      )}

      {/* 3. Primary Predicted Corporate Email */}
      {contact.email_primary && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between p-2 rounded bg-background-deep border border-border-subtle/80 text-[11px] font-mono">
            <div className="flex items-center space-x-2 min-w-0 text-text-primary">
              <Mail className="w-3.5 h-3.5 text-legion-crimson flex-shrink-0" />
              <span className="truncate text-zinc-300 select-all font-semibold">{contact.email_primary}</span>
            </div>

            <div className="flex items-center space-x-1.5 flex-shrink-0 ml-2">
              <button
                onClick={() => handleCopyEmail(contact.email_primary!)}
                className={`p-1 rounded text-xs transition-all ${
                  copiedEmail === contact.email_primary
                    ? "bg-emerald-600 text-white"
                    : "bg-zinc-800 hover:bg-zinc-700 text-text-secondary hover:text-white"
                }`}
                title="Copy Email Address"
              >
                {copiedEmail === contact.email_primary ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              </button>

              {mailtoUrl && (
                <a
                  href={mailtoUrl}
                  className="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-text-secondary hover:text-emerald-400 transition-colors"
                  title="Compose Email (1-Click Mailto)"
                >
                  <Send className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>

          {/* Expandable Alternative Hunter.io Patterns */}
          {alternatives.length > 0 && (
            <div>
              <button
                onClick={() => setShowPatterns(!showPatterns)}
                className="flex items-center space-x-1 text-[10px] font-mono text-zinc-400 hover:text-zinc-200 transition-colors px-1"
              >
                {showPatterns ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                <span>{showPatterns ? "Hide Alternative Formats" : `View ${alternatives.length} Alternative Email Patterns`}</span>
              </button>

              {showPatterns && (
                <div className="mt-1.5 space-y-1 pl-2 border-l border-border-subtle">
                  {alternatives.map((alt, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between py-0.5 text-[10px] font-mono text-zinc-400"
                    >
                      <span className="truncate select-all">{alt}</span>
                      <button
                        onClick={() => handleCopyEmail(alt)}
                        className="p-0.5 hover:text-white transition-colors"
                        title="Copy Alternative Email"
                      >
                        {copiedEmail === alt ? (
                          <Check className="w-2.5 h-2.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-2.5 h-2.5" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 4. Multi-Channel Contact & Deep Search Toolbar */}
      <div className="flex items-center justify-between pt-1 border-t border-border-subtle/60 text-[10px] text-text-muted font-mono">
        <span className="text-zinc-500">Public Contact Checks:</span>
        <div className="flex items-center space-x-2">
          {contact.google_dork_url && (
            <a
              href={contact.google_dork_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 hover:text-amber-400 transition-colors"
              title="Google Dork: Verify public email / resume snippets"
            >
              <Search className="w-3 h-3" />
              <span>Dork</span>
            </a>
          )}

          {contact.github_search_url && (
            <a
              href={contact.github_search_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 hover:text-purple-400 transition-colors"
              title="GitHub: Search developer profile & commit emails"
            >
              <Github className="w-3 h-3" />
              <span>GitHub</span>
            </a>
          )}

          {contact.twitter_search_url && (
            <a
              href={contact.twitter_search_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 hover:text-sky-400 transition-colors"
              title="Twitter / X: Search direct handle / DM"
            >
              <span className="font-bold">𝕏</span>
              <span>Search</span>
            </a>
          )}
        </div>
      </div>

      {/* 5. Referral Pitch Generator & Copy */}
      {contact.referral_message_draft ? (
        <div className="pt-2 border-t border-border-subtle space-y-2">
          <div className="p-2 rounded bg-background-deep text-[11px] font-mono text-text-secondary leading-relaxed border border-border-subtle/60 max-h-24 overflow-y-auto">
            {contact.referral_message_draft}
          </div>
          <button
            onClick={handleCopyPitch}
            className={`w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded text-xs font-medium font-mono transition-all ${
              copiedPitch
                ? "bg-emerald-600 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)]"
                : "bg-legion-crimson hover:bg-legion-neon text-white shadow-[0_0_12px_rgba(225,29,72,0.3)]"
            }`}
          >
            {copiedPitch ? (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>Referral Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy Referral Pitch</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <button
          onClick={() => onGenerateReferral && onGenerateReferral(contact)}
          disabled={isGenerating}
          className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded bg-zinc-800 hover:bg-zinc-700 text-text-primary text-xs font-medium transition-all disabled:opacity-50"
        >
          <MessageSquare className="w-3.5 h-3.5 text-legion-crimson" />
          <span>{isGenerating ? "Drafting..." : "Draft Referral Pitch"}</span>
        </button>
      )}
    </div>
  );
};

export default ContactCard;
