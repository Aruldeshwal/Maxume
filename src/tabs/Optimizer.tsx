import React, { useState, useEffect, useRef } from "react";
import { 
  Sparkles, 
  Upload, 
  FileText, 
  Check, 
  Copy, 
  Sliders, 
  AlertTriangle,
  UserCheck,
  X
} from "lucide-react";
import TerminalLog, { LogLine } from "../components/TerminalLog";
import SignalCard from "../components/SignalCard";
import ContactCard, { ContactData } from "../components/ContactCard";

interface UploadedImage {
  file: File;
  name: string;
  sizeKb: number;
  base64: string;
  previewUrl: string;
}

export const Optimizer: React.FC = () => {
  // Input states (empty initial values)
  const [companyName, setCompanyName] = useState<string>("");
  const [roleTitle, setRoleTitle] = useState<string>("");
  const [companyUrl, setCompanyUrl] = useState<string>("");
  const [jdText, setJdText] = useState<string>("");

  // Screenshot Upload State
  const [uploadedImage, setUploadedImage] = useState<UploadedImage | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Settings & Guardrails
  const [personalizationEnabled, setPersonalizationEnabled] = useState<boolean>(true);
  const [numCtx, setNumCtx] = useState<number>(2048);
  const [selectedModel, setSelectedModel] = useState<string>("qwen2.5:7b-instruct");
  const [vramWarning, setVramWarning] = useState<string | null>(null);

  // Execution states
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [activeResult, setActiveResult] = useState<any | null>(null);
  const [activeTabSub, setActiveTabSub] = useState<"resume" | "cover_letter" | "email">("cover_letter");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Load models on mount
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/ollama/models?num_ctx=2048&budget_gb=5.2")
      .then((res) => res.json())
      .then((data) => {
        if (data.models && data.models.length > 0) {
          const match = data.models.find((m: any) => m.name === selectedModel);
          if (match && !match.fits_vram) {
            setVramWarning(match.warning);
          }
        }
      })
      .catch(() => {});
  }, [selectedModel]);

  const processFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file (.png, .jpg, .jpeg, .webp)");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage({
        file,
        name: file.name,
        sizeKb: Math.round(file.size / 1024),
        base64,
        previewUrl: URL.createObjectURL(file),
      });
    };
    reader.readAsDataURL(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const removeUploadedImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setUploadedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const addLog = (stage: string, message: string, level: "info" | "success" | "warning" | "error" = "info") => {
    const now = new Date();
    const timeStr = now.toTimeString().split(" ")[0];
    setLogs((prev) => [
      ...prev,
      {
        id: Math.random().toString(36).substring(2, 9),
        timestamp: timeStr,
        stage,
        message,
        level,
      },
    ]);
  };

  const handleRunOptimizer = async () => {
    if (!jdText.trim() && !uploadedImage) {
      alert("Please paste a job description or upload a JD screenshot first.");
      return;
    }

    setIsOptimizing(true);
    setLogs([]);
    setActiveResult(null);

    const targetCompany = companyName.trim() || "Target Company";
    const targetRole = roleTitle.trim() || "Software Engineer";

    // Initial log steps
    if (uploadedImage) {
      addLog("OCR", `Compressing screenshot (${uploadedImage.sizeKb} KB) & running Multimodal Gemini OCR...`);
    }
    addLog("Sidecar", `Initiating optimization pipeline for ${targetCompany} (${targetRole})...`);
    addLog("Local DB", "Performing Semantic Project Similarity Retrieval over /projects SSOT...");
    
    if (personalizationEnabled && companyName.trim()) {
      addLog("Research", `Searching for recent company signals for ${targetCompany} in 90-day window...`);
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: targetCompany,
          role_title: targetRole,
          company_url: companyUrl.trim() || undefined,
          jd_raw_text: jdText.trim() || undefined,
          screenshot_base64: uploadedImage ? uploadedImage.base64 : undefined,
          personalization_enabled: personalizationEnabled,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        
        if (personalizationEnabled) {
          if (data.research_brief?.status === "FOUND") {
            addLog("Research", `${data.research_brief.signals.length} grounded signal(s) verified by hallucination guard`, "success");
          } else {
            addLog("Research", "No qualifying signals in the last 90 days (grounded fallback active)", "info");
          }
        }

        addLog("Ollama", "Swapping Resume Section {{PROJECTS}} & {{SKILLS}} with clickable live hyperlinks...", "info");
        addLog("Groq", "Compiling grounded Cover Letter, Referral Pitch & Email via Llama 3.3 70B...", "info");
        addLog("Google CSE", `Discovered ${data.networking_contacts?.length || 0} employee profiles for networking`, "info");
        addLog("Completed", `Pack successfully compiled to ${data.output_folder || "/output"}`, "success");

        setActiveResult(data);
      } else {
        const errData = await res.json().catch(() => ({}));
        addLog("Error", `Optimization error: ${errData.detail || "Sidecar pipeline error."}`, "error");
      }
    } catch (err: any) {
      addLog("Error", `Pipeline exception: ${err.message}`, "error");
    } finally {
      setIsOptimizing(false);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto pb-12">
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/png,image/jpeg,image/jpg,image/webp"
        className="hidden"
      />

      {/* Left 8 Columns: Input & Configuration & Execution */}
      <div className="lg:col-span-8 space-y-6">
        {/* Top Header */}
        <div className="border-b border-border-subtle pb-4">
          <h1 className="text-xl font-bold font-mono text-white flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-legion-crimson" />
            <span>Application Optimizer</span>
          </h1>
          <p className="text-xs text-text-secondary mt-1">
            Dual-input JD processing with grounded 3-stage company personalization and Word DOCX rebuild.
          </p>
        </div>

        {/* Target Job Metadata */}
        <div className="p-4 rounded-lg bg-background-card border border-border-subtle grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-mono uppercase text-text-secondary">Target Company</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
              placeholder="e.g. Stripe, Google, Acme"
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-text-secondary">Role Title</label>
            <input
              type="text"
              value={roleTitle}
              onChange={(e) => setRoleTitle(e.target.value)}
              className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
              placeholder="e.g. Senior Software Engineer"
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-text-secondary">Company / Careers Link</label>
            <input
              type="text"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
              placeholder="e.g. https://company.com/careers"
            />
          </div>
        </div>

        {/* Dual Input Area: Job Description Text & Screenshot Box */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono font-semibold text-white uppercase flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-legion-crimson" />
              <span>Job Description Text</span>
            </label>
            <textarea
              rows={6}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              className="w-full bg-background-card border border-border-subtle rounded-lg p-3 text-xs text-text-primary font-mono focus:outline-none focus:border-legion-crimson leading-relaxed"
              placeholder="Paste raw job description text here, or drop a screenshot on the right..."
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono font-semibold text-white uppercase flex items-center space-x-1.5">
              <Upload className="w-3.5 h-3.5 text-sky-400" />
              <span>Or Upload / Drop Screenshot JD</span>
            </label>

            {uploadedImage ? (
              <div className="h-[148px] rounded-lg border border-emerald-800/80 bg-emerald-950/20 p-3 flex flex-col justify-between relative group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <img
                      src={uploadedImage.previewUrl}
                      alt="JD Preview"
                      className="w-12 h-12 object-cover rounded border border-emerald-700/60"
                    />
                    <div>
                      <div className="text-xs font-bold text-white truncate max-w-[150px]">
                        {uploadedImage.name}
                      </div>
                      <div className="text-[10px] font-mono text-emerald-400">
                        {uploadedImage.sizeKb} KB • Screenshot Ready
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={removeUploadedImage}
                    className="p-1 rounded-full bg-zinc-800 hover:bg-rose-900 text-text-muted hover:text-white transition-colors"
                    title="Remove Screenshot"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="text-[10px] font-mono text-text-secondary flex items-center space-x-1">
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span>Multimodal OCR will extract JD requirements automatically.</span>
                </div>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`h-[148px] rounded-lg border-2 border-dashed transition-all flex flex-col items-center justify-center p-4 text-center cursor-pointer group ${
                  isDragging
                    ? "border-legion-crimson bg-legion-crimson/10 scale-[1.01]"
                    : "border-border-subtle bg-background-card hover:border-legion-crimson/60"
                }`}
              >
                <Upload className="w-6 h-6 text-text-muted group-hover:text-legion-crimson transition-colors" />
                <span className="mt-2 text-xs font-medium text-text-primary">
                  Click to upload or drag &amp; drop JD screenshot
                </span>
                <span className="text-[10px] text-text-muted mt-0.5 font-mono">
                  PNG, JPG, WEBP • Auto-compressed via Pillow (ADR 1)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Advanced Parameter Controls & Guardrails */}
        <div className="p-4 rounded-lg bg-background-card border border-border-subtle space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-bold font-mono text-white uppercase">
              <Sliders className="w-4 h-4 text-legion-crimson" />
              <span>Engine Parameters &amp; Guardrails</span>
            </div>

            {/* Personalization Toggle */}
            <label className="flex items-center space-x-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={personalizationEnabled}
                onChange={(e) => setPersonalizationEnabled(e.target.checked)}
                className="rounded border-border-subtle text-legion-crimson focus:ring-0 bg-background-deep"
              />
              <span className="text-xs font-mono text-text-primary">
                Company Signal Research: <strong className={personalizationEnabled ? "text-emerald-400" : "text-text-muted"}>{personalizationEnabled ? "ON" : "OFF"}</strong>
              </span>
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-border-subtle/60">
            <div>
              <div className="flex justify-between text-xs font-mono text-text-secondary mb-1">
                <span>Ollama Model:</span>
                <span className="text-white font-semibold">{selectedModel}</span>
              </div>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-background-deep border border-border-subtle rounded px-2.5 py-1.5 text-xs font-mono text-text-primary focus:outline-none focus:border-legion-crimson"
              >
                <option value="qwen2.5:7b-instruct">qwen2.5:7b-instruct (Q4_K_M - Recommended 5.1GB VRAM)</option>
                <option value="llama3.1:8b">llama3.1:8b (5.4GB VRAM)</option>
                <option value="mistral:7b">mistral:7b (4.9GB VRAM)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono text-text-secondary mb-1">
                <span>Context Window Limit:</span>
                <span className="text-emerald-400 font-semibold">{numCtx} tokens</span>
              </div>
              <input
                type="range"
                min="1024"
                max="4096"
                step="512"
                value={numCtx}
                onChange={(e) => setNumCtx(parseInt(e.target.value))}
                className="w-full accent-legion-crimson bg-background-deep rounded"
              />
            </div>
          </div>

          {vramWarning && (
            <div className="p-2.5 rounded bg-amber-950/40 border border-amber-800/60 text-amber-200 text-xs font-mono flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>{vramWarning}</span>
            </div>
          )}
        </div>

        {/* Primary Action Button */}
        <button
          onClick={handleRunOptimizer}
          disabled={isOptimizing}
          className="w-full py-3.5 rounded-lg bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-sm tracking-wider uppercase shadow-[0_0_25px_rgba(225,29,72,0.6)] transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <Sparkles className={`w-4 h-4 ${isOptimizing ? "animate-spin" : ""}`} />
          <span>{isOptimizing ? "Optimizing Asset Pack..." : "Compile & Optimize Resume Pack"}</span>
        </button>

        {/* Live Execution Stream Logger */}
        <TerminalLog logs={logs} isRunning={isOptimizing} />

        {/* Generated Output Viewer */}
        {activeResult && (
          <div className="p-4 rounded-lg bg-background-card border border-border-subtle space-y-3">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTabSub("cover_letter")}
                  className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                    activeTabSub === "cover_letter" ? "bg-legion-crimson text-white font-bold" : "text-text-secondary hover:text-white"
                  }`}
                >
                  Cover Letter
                </button>
                <button
                  onClick={() => setActiveTabSub("email")}
                  className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                    activeTabSub === "email" ? "bg-legion-crimson text-white font-bold" : "text-text-secondary hover:text-white"
                  }`}
                >
                  Outreach Email
                </button>
                <button
                  onClick={() => setActiveTabSub("resume")}
                  className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                    activeTabSub === "resume" ? "bg-legion-crimson text-white font-bold" : "text-text-secondary hover:text-white"
                  }`}
                >
                  Compiled Resume (.docx)
                </button>
              </div>

              <button
                onClick={() => copyToClipboard(
                  activeTabSub === "cover_letter" ? activeResult.cover_letter : activeResult.outreach_email,
                  activeTabSub
                )}
                className="flex items-center space-x-1 text-xs font-mono px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-text-primary"
              >
                {copiedKey === activeTabSub ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey === activeTabSub ? "Copied!" : "Copy Text"}</span>
              </button>
            </div>

            <div className="p-3 rounded bg-background-deep font-mono text-xs text-text-primary leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto">
              {activeTabSub === "cover_letter" && activeResult.cover_letter}
              {activeTabSub === "email" && activeResult.outreach_email}
              {activeTabSub === "resume" && (
                <div className="space-y-2 py-4 text-center">
                  <div className="text-emerald-400 font-bold">Resume DOCX Successfully Compiled!</div>
                  <div className="text-[11px] text-text-muted truncate">{activeResult.resume_path}</div>
                  <div className="text-xs text-text-secondary">Single-page guardrail applied (max 4 projects, clickable live hyperlinks).</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right 4 Columns: Tab D Networking & Personalization Drawer */}
      <div className="lg:col-span-4 space-y-4">
        <div className="p-3 rounded-lg bg-background-card border border-border-subtle">
          <div className="text-xs font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-1.5">
            <UserCheck className="w-4 h-4 text-legion-crimson" />
            <span>Networking &amp; Personalization Hub</span>
          </div>
        </div>

        {/* Personalization Signal Card */}
        <SignalCard
          status={activeResult?.research_brief?.status || "Not Attempted"}
          signals={activeResult?.research_brief?.signals || []}
          companyName={companyName || "Target Company"}
        />

        {/* Networking Contacts Drawer */}
        <div className="space-y-3">
          <div className="text-xs font-bold font-mono text-white uppercase tracking-wider px-1">
            Targeted Referral Contacts ({activeResult?.networking_contacts?.length || 0})
          </div>

          {!activeResult || !activeResult.networking_contacts || activeResult.networking_contacts.length === 0 ? (
            <div className="p-6 rounded-lg bg-background-card border border-border-subtle text-center text-xs text-text-muted">
              Run job optimization to discover verified LinkedIn employee contacts and drafts.
            </div>
          ) : (
            activeResult.networking_contacts.map((c: ContactData, idx: number) => (
              <ContactCard key={idx} contact={c} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Optimizer;
