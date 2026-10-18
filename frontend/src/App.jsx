import React, { useState } from "react";
import { 
  GitBranch, 
  ShieldCheck, 
  AlertTriangle, 
  FileCode, 
  Cpu, 
  Terminal, 
  Loader2, 
  CheckCircle2, 
  Database,
  Wand2,
  X,
  Copy,
  Check,
  History,
  Download
} from "lucide-react";
import DependencyGraph from "./DependencyGraph";

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("findings");
  const [jobData, setJobData] = useState(null);
  const [error, setError] = useState(null);

  // Fix Modal State
  const [activeFix, setActiveFix] = useState(null);
  const [fixLoading, setFixLoading] = useState(false);
  const [fixData, setFixData] = useState(null);
  const [copied, setCopied] = useState(false);

  // Scan History Drawer State
  const [showHistory, setShowHistory] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const startAnalysis = async (e) => {
    e?.preventDefault();
    if (!repoUrl) return;

    setLoading(true);
    setError(null);
    setJobData(null);

    try {
      const response = await fetch(`${API_BASE}/analyses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          repo_url: repoUrl.trim(), 
          branch_name: branch.trim() || "main" 
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const data = await response.json();
      setJobData(data);
    } catch (err) {
      setError(err.message || "Failed to reach backend review pipeline.");
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    setShowHistory(true);
    setHistoryLoading(true);
    try {
      const response = await fetch(`${API_BASE}/analyses`);
      if (response.ok) {
        const data = await response.json();
        setHistoryList(data.history || []);
      }
    } catch (err) {
      console.error("Could not fetch history:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadPastScan = async (jobId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/analyses/${jobId}`);
      if (response.ok) {
        const data = await response.json();
        setJobData(data);
        setRepoUrl(data.repo_url || "");
        setBranch(data.branch_name || "main");
        setShowHistory(false);
      }
    } catch (err) {
      setError("Failed to load historical scan.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFix = async (finding) => {
    setActiveFix(finding);
    setFixLoading(true);
    setFixData(null);
    setCopied(false);

    try {
      const response = await fetch(`${API_BASE}/analyses/fix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rule_id: finding.rule_id,
          message: finding.message || finding.title,
          file_path: finding.file_path,
          line: finding.line,
          code_context: ""
        })
      });

      if (!response.ok) throw new Error("Fix generation failed.");
      const result = await response.json();
      setFixData(result);
    } catch (err) {
      setFixData({
        explanation: "Unable to contact remediation engine.",
        suggested_patch: "# Ensure backend Uvicorn is active on port 8000."
      });
    } finally {
      setFixLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const exportReport = () => {
    if (!jobData) return;
    const report = `# Code Review Audit Report
Repository: ${jobData.repo_url || "Local Audit"}
Branch: ${jobData.branch_name || "main"}
Status: ${jobData.status}
Files Scanned: ${jobData.structural_metrics?.file_count || 0}
Functions Scanned: ${jobData.structural_metrics?.function_count || 0}

## AI Synthesis
${jobData.ai_summary || "No AI summary available."}

## Findings (${jobData.findings?.length || 0})
${jobData.findings?.map(f => `- [\${f.severity}] ${f.rule_id} at${f.file_path}:${f.line} -${f.title || f.message}`).join("\n")}
`;
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-report-${jobData.job_id || "scan"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getSeverityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case "HIGH":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-950/80 text-red-400 border border-red-800">HIGH</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">LOW</span>;
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-[#111827]/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-lg border border-indigo-500/30">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-white">Repository Review Analyst</h1>
              <p className="text-xs text-slate-400">FastAPI • Ruff • Radon AST • Neon PostgreSQL</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={fetchHistory}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition cursor-pointer"
            >
              <History className="w-4 h-4 text-indigo-400" />
              <span>Past Scans</span>
            </button>

            <span className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 rounded-full text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <Database className="w-3.5 h-3.5 inline" />
              <span>Neon Cloud</span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Input Card */}
        <section className="bg-[#111827] rounded-xl border border-slate-800 p-6 shadow-xl">
          <form onSubmit={startAnalysis} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-3">
                <label className="block text-xs uppercase font-semibold text-slate-400 mb-2">
                  GitHub Repository URL
                </label>
                <div className="relative">
                  <Terminal className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="url"
                    required
                    placeholder="https://github.com/octocat/Hello-World.git"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-200 placeholder-slate-500 font-mono transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase font-semibold text-slate-400 mb-2">
                  Branch
                </label>
                <div className="relative">
                  <GitBranch className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-200 placeholder-slate-500 font-mono transition"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900/50 text-white font-medium px-6 py-2.5 rounded-lg shadow-lg shadow-indigo-600/20 transition cursor-pointer disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing Codebase...</span>
                  </>
                ) : (
                  <>
                    <Cpu className="w-4 h-4" />
                    <span>Run Automated Audit</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="mt-4 p-4 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-sm flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </section>

        {/* Results Presentation */}
        {jobData && (
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <span>Audit Results</span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  {jobData.job_id}
                </span>
              </h2>
              <button
                onClick={exportReport}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-medium transition cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 text-indigo-400" />
                <span>Export Report (.md)</span>
              </button>
            </div>

            {/* Scorecard Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
                <p className="text-xs uppercase font-semibold text-slate-400">Total Files</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {jobData.structural_metrics?.file_count || 0}
                </h3>
              </div>

              <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
                <p className="text-xs uppercase font-semibold text-slate-400">Functions Scanned</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {jobData.structural_metrics?.function_count || 0}
                </h3>
              </div>

              <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
                <p className="text-xs uppercase font-semibold text-slate-400">Static Findings</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {jobData.findings?.length || 0}
                </h3>
              </div>

              <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
                <p className="text-xs uppercase font-semibold text-slate-400">Status</p>
                <div className="flex items-center space-x-2 mt-1">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="font-semibold text-emerald-400 uppercase text-sm">
                    {jobData.status || "COMPLETED"}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Review Box */}
            {jobData.ai_summary && (
              <div className="bg-gradient-to-br from-indigo-950/40 via-[#111827] to-[#111827] border border-indigo-500/30 rounded-xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold uppercase text-indigo-300 tracking-wider mb-2 flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  <span>AI Review Synthesis</span>
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {jobData.ai_summary}
                </p>
              </div>
            )}

            {/* Tab Selection */}
            <div className="border-b border-slate-800 flex space-x-8">
              <button
                onClick={() => setActiveTab("findings")}
                className={`pb-3 text-sm font-medium transition cursor-pointer ${
                  activeTab === "findings"
                    ? "border-b-2 border-indigo-500 text-indigo-400"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Static Findings ({jobData.findings?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab("dependencies")}
                className={`pb-3 text-sm font-medium transition cursor-pointer ${
                  activeTab === "dependencies"
                    ? "border-b-2 border-indigo-500 text-indigo-400"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Dependency Map ({jobData.dependencies?.length || 0})
              </button>
            </div>

            {/* Table Findings */}
            {activeTab === "findings" && (
              <div className="bg-[#111827] border border-slate-800 rounded-xl overflow-hidden shadow-lg">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-300">
                    <thead className="bg-slate-900/60 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4">Severity</th>
                        <th className="py-3 px-4">Rule ID</th>
                        <th className="py-3 px-4">File Path</th>
                        <th className="py-3 px-4">Line</th>
                        <th className="py-3 px-4">Description</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 font-mono text-xs">
                      {jobData.findings && jobData.findings.length > 0 ? (
                        jobData.findings.map((f, i) => (
                          <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                            <td className="py-3 px-4 font-sans">{getSeverityBadge(f.severity)}</td>
                            <td className="py-3 px-4 text-indigo-300 font-semibold">{f.rule_id}</td>
                            <td className="py-3 px-4 text-slate-300">{f.file_path}</td>
                            <td className="py-3 px-4 text-amber-300 font-bold">{f.line}</td>
                            <td className="py-3 px-4 text-slate-400 font-sans max-w-xs truncate">{f.title || f.message}</td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={() => handleOpenFix(f)}
                                className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-md bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-xs transition cursor-pointer"
                              >
                                <Wand2 className="w-3.5 h-3.5" />
                                <span>Fix with AI</span>
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="6" className="py-6 text-center text-slate-500 font-sans">
                            No static analysis warnings reported.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Interactive Dependency Graph Canvas */}
            {activeTab === "dependencies" && (
              <div className="space-y-4">
                <div className="flex justify-between items-center text-xs text-slate-400">
                  <span>Interactive Node-Link Architecture Canvas</span>
                  <span>Drag nodes • Scroll to Zoom • Pan Canvas</span>
                </div>
                <DependencyGraph dependencies={jobData.dependencies || []} />
              </div>
            )}
          </section>
        )}
      </main>

      {/* AI Remediation Slide-Over Modal */}
      {activeFix && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-[#111827] border-l border-slate-800 h-full p-6 flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2">
                <Wand2 className="w-5 h-5 text-indigo-400" />
                <h3 className="font-semibold text-white">AI Suggested Remediation</h3>
              </div>
              <button
                onClick={() => setActiveFix(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-6 space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-indigo-400">{activeFix.rule_id}</span>
                  {getSeverityBadge(activeFix.severity)}
                </div>
                <p className="text-sm text-slate-300 font-medium">{activeFix.title || activeFix.message}</p>
                <p className="text-xs text-slate-500 font-mono">{activeFix.file_path}:{activeFix.line}</p>
              </div>

              {fixLoading ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3 text-slate-400">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                  <p className="text-sm">Synthesizing patch with Gemini...</p>
                </div>
              ) : fixData ? (
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-2">Why this matters</h4>
                    <p className="text-sm text-slate-300 bg-slate-900/60 border border-slate-800 p-3 rounded-lg leading-relaxed">
                      {fixData.explanation}
                    </p>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Suggested Patch</h4>
                      <button
                        onClick={() => copyToClipboard(fixData.suggested_patch)}
                        className="inline-flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
                      >
                        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copied ? "Copied" : "Copy Patch"}</span>
                      </button>
                    </div>
                    <pre className="bg-slate-950 border border-slate-800 p-4 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre leading-relaxed">
                      {fixData.suggested_patch}
                    </pre>
                  </div>
                </div>
              ) : null}
            </div>

            <div className="border-t border-slate-800 pt-4 flex justify-end">
              <button
                onClick={() => setActiveFix(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Scan History Slide-Over Drawer */}
      {showHistory && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-[#111827] border-l border-slate-800 h-full p-6 flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2">
                <History className="w-5 h-5 text-indigo-400" />
                <h3 className="font-semibold text-white">Audit History</h3>
              </div>
              <button
                onClick={() => setShowHistory(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-3">
              {historyLoading ? (
                <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-indigo-500 mb-2" />
                  <p className="text-xs">Fetching past audits...</p>
                </div>
              ) : historyList.length > 0 ? (
                historyList.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => loadPastScan(item.job_id)}
                    className="p-4 rounded-lg bg-slate-900 border border-slate-800 hover:border-indigo-500/50 cursor-pointer transition hover:bg-slate-800/60"
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono text-indigo-400 font-semibold">{item.job_id}</span>
                      <span className="text-emerald-400 font-medium uppercase text-[10px] bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
                        {item.status}
                      </span>
                    </div>
                    <p className="text-xs font-mono text-slate-300 truncate">{item.repo_url}</p>
                    <div className="flex justify-between items-center text-[11px] text-slate-500 mt-2 font-sans">
                      <span>Files: {item.total_files} | Findings: {item.total_findings}</span>
                      <span>Branch: {item.branch_name}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-12 text-center text-slate-500 text-xs font-sans">
                  No previous scans recorded.
                </div>
              )}
            </div>

            <div className="border-t border-slate-800 pt-4 flex justify-end">
              <button
                onClick={() => setShowHistory(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}