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
  X,
  Plus,
  ClipboardPaste,
  FolderOpen
} from "lucide-react";
import TerminalLog, { LogLine } from "../components/TerminalLog";
import SignalCard from "../components/SignalCard";
import ContactCard, { ContactData } from "../components/ContactCard";

interface UploadedImage {
  id: string;
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
  const [companyDomain, setCompanyDomain] = useState<string>("");
  const [jdText, setJdText] = useState<string>("");

  // Multiple Screenshots State
  const [uploadedImages, setUploadedImages] = useState<UploadedImage[]>([]);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [pasteNotice, setPasteNotice] = useState<string | null>(null);
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

  // Global Clipboard Paste Listener (Ctrl+V / Command+V)
  useEffect(() => {
    const handleGlobalPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      let foundImage = false;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            foundImage = true;
            processFiles([file], "Pasted from clipboard");
          }
        }
      }

      if (foundImage) {
        setPasteNotice("Screenshot pasted from clipboard!");
        setTimeout(() => setPasteNotice(null), 3000);
      }
    };

    window.addEventListener("paste", handleGlobalPaste);
    return () => window.removeEventListener("paste", handleGlobalPaste);
  }, []);

  const processFiles = (files: File[] | FileList, labelPrefix = "Screenshot") => {
    const newItems: Promise<UploadedImage>[] = [];

    Array.from(files).forEach((file, index) => {
      if (!file.type.startsWith("image/")) return;

      const p = new Promise<UploadedImage>((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const base64 = e.target?.result as string;
          resolve({
            id: Math.random().toString(36).substring(2, 9),
            name: file.name && file.name !== "image.png" ? file.name : `${labelPrefix} #${uploadedImages.length + index + 1}`,
            sizeKb: Math.round(file.size / 1024),
            base64,
            previewUrl: URL.createObjectURL(file),
          });
        };
        reader.readAsDataURL(file);
      });

      newItems.push(p);
    });

    Promise.all(newItems).then((processed) => {
      setUploadedImages((prev) => [...prev, ...processed]);
    });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
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
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeUploadedImage = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setUploadedImages((prev) => prev.filter((img) => img.id !== id));
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const clearAllImages = (e: React.MouseEvent) => {
    e.stopPropagation();
    setUploadedImages([]);
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
    if (!jdText.trim() && uploadedImages.length === 0) {
      alert("Please paste job description text or upload/paste at least one JD screenshot.");
      return;
    }

    setIsOptimizing(true);
    setLogs([]);
    setActiveResult(null);

    const targetCompany = companyName.trim() || "Target Company";
    const targetRole = roleTitle.trim() || "Software Engineer";

    // Initial log steps
    if (uploadedImages.length > 0) {
      const totalSize = uploadedImages.reduce((sum, img) => sum + img.sizeKb, 0);
      addLog("OCR", `Compressing & transcribing ${uploadedImages.length} sequential screenshot(s) (${totalSize} KB total) via Gemini Multimodal OCR...`);
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
          company_domain: companyDomain.trim() || undefined,
          jd_raw_text: jdText.trim() || undefined,
          screenshots_base64: uploadedImages.length > 0 ? uploadedImages.map((img) => img.base64) : undefined,
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

  const handleOpenFolder = async (path: string) => {
    if (!path) return;
    try {
      await fetch("http://127.0.0.1:8000/api/open-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
    } catch {}
  };

  const totalUploadedKb = uploadedImages.reduce((sum, img) => sum + img.sizeKb, 0);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto pb-12">
      {/* Hidden File Input for Multiple Files */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept="image/png,image/jpeg,image/jpg,image/webp"
        multiple
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
            Dual-input JD processing with screenshot paste (Ctrl+V), grounded company personalization, and Word DOCX rebuild.
          </p>
        </div>

        {/* Target Job Metadata */}
        <div className="p-4 rounded-lg bg-background-card border border-border-subtle grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <div>
            <label className="text-[11px] font-mono uppercase text-text-secondary">Target Company</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => {
                setCompanyName(e.target.value);
                if (!companyDomain && e.target.value.trim()) {
                  const autoDom = "@" + e.target.value.trim().toLowerCase().replace(/[^a-z0-9]/g, "") + ".com";
                  setCompanyDomain(autoDom);
                }
              }}
              className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
              placeholder="e.g. Stripe, Meritshot, Google"
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
              onChange={(e) => {
                setCompanyUrl(e.target.value);
                try {
                  const urlStr = e.target.value.trim();
                  if (urlStr) {
                    const parsed = new URL(urlStr.startsWith("http") ? urlStr : `https://${urlStr}`);
                    const host = parsed.hostname.replace(/^www\./, "");
                    if (host) setCompanyDomain(`@${host}`);
                  }
                } catch {}
              }}
              className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
              placeholder="e.g. https://meritshot.com/careers"
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-text-secondary flex items-center justify-between">
              <span>Email Domain</span>
              <span className="text-[9px] text-emerald-400 font-mono">Hunter.io Synth</span>
            </label>
            <input
              type="text"
              value={companyDomain}
              onChange={(e) => setCompanyDomain(e.target.value)}
              className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-emerald-300 font-mono focus:outline-none focus:border-emerald-500 placeholder-zinc-600"
              placeholder="e.g. @meritshot.com"
            />
          </div>
        </div>

        {/* Dual Input Area: Job Description Text & Multi-Screenshot Box */}
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
              placeholder="Paste raw job description text here, or press Ctrl+V to paste screenshots..."
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-semibold text-white uppercase flex items-center space-x-1.5">
                <Upload className="w-3.5 h-3.5 text-sky-400" />
                <span>Upload, Drop, or Paste (Ctrl+V)</span>
              </label>

              {uploadedImages.length > 0 && (
                <button
                  onClick={clearAllImages}
                  className="text-[10px] font-mono text-rose-400 hover:underline"
                >
                  Clear all ({uploadedImages.length})
                </button>
              )}
            </div>

            {uploadedImages.length > 0 ? (
              <div className="rounded-lg border border-border-subtle bg-background-card p-3 space-y-2">
                <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                  <div className="flex items-center space-x-1.5 text-xs font-mono text-emerald-400 font-bold">
                    <Check className="w-3.5 h-3.5" />
                    <span>{uploadedImages.length} Screenshot(s) Attached ({totalUploadedKb} KB)</span>
                  </div>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-800 hover:bg-zinc-700 text-text-primary transition-colors"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add More</span>
                  </button>
                </div>

                {/* Thumbnails Scrollable Strip */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[110px] overflow-y-auto pr-1">
                  {uploadedImages.map((img) => (
                    <div
                      key={img.id}
                      className="relative p-1.5 rounded bg-background-deep border border-border-subtle flex items-center space-x-2 group hover:border-legion-crimson transition-colors"
                    >
                      <img
                        src={img.previewUrl}
                        alt="JD segment"
                        className="w-10 h-10 object-cover rounded border border-border-subtle flex-shrink-0"
                      />
                      <div className="overflow-hidden flex-1">
                        <div className="text-[11px] font-mono text-white truncate">{img.name}</div>
                        <div className="text-[10px] font-mono text-text-muted">{img.sizeKb} KB</div>
                      </div>
                      <button
                        onClick={(e) => removeUploadedImage(img.id, e)}
                        className="p-1 rounded-full bg-zinc-800 hover:bg-rose-950 text-text-muted hover:text-rose-400 transition-colors"
                        title="Remove segment"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>

                <div className="text-[10px] font-mono text-text-muted flex items-center space-x-1">
                  <ClipboardPaste className="w-3 h-3 text-sky-400" />
                  <span>Press <kbd className="px-1 py-0.5 bg-zinc-800 rounded text-[9px] text-white">Ctrl+V</kbd> to paste additional screenshot segments.</span>
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
                <div className="flex items-center space-x-2">
                  <Upload className="w-5 h-5 text-text-muted group-hover:text-legion-crimson transition-colors" />
                  <ClipboardPaste className="w-5 h-5 text-sky-400 opacity-70 group-hover:opacity-100 transition-opacity" />
                </div>
                <span className="mt-2 text-xs font-medium text-text-primary">
                  Click to upload, drop files, or press <strong className="text-white font-mono">Ctrl+V</strong> to paste
                </span>
                <span className="text-[10px] text-text-muted mt-0.5 font-mono">
                  Supports multiple screenshots (top + middle + bottom requirements)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Paste notification toast */}
        {pasteNotice && (
          <div className="p-2.5 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 text-xs font-mono flex items-center space-x-2 shadow-[0_0_12px_rgba(16,185,129,0.3)] animate-bounce">
            <ClipboardPaste className="w-4 h-4 text-emerald-400" />
            <span>{pasteNotice}</span>
          </div>
        )}

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
                <div className="space-y-4 py-4 text-center">
                  <div className="text-emerald-400 font-bold text-sm">Resume DOCX Successfully Compiled!</div>
                  <div className="p-2.5 rounded bg-background-card border border-border-subtle text-left max-w-lg mx-auto space-y-1">
                    <div className="text-[11px] text-text-muted uppercase">Output Location:</div>
                    <div className="text-xs text-white font-bold select-all break-all">{activeResult.resume_path || activeResult.output_folder}</div>
                  </div>
                  <div className="flex items-center justify-center space-x-3 pt-2">
                    <button
                      onClick={() => handleOpenFolder(activeResult.output_folder || activeResult.resume_path)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs shadow-[0_0_12px_rgba(225,29,72,0.4)] transition-all"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                      <span>Open in Windows Explorer</span>
                    </button>
                    {activeResult.resume_path && (
                      <button
                        onClick={() => handleOpenFolder(activeResult.resume_path)}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-text-primary font-mono text-xs transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5 text-sky-400" />
                        <span>Open Word Document</span>
                      </button>
                    )}
                  </div>
                  <div className="text-[11px] text-text-secondary">Single-page guardrail applied (max 4 projects with clickable live demo links).</div>
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

        {/* Personalization & Intelligence Dossier Card */}
        <SignalCard
          status={activeResult?.research_brief?.status || "Not Attempted"}
          signals={activeResult?.research_brief?.signals || []}
          companyName={companyName || activeResult?.research_brief?.company_name || "Target Company"}
          companySummary={activeResult?.research_brief?.company_summary}
          industryDomain={activeResult?.research_brief?.industry_domain}
          technicalPriorities={activeResult?.research_brief?.technical_priorities}
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
              <ContactCard key={idx} contact={c} companyName={companyName || "Target Company"} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Optimizer;
