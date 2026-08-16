import React, { useState, useEffect } from "react";
import { 
  FolderSync, 
  CheckCircle2, 
  RefreshCw, 
  GitBranch, 
  ExternalLink, 
  FileText, 
  AlertCircle, 
  FolderOpen,
  Github,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp
} from "lucide-react";

interface ProjectItem {
  id?: number;
  directory_name: string;
  directory_path: string;
  last_commit_hash?: string | null;
  summary_markdown?: string | null;
  live_demo_url?: string | null;
  last_synced_at?: string | null;
  status?: string;
}

export const ProjectSync: React.FC = () => {
  // Sync Mode & Inputs
  const [syncMode, setSyncMode] = useState<"github" | "local">("github");
  const [githubUsername, setGithubUsername] = useState<string>("Aruldeshwal");
  const [githubToken, setGithubToken] = useState<string>("");
  const [projectsDir, setProjectsDir] = useState<string>("");

  // Projects & Status
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncFeedback, setSyncFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [expandedSummary, setExpandedSummary] = useState<string | null>(null);

  const fetchConfigAndProjects = async () => {
    try {
      const cfgRes = await fetch("http://127.0.0.1:8000/api/config");
      if (cfgRes.ok) {
        const cfg = await cfgRes.json();
        const savedDir = localStorage.getItem("maxume_projects_dir");
        setProjectsDir(savedDir || cfg.projects_dir || "./projects");
      }
    } catch {
      const savedDir = localStorage.getItem("maxume_projects_dir");
      setProjectsDir(savedDir || "./projects");
    }

    const savedUser = localStorage.getItem("maxume_github_username");
    if (savedUser) setGithubUsername(savedUser);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects");
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      }
    } catch {}
  };

  useEffect(() => {
    fetchConfigAndProjects();
  }, []);

  const handleGithubSync = async () => {
    if (!githubUsername.trim()) return;
    setIsSyncing(true);
    setSyncFeedback(null);
    localStorage.setItem("maxume_github_username", githubUsername.trim());

    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects/github-sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: githubUsername.trim(),
          token: githubToken.trim() || undefined,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const count = data.results?.length || 0;
        const liveCount = data.results?.filter((r: any) => r.live_demo_url)?.length || 0;
        setSyncFeedback({
          type: "success",
          text: `Successfully synced @${githubUsername}! Found ${count} public repositories (${liveCount} live demo links extracted).`,
        });

        // Refresh project list
        const projRes = await fetch("http://127.0.0.1:8000/api/projects");
        if (projRes.ok) {
          const pdata = await projRes.json();
          setProjects(pdata.projects || []);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setSyncFeedback({
          type: "error",
          text: `GitHub Sync Failed: ${errData.detail || "Could not fetch repositories."}`,
        });
      }
    } catch (err: any) {
      setSyncFeedback({
        type: "error",
        text: `Error: ${err.message || "Could not connect to Python sidecar."}`,
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleLocalSync = async () => {
    if (!projectsDir.trim()) return;
    setIsSyncing(true);
    setSyncFeedback(null);
    localStorage.setItem("maxume_projects_dir", projectsDir.trim());

    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projects_dir: projectsDir.trim() }),
      });

      if (res.ok) {
        const data = await res.json();
        const count = data.results?.length || 0;
        setSyncFeedback({
          type: "success",
          text: `Scanned local directory "${data.scanned_directory}". Synced ${count} subfolder projects!`,
        });

        const projRes = await fetch("http://127.0.0.1:8000/api/projects");
        if (projRes.ok) {
          const pdata = await projRes.json();
          setProjects(pdata.projects || []);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setSyncFeedback({
          type: "error",
          text: `Local Sync Failed: ${errData.detail || "Check folder path."}`,
        });
      }
    } catch (err: any) {
      setSyncFeedback({
        type: "error",
        text: `Error: ${err.message || "Could not connect to Python sidecar."}`,
      });
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-white flex items-center space-x-2">
            <FolderSync className="w-5 h-5 text-legion-crimson" />
            <span>Projects SSOT Synchronizer</span>
          </h1>
          <p className="text-xs text-text-secondary mt-1">
            Connects your GitHub profile or local directories, auto-detects live demo links, and extracts high-impact resume bullets.
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center space-x-1 p-1 rounded-lg bg-background-card border border-border-subtle">
          <button
            onClick={() => setSyncMode("github")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-mono transition-all ${
              syncMode === "github"
                ? "bg-legion-crimson text-white font-bold shadow-[0_0_10px_rgba(225,29,72,0.4)]"
                : "text-text-secondary hover:text-white"
            }`}
          >
            <Github className="w-3.5 h-3.5" />
            <span>Sync from GitHub</span>
          </button>
          <button
            onClick={() => setSyncMode("local")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-mono transition-all ${
              syncMode === "local"
                ? "bg-legion-crimson text-white font-bold shadow-[0_0_10px_rgba(225,29,72,0.4)]"
                : "text-text-secondary hover:text-white"
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Sync Local Folder</span>
          </button>
        </div>
      </div>

      {/* Sync Control Card */}
      {syncMode === "github" ? (
        <div className="p-5 rounded-xl bg-background-card border border-border-subtle space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Github className="w-5 h-5 text-white" />
              <div>
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  Sync GitHub Public Profile
                </span>
                <p className="text-[11px] text-text-muted">
                  Reads READMEs, parses live demo links (Vercel, Netlify, Render, Cloudflare), and saves summary bullet points.
                </p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/40">
              Zero-Config Public API
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
            <div className="md:col-span-5">
              <label className="text-[11px] font-mono uppercase text-text-secondary">GitHub Username</label>
              <div className="relative mt-1">
                <span className="absolute left-3 top-2 text-xs font-mono text-text-muted">@</span>
                <input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  className="w-full bg-background-deep border border-border-subtle rounded pl-7 pr-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
                  placeholder="Aruldeshwal"
                />
              </div>
            </div>

            <div className="md:col-span-4">
              <label className="text-[11px] font-mono uppercase text-text-secondary">GitHub Token (Optional)</label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                className="w-full mt-1 bg-background-deep border border-border-subtle rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-legion-crimson"
                placeholder="ghp_... (Optional for private repos)"
              />
            </div>

            <div className="md:col-span-3 md:mt-5">
              <button
                onClick={handleGithubSync}
                disabled={isSyncing || !githubUsername.trim()}
                className="w-full py-2 px-4 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs uppercase tracking-wider shadow-[0_0_15px_rgba(225,29,72,0.4)] transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                <span>{isSyncing ? "Fetching Repos..." : "Sync Repositories"}</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-5 rounded-xl bg-background-card border border-border-subtle space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FolderOpen className="w-5 h-5 text-legion-crimson" />
              <div>
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  Scan Local Workstation Projects
                </span>
                <p className="text-[11px] text-text-muted">
                  Scans subfolders on your computer using local Git hashes and local README markdown files.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-mono">
              <GitBranch className="w-3.5 h-3.5" />
              <span>Local Git Enabled</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="text"
              value={projectsDir}
              onChange={(e) => setProjectsDir(e.target.value)}
              className="flex-1 bg-background-deep border border-border-subtle rounded px-3 py-2 text-xs font-mono text-text-primary focus:outline-none focus:border-legion-crimson"
              placeholder="C:/Users/Legion/Documents/projects"
            />
            <button
              onClick={handleLocalSync}
              disabled={isSyncing || !projectsDir.trim()}
              className="px-4 py-2 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs uppercase tracking-wider transition-all disabled:opacity-50 flex items-center space-x-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
              <span>{isSyncing ? "Scanning..." : "Sync Local Folder"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Sync Status Banner */}
      {syncFeedback && (
        <div
          className={`p-3 rounded-lg text-xs font-mono flex items-center space-x-2 border transition-all ${
            syncFeedback.type === "success"
              ? "bg-emerald-950/50 text-emerald-300 border-emerald-800/50 shadow-[0_0_12px_rgba(16,185,129,0.2)]"
              : "bg-rose-950/50 text-rose-300 border-rose-800/50"
          }`}
        >
          {syncFeedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          )}
          <span>{syncFeedback.text}</span>
        </div>
      )}

      {/* Projects Catalog Grid */}
      <div className="rounded-xl border border-border-subtle bg-background-card overflow-hidden shadow-lg">
        <div className="px-5 py-3.5 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-legion-crimson" />
            <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
              Tracked Project SSOT Catalog ({projects.length})
            </span>
          </div>
          <span className="text-[11px] font-mono text-text-muted">
            Stored in maxume_local.db
          </span>
        </div>

        {projects.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-text-muted mx-auto opacity-40" />
            <div className="text-sm font-mono text-text-primary">No projects synchronized yet.</div>
            <p className="text-xs text-text-secondary max-w-md mx-auto leading-relaxed">
              Enter your GitHub username above and click <strong>&quot;Sync Repositories&quot;</strong> to automatically pull your project documentation, live links, and bullet points.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-background-deep text-text-secondary border-b border-border-subtle text-[11px]">
                <tr>
                  <th className="px-4 py-3">Project / Repository</th>
                  <th className="px-4 py-3">Live Demo URL</th>
                  <th className="px-4 py-3">Source Origin</th>
                  <th className="px-4 py-3">Highlights</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle text-text-primary">
                {projects.map((proj, i) => {
                  const isExpanded = expandedSummary === proj.directory_name;
                  return (
                    <React.Fragment key={i}>
                      <tr className="hover:bg-background-hover transition-colors">
                        <td className="px-4 py-3.5 font-semibold text-white">
                          <div className="flex items-center space-x-2">
                            <FileText className="w-3.5 h-3.5 text-legion-crimson flex-shrink-0" />
                            <span>{proj.directory_name}</span>
                          </div>
                        </td>

                        <td className="px-4 py-3.5">
                          {proj.live_demo_url ? (
                            <a
                              href={proj.live_demo_url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 hover:border-emerald-500 transition-colors"
                            >
                              <span className="truncate max-w-[170px]">{proj.live_demo_url}</span>
                              <ExternalLink className="w-3 h-3 flex-shrink-0" />
                            </a>
                          ) : (
                            <span className="text-text-muted text-[11px] italic">No live link</span>
                          )}
                        </td>

                        <td className="px-4 py-3.5 text-text-muted text-[11px]">
                          {proj.directory_path.startsWith("github.com") ? (
                            <span className="flex items-center space-x-1 text-sky-400">
                              <Github className="w-3 h-3" />
                              <span>{proj.directory_path}</span>
                            </span>
                          ) : (
                            <span className="truncate max-w-[150px] inline-block">{proj.directory_path}</span>
                          )}
                        </td>

                        <td className="px-4 py-3.5">
                          <button
                            onClick={() => setExpandedSummary(isExpanded ? null : proj.directory_name)}
                            className="flex items-center space-x-1 text-[11px] font-mono text-text-secondary hover:text-white px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 transition-colors"
                          >
                            <Sparkles className="w-3 h-3 text-legion-crimson" />
                            <span>{isExpanded ? "Hide Points" : "View Points"}</span>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        </td>
                      </tr>

                      {/* Expandable Project Highlights Drawer */}
                      {isExpanded && (
                        <tr className="bg-background-deep/80 border-b border-border-subtle">
                          <td colSpan={4} className="p-4">
                            <div className="p-3.5 rounded-lg bg-background-card border border-border-subtle space-y-2">
                              <div className="text-xs font-bold text-white uppercase flex items-center space-x-1.5">
                                <Sparkles className="w-3.5 h-3.5 text-legion-crimson" />
                                <span>Extracted Resume Bullets for {proj.directory_name}</span>
                              </div>
                              <div className="text-xs text-text-primary whitespace-pre-wrap font-mono leading-relaxed pl-2 border-l-2 border-legion-crimson">
                                {proj.summary_markdown || "No summary content available."}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectSync;
