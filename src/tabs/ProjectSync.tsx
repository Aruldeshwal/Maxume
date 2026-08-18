import React, { useState, useEffect } from "react";
import { 
  FolderSync, 
  CheckCircle2, 
  RefreshCw, 
  ExternalLink, 
  FileText, 
  AlertCircle, 
  FolderOpen, 
  Github, 
  Sparkles, 
  Layers, 
  ChevronDown, 
  ChevronUp, 
  Eye, 
  EyeOff, 
  Trash2, 
  Edit3, 
  Calendar, 
  X, 
  Save 
} from "lucide-react";

interface ProjectItem {
  id?: number;
  directory_name: string;
  directory_path: string;
  last_commit_hash?: string | null;
  summary_markdown?: string | null;
  live_demo_url?: string | null;
  tech_stack?: string | null;
  timeline?: string | null;
  bullets?: string[] | null;
  is_hidden?: number;
  last_synced_at?: string | null;
  status?: string;
}

export const ProjectSync: React.FC = () => {
  // Sync Mode & Inputs
  const [syncMode, setSyncMode] = useState<"github" | "local">("github");
  const [githubUsername, setGithubUsername] = useState<string>("Aruldeshwal");
  const [githubToken, setGithubToken] = useState<string>("");
  const [projectsDir, setProjectsDir] = useState<string>("");

  // Filter & Projects
  const [filterView, setFilterView] = useState<"all" | "active" | "hidden">("all");
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncFeedback, setSyncFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [expandedSummary, setExpandedSummary] = useState<string | null>(null);

  // Edit Modal State
  const [editingProject, setEditingProject] = useState<ProjectItem | null>(null);
  const [editTechStack, setEditTechStack] = useState<string>("");
  const [editTimeline, setEditTimeline] = useState<string>("");
  const [editLiveDemo, setEditLiveDemo] = useState<string>("");
  const [editBulletsText, setEditBulletsText] = useState<string>("");
  const [isSavingEdit, setIsSavingEdit] = useState<boolean>(false);

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
      const res = await fetch("http://127.0.0.1:8000/api/projects?include_hidden=true");
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      }
    } catch {}
  };

  useEffect(() => {
    fetchConfigAndProjects();
  }, []);

  const handleOpenEdit = (proj: ProjectItem) => {
    setEditingProject(proj);
    setEditTechStack(proj.tech_stack || "");
    setEditTimeline(proj.timeline || "");
    setEditLiveDemo(proj.live_demo_url || "");
    const bulletsList = proj.bullets && proj.bullets.length > 0
      ? proj.bullets.join("\n")
      : "";
    setEditBulletsText(bulletsList);
  };

  const handleSaveEdit = async () => {
    if (!editingProject || !editingProject.id) return;
    setIsSavingEdit(true);

    const bulletsArray = editBulletsText
      .split("\n")
      .map((b) => b.trim().replace(/^[-*•]\s*/, ""))
      .filter(Boolean);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${editingProject.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tech_stack: editTechStack.trim(),
          timeline: editTimeline.trim(),
          live_demo_url: editLiveDemo.trim() || null,
          bullets: bulletsArray,
        }),
      });

      if (res.ok) {
        setSyncFeedback({
          type: "success",
          text: `Updated '${editingProject.directory_name}' details successfully!`,
        });
        setEditingProject(null);
        await fetchConfigAndProjects();
      } else {
        const err = await res.json();
        setSyncFeedback({ type: "error", text: err.detail || "Failed to update project." });
      }
    } catch (e: any) {
      setSyncFeedback({ type: "error", text: e.message || "Error saving project." });
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleToggleVisibility = async (proj: ProjectItem) => {
    if (!proj.id) return;
    const newHidden = proj.is_hidden === 1 ? 0 : 1;

    setProjects((prev) =>
      prev.map((p) => (p.id === proj.id ? { ...p, is_hidden: newHidden } : p))
    );

    try {
      await fetch(`http://127.0.0.1:8000/api/projects/${proj.id}/visibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_hidden: newHidden }),
      });
    } catch {
      fetchConfigAndProjects();
    }
  };

  const handleDeleteProject = async (proj: ProjectItem) => {
    if (!proj.id) return;
    if (!window.confirm(`Remove '${proj.directory_name}' from tracked catalog?`)) return;

    setProjects((prev) => prev.filter((p) => p.id !== proj.id));

    try {
      await fetch(`http://127.0.0.1:8000/api/projects/${proj.id}`, {
        method: "DELETE",
      });
    } catch {
      fetchConfigAndProjects();
    }
  };

  const handleGithubSync = async (force: boolean = false) => {
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
          force_resync: force,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const results = data.results || [];
        const count = results.length;
        const unchangedCount = results.filter((r: any) => r.status === "unchanged").length;
        const syncedCount = count - unchangedCount;
        const liveCount = results.filter((r: any) => r.live_demo_url)?.length || 0;

        const summaryText = force
          ? `Force Re-Sync complete! Re-analyzed all ${count} repositories from GitHub.`
          : syncedCount > 0
            ? `Sync complete! Synced ${syncedCount} new/updated repos (${unchangedCount} unchanged, ${liveCount} live demo URLs).`
            : `Sync complete! All ${count} repositories are up to date with zero changes (${liveCount} live demo URLs).`;

        setSyncFeedback({
          type: "success",
          text: summaryText,
        });

        const projRes = await fetch("http://127.0.0.1:8000/api/projects?include_hidden=true");
        if (projRes.ok) {
          const pdata = await projRes.json();
          setProjects(pdata.projects || []);
        }
      } else {
        const err = await res.json();
        setSyncFeedback({
          type: "error",
          text: err.detail || "Failed to sync GitHub repositories.",
        });
      }
    } catch (e: any) {
      setSyncFeedback({
        type: "error",
        text: `Sync error: ${e.message || "Backend unreachable"}`,
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
        const liveCount = data.results?.filter((r: any) => r.live_demo_url)?.length || 0;
        setSyncFeedback({
          type: "success",
          text: `Local sync complete! Indexed ${count} project directories (${liveCount} live demo links extracted).`,
        });

        const projRes = await fetch("http://127.0.0.1:8000/api/projects?include_hidden=true");
        if (projRes.ok) {
          const pdata = await projRes.json();
          setProjects(pdata.projects || []);
        }
      } else {
        const err = await res.json();
        setSyncFeedback({
          type: "error",
          text: err.detail || "Local scan failed.",
        });
      }
    } catch (e: any) {
      setSyncFeedback({
        type: "error",
        text: `Sync error: ${e.message || "Backend unreachable"}`,
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const visibleProjects = projects.filter((p) => {
    if (filterView === "active") return p.is_hidden !== 1;
    if (filterView === "hidden") return p.is_hidden === 1;
    return true;
  });

  const activeCount = projects.filter((p) => p.is_hidden !== 1).length;
  const hiddenCount = projects.filter((p) => p.is_hidden === 1).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <h1 className="text-xl font-bold font-mono tracking-tight text-white flex items-center space-x-2">
            <FolderSync className="w-5 h-5 text-legion-crimson" />
            <span>Project Knowledge Base (SSOT)</span>
          </h1>
          <p className="text-xs text-text-secondary mt-1">
            Single Source of Truth for verified technical stack, accurate timelines, and FAANG-grade resume bullets.
          </p>
        </div>

        {/* Sync Mode Switcher */}
        <div className="flex items-center space-x-1 bg-background-card p-1 rounded-lg border border-border-subtle text-xs font-mono">
          <button
            onClick={() => setSyncMode("github")}
            className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition-colors ${
              syncMode === "github"
                ? "bg-legion-crimson text-white font-bold"
                : "text-text-secondary hover:text-white"
            }`}
          >
            <Github className="w-3.5 h-3.5" />
            <span>GitHub Profile Sync</span>
          </button>
          <button
            onClick={() => setSyncMode("local")}
            className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition-colors ${
              syncMode === "local"
                ? "bg-legion-crimson text-white font-bold"
                : "text-text-secondary hover:text-white"
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Local Folder</span>
          </button>
        </div>
      </div>

      {/* GitHub Profile Sync Controls */}
      {syncMode === "github" ? (
        <div className="p-4 rounded-xl border border-border-subtle bg-background-card space-y-4">
          <div className="flex items-center space-x-2 text-xs font-mono text-text-secondary">
            <Github className="w-4 h-4 text-white" />
            <span className="font-bold text-white uppercase tracking-wider">Sync GitHub Repositories</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-4">
              <label className="block text-[11px] font-mono text-text-secondary uppercase mb-1">
                GitHub Username
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-text-muted font-mono text-xs">@</span>
                <input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  placeholder="Aruldeshwal"
                  className="w-full bg-background-deep border border-border-subtle rounded px-3 py-2 pl-7 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson"
                />
              </div>
            </div>

            <div className="md:col-span-4">
              <label className="block text-[11px] font-mono text-text-secondary uppercase mb-1">
                Personal Access Token (Optional)
              </label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="w-full bg-background-deep border border-border-subtle rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson"
              />
            </div>

            <div className="md:col-span-4 flex items-end space-x-2">
              <button
                onClick={() => handleGithubSync(false)}
                disabled={isSyncing || !githubUsername.trim()}
                className="flex-1 px-3 py-2 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs uppercase tracking-wider transition-all disabled:opacity-50 flex items-center justify-center space-x-1.5 shadow-[0_0_15px_rgba(225,29,72,0.3)]"
                title="Incremental sync: Only updates repositories with new commits (keeps custom in-app edits)"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                <span>{isSyncing ? "Syncing..." : "Sync GitHub"}</span>
              </button>

              <button
                onClick={() => handleGithubSync(true)}
                disabled={isSyncing || !githubUsername.trim()}
                className="px-3 py-2 rounded bg-background-elevated hover:bg-background-hover border border-border-subtle hover:border-legion-crimson/50 text-text-secondary hover:text-white font-mono font-medium text-xs uppercase tracking-wider transition-all disabled:opacity-50 flex items-center justify-center space-x-1"
                title="Force re-sync: Re-analyzes all repositories from GitHub from scratch"
              >
                <Sparkles className="w-3.5 h-3.5 text-legion-crimson" />
                <span>Force Full</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Local Directory Sync Controls */
        <div className="p-4 rounded-xl border border-border-subtle bg-background-card space-y-4">
          <div className="flex items-center space-x-2 text-xs font-mono text-text-secondary">
            <FolderOpen className="w-4 h-4 text-legion-crimson" />
            <span className="font-bold text-white uppercase tracking-wider">Local Projects Folder Scanner</span>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={projectsDir}
                onChange={(e) => setProjectsDir(e.target.value)}
                placeholder="C:\Users\aruld\OneDrive\Desktop\Projects"
                className="w-full bg-background-deep border border-border-subtle rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson"
              />
            </div>
            <button
              onClick={handleLocalSync}
              disabled={isSyncing || !projectsDir.trim()}
              className="px-4 py-2 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs uppercase tracking-wider transition-all disabled:opacity-50 flex items-center justify-center space-x-1.5"
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
      <div className="rounded-xl border border-border-subtle bg-background-card overflow-hidden shadow-lg space-y-0">
        <div className="px-5 py-3.5 border-b border-border-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-legion-crimson" />
            <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
              Tracked Project SSOT Catalog ({projects.length})
            </span>
          </div>

          {/* Visibility Filter Buttons */}
          <div className="flex items-center space-x-1 bg-background-deep p-1 rounded-lg border border-border-subtle text-xs font-mono">
            <button
              onClick={() => setFilterView("all")}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterView === "all" ? "bg-zinc-800 text-white font-bold" : "text-text-muted hover:text-white"
              }`}
            >
              All ({projects.length})
            </button>
            <button
              onClick={() => setFilterView("active")}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterView === "active" ? "bg-emerald-950 text-emerald-400 font-bold border border-emerald-800/40" : "text-text-muted hover:text-white"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => setFilterView("hidden")}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterView === "hidden" ? "bg-rose-950 text-rose-400 font-bold border border-rose-800/40" : "text-text-muted hover:text-white"
              }`}
            >
              Hidden ({hiddenCount})
            </button>
          </div>
        </div>

        {visibleProjects.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-text-muted mx-auto opacity-40" />
            <div className="text-sm font-mono text-text-primary">
              {filterView === "hidden" ? "No hidden projects." : "No projects found."}
            </div>
            <p className="text-xs text-text-secondary max-w-md mx-auto leading-relaxed">
              Sync your GitHub profile above to populate projects into your database.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-background-deep text-text-secondary border-b border-border-subtle text-[11px]">
                <tr>
                  <th className="px-4 py-3">Project / Repository</th>
                  <th className="px-4 py-3">Tech Stack & Timeline</th>
                  <th className="px-4 py-3">Live Demo URL</th>
                  <th className="px-4 py-3">Resume Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle text-text-primary">
                {visibleProjects.map((proj, i) => {
                  const isExpanded = expandedSummary === proj.directory_name;
                  const isHidden = proj.is_hidden === 1;

                  return (
                    <React.Fragment key={i}>
                      <tr className={`transition-colors ${isHidden ? "bg-background-deep/50 opacity-60" : "hover:bg-background-hover"}`}>
                        <td className="px-4 py-3.5 font-semibold text-white">
                          <div className="flex items-center space-x-2">
                            <FileText className={`w-3.5 h-3.5 flex-shrink-0 ${isHidden ? "text-text-muted" : "text-legion-crimson"}`} />
                            <span className={isHidden ? "line-through text-text-muted" : ""}>{proj.directory_name}</span>
                          </div>
                        </td>

                        <td className="px-4 py-3.5">
                          <div className="space-y-1">
                            <div className="text-[11px] text-zinc-300 font-sans line-clamp-1">
                              {proj.tech_stack || "Software Engineering"}
                            </div>
                            <div className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded bg-zinc-800 border border-border-subtle text-[10px] text-amber-400">
                              <Calendar className="w-2.5 h-2.5" />
                              <span>{proj.timeline || "2024"}</span>
                            </div>
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
                              <span className="truncate max-w-[150px]">{proj.live_demo_url}</span>
                              <ExternalLink className="w-3 h-3 flex-shrink-0" />
                            </a>
                          ) : (
                            <span className="text-text-muted text-[11px] italic">No live link</span>
                          )}
                        </td>

                        <td className="px-4 py-3.5">
                          <button
                            onClick={() => handleToggleVisibility(proj)}
                            className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all border ${
                              isHidden
                                ? "bg-rose-950/60 text-rose-400 border-rose-800/60 hover:bg-rose-900"
                                : "bg-emerald-950/60 text-emerald-300 border-emerald-800/60 hover:bg-emerald-900"
                            }`}
                            title={isHidden ? "Click to include in resume" : "Click to hide from resume"}
                          >
                            {isHidden ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            <span>{isHidden ? "Hidden" : "Active"}</span>
                          </button>
                        </td>

                        <td className="px-4 py-3.5 text-right">
                          <div className="inline-flex items-center space-x-1.5">
                            {/* Edit Project Button */}
                            <button
                              onClick={() => handleOpenEdit(proj)}
                              className="flex items-center space-x-1 text-[11px] font-mono text-zinc-300 hover:text-white px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 transition-colors"
                              title="Edit Tech Stack, Timeline & Bullets"
                            >
                              <Edit3 className="w-3 h-3 text-amber-400" />
                              <span>Edit</span>
                            </button>

                            {/* View Bullets Button */}
                            <button
                              onClick={() => setExpandedSummary(isExpanded ? null : proj.directory_name)}
                              className="flex items-center space-x-1 text-[11px] font-mono text-text-secondary hover:text-white px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 transition-colors"
                            >
                              <Sparkles className="w-3 h-3 text-legion-crimson" />
                              <span>{isExpanded ? "Hide" : "Points"}</span>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </button>

                            {/* Delete Button */}
                            <button
                              onClick={() => handleDeleteProject(proj)}
                              className="p-1.5 rounded text-text-muted hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                              title="Delete permanently from catalog"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Expandable Project Highlights Drawer */}
                      {isExpanded && (
                        <tr className="bg-background-deep/80 border-b border-border-subtle">
                          <td colSpan={5} className="p-4">
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

      {/* Edit Project Details Modal */}
      {editingProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-background-card border border-border-subtle rounded-xl shadow-2xl p-5 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div className="flex items-center space-x-2">
                <Edit3 className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold font-mono text-white">
                  Edit Project Details: <span className="text-legion-crimson">{editingProject.directory_name}</span>
                </h3>
              </div>
              <button
                onClick={() => setEditingProject(null)}
                className="p-1 rounded text-text-muted hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              {/* Tech Stack */}
              <div>
                <label className="block text-[11px] font-mono text-text-secondary uppercase mb-1">
                  Tech Stack (Comma-separated for resume header)
                </label>
                <input
                  type="text"
                  value={editTechStack}
                  onChange={(e) => setEditTechStack(e.target.value)}
                  placeholder="e.g. Next.js, React, TypeScript, Tailwind CSS, PostgreSQL"
                  className="w-full bg-background-deep border border-border-subtle rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson"
                />
              </div>

              {/* Timeline & Live Demo Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-text-secondary uppercase mb-1">
                    Timeline (e.g. Oct 2024 – Dec 2024)
                  </label>
                  <input
                    type="text"
                    value={editTimeline}
                    onChange={(e) => setEditTimeline(e.target.value)}
                    placeholder="e.g. Oct 2024 – Nov 2024"
                    className="w-full bg-background-deep border border-border-subtle rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-text-secondary uppercase mb-1">
                    Live Demo URL (For Word clickable hyperlink)
                  </label>
                  <input
                    type="text"
                    value={editLiveDemo}
                    onChange={(e) => setEditLiveDemo(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full bg-background-deep border border-border-subtle rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson"
                  />
                </div>
              </div>

              {/* Engineering Highlights / Bullets */}
              <div>
                <label className="block text-[11px] font-mono text-text-secondary uppercase mb-1">
                  FAANG Engineering Highlights (1 bullet per line)
                </label>
                <textarea
                  value={editBulletsText}
                  onChange={(e) => setEditBulletsText(e.target.value)}
                  rows={5}
                  placeholder="Accomplished [X] as measured by [Y], by doing [Z]..."
                  className="w-full bg-background-deep border border-border-subtle rounded p-3 text-xs font-mono text-white focus:outline-none focus:border-legion-crimson resize-y leading-relaxed"
                />
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border-subtle">
              <button
                onClick={() => setEditingProject(null)}
                className="px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-text-secondary hover:text-white text-xs font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={isSavingEdit}
                className="px-4 py-1.5 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs uppercase tracking-wider transition-all flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{isSavingEdit ? "Saving..." : "Save Project Details"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectSync;
