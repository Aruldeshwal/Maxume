import React, { useState } from "react";
import { User, ExternalLink, MessageSquare, Check, Copy } from "lucide-react";

export interface ContactData {
  id?: number;
  employee_name: string;
  employee_tagline?: string;
  profile_url: string;
  referral_message_draft?: string;
  referral_status?: string;
}

interface ContactCardProps {
  contact: ContactData;
  onGenerateReferral?: (contact: ContactData) => void;
  isGenerating?: boolean;
}

export const ContactCard: React.FC<ContactCardProps> = ({
  contact,
  onGenerateReferral,
  isGenerating = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (contact.referral_message_draft) {
      navigator.clipboard.writeText(contact.referral_message_draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="p-3.5 rounded-lg bg-background-card border border-border-subtle hover:border-border-strong transition-all space-y-2.5">
      <div className="flex items-start justify-between space-x-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-zinc-800 border border-border-subtle flex items-center justify-center text-text-secondary flex-shrink-0">
            <User className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white tracking-tight">{contact.employee_name}</div>
            <div className="text-[11px] text-text-secondary leading-snug line-clamp-2">
              {contact.employee_tagline || "Professional on LinkedIn"}
            </div>
          </div>
        </div>

        <a
          href={contact.profile_url}
          target="_blank"
          rel="noreferrer"
          className="p-1 rounded text-text-muted hover:text-white hover:bg-background-hover transition-colors"
          title="Open LinkedIn Profile"
        >
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {contact.referral_message_draft ? (
        <div className="pt-2 border-t border-border-subtle space-y-2">
          <div className="p-2 rounded bg-background-deep text-[11px] font-mono text-text-secondary leading-relaxed border border-border-subtle/60">
            {contact.referral_message_draft}
          </div>
          <button
            onClick={handleCopy}
            className={`w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded text-xs font-medium font-mono transition-all ${
              copied
                ? "bg-emerald-600 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)]"
                : "bg-legion-crimson hover:bg-legion-neon text-white shadow-[0_0_12px_rgba(225,29,72,0.3)]"
            }`}
          >
            {copied ? (
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
