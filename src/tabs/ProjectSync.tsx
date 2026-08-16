import React, { useState, useEffect } from "react";
import { FolderSync, CheckCircle2, RefreshCw, GitBranch, ExternalLink, FileText, AlertCircle } from "lucide-react";

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
  const [projectsDir, setProjectsDir] = useState<string>("./projects");
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncResult, setLastSyncResult] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects");
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      }
    } catch {
      // Offline fallback
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleSyncNow = async () => {
    setIsSyncing(true);
    setLastSyncResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projects_dir: projectsDir })
      });
      if (res.ok) {
        const data = await res.json();
        setLastSyncResult(`Sync complete! Scanned ${data.results?.length || 0} subdirectories.`);
        await fetchProjects();
      } else {
        setLastSyncResult("Sync failed. Check directory path.");
      }
    } catch (err: any) {
      setLastSyncResult(`Error: ${err.message || "Could not reach sidecar."}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-white flex items-center space-x-2">
            <FolderSync className="w-5 h-5 text-legion-crimson" />
            <span>Projects SSOT Synchronizer</span>
          </h1>
          <p className="text-xs text-text-secondary mt-1">
            Scans engineering project logs, extracts live deployment URLs, and detects incremental Git commits.
          </p>
        </div>

        <button
          onClick={handleSyncNow}
          disabled={isSyncing}
          className="px-4 py-2 rounded bg-legion-crimson hover:bg-legion-neon text-white font-mono font-bold text-xs uppercase tracking-wider shadow-[0_0_15px_rgba(225,29,72,0.4)] transition-all flex items-center space-x-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
          <span>{isSyncing ? "Scanning /projects..." : "Force Sync SSOT"}</span>
        </button>
      </div>

      {/* Directory Binding Bar */}
      <div className="p-4 rounded-lg bg-background-card border border-border-subtle space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
            Workspace Mapping
          </span>
          <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-mono">
            <GitBranch className="w-3.5 h-3.5 text-emerald-400" />
            <span>Git Tracking Active</span>
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
            onClick={handleSyncNow}
            className="px-3 py-2 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-text-primary transition-all border border-border-subtle"
          >
            Update Path
          </button>
        </div>

        {lastSyncResult && (
          <div className="text-xs font-mono text-emerald-400 flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{lastSyncResult}</span>
          </div>
        )}
      </div>

      {/* Project SSOT Table Grid */}
      <div className="rounded-lg border border-border-subtle bg-background-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
          <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
            Tracked Projects Catalog ({projects.length})
          </span>
          <span className="text-[11px] font-mono text-text-muted">
            SQLite Database SSOT
          </span>
        </div>

        {projects.length === 0 ? (
          <div className="p-8 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-text-muted mx-auto opacity-50" />
            <div className="text-xs text-text-secondary">No project folders synchronized yet.</div>
            <div className="text-[11px] text-text-muted">
              Click &quot;Force Sync SSOT&quot; above to scan your /projects directory.
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-background-deep text-text-secondary border-b border-border-subtle text-[11px]">
                <tr>
                  <th className="px-4 py-2.5">Directory Name</th>
                  <th className="px-4 py-2.5">Commit Hash</th>
                  <th className="px-4 py-2.5">Live Demo URL</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle text-text-primary">
                {projects.map((proj, i) => (
                  <tr key={i} className="hover:bg-background-hover transition-colors">
                    <td className="px-4 py-3 font-semibold text-white flex items-center space-x-2">
                      <FileText className="w-3.5 h-3.5 text-legion-crimson" />
                      <span>{proj.directory_name}</span>
                    </td>
                    <td className="px-4 py-3 text-text-muted text-[11px]">
                      {proj.last_commit_hash ? proj.last_commit_hash.slice(0, 7) : "Untracked"}
                    </td>
                    <td className="px-4 py-3">
                      {proj.live_demo_url ? (
                        <a
                          href={proj.live_demo_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-400 hover:underline flex items-center space-x-1"
                        >
                          <span className="truncate max-w-[160px]">{proj.live_demo_url}</span>
                          <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                        </a>
                      ) : (
                        <span className="text-text-muted text-[11px]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/40">
                        Up to Date
                      </span>
                    </td>
                    <td className="px-4 py-3 text-text-secondary text-[11px]">
                      {proj.summary_markdown ? `${proj.directory_name}_summary.md` : "Generated"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectSync;
