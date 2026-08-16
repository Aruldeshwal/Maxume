import React, { useState, useEffect } from "react";
import { History, Building2, Clock } from "lucide-react";

interface ApplicationRecord {
  id: number;
  company_name: string;
  role_title: string;
  status: string;
  personalization_status: string;
  output_folder_path?: string;
  created_at: string;
}

export const HistoryLogs: React.FC = () => {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/applications")
      .then((res) => res.json())
      .then((data) => {
        setApplications(data.applications || []);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="border-b border-border-subtle pb-4">
        <h1 className="text-xl font-bold font-mono text-white flex items-center space-x-2">
          <History className="w-5 h-5 text-legion-crimson" />
          <span>Application History &amp; SSOT Logs</span>
        </h1>
        <p className="text-xs text-text-secondary mt-1">
          Stateless local history of all compiled resumes, cover letters, and personalization briefs.
        </p>
      </div>

      <div className="rounded-lg border border-border-subtle bg-background-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
          <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
            Logged Applications ({applications.length})
          </span>
          <span className="text-[11px] font-mono text-text-muted">maxume_local.db</span>
        </div>

        {applications.length === 0 ? (
          <div className="p-8 text-center text-xs text-text-muted">
            {isLoading ? "Loading application logs..." : "No job applications compiled yet."}
          </div>
        ) : (
          <div className="divide-y divide-border-subtle">
            {applications.map((app) => (
              <div key={app.id} className="p-4 hover:bg-background-hover transition-colors flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Building2 className="w-4 h-4 text-legion-crimson" />
                    <span className="text-sm font-bold text-white font-mono">{app.company_name}</span>
                    <span className="text-xs text-text-secondary font-mono">— {app.role_title}</span>
                  </div>

                  <div className="flex items-center space-x-4 text-[11px] font-mono text-text-muted">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{app.created_at?.split("T")[0] || app.created_at}</span>
                    </span>
                    <span>Status: <strong className="text-text-primary">{app.status}</strong></span>
                    <span>Personalization: <strong className={app.personalization_status === "Found" ? "text-emerald-400" : "text-sky-400"}>{app.personalization_status}</strong></span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 rounded bg-zinc-800 text-xs font-mono text-text-secondary">
                    {app.output_folder_path ? app.output_folder_path.split("/").pop() : "Compiled"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryLogs;
