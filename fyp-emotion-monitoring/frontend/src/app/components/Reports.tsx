import { useState } from "react";
import { Download, FileText, X, CheckSquare, Square, Trash2, Loader2 } from "lucide-react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "./ui/alert-dialog";
import { removeSessions, useSessionStore, type Emotion } from "../utils/emotionEngine";
import { deleteReports } from "../api/client";
import { toast } from "sonner";

const EMOTION_COLORS: { [key in Emotion]: string } = {
  happy: "#c07c20", sad: "#1e5f8a", angry: "#b8312f",
  neutral: "#786c5c"
};

const serif = "'Playfair Display', Georgia, serif";
const sans = "'IBM Plex Sans', system-ui, sans-serif";
const mono = "'IBM Plex Mono', monospace";

export function Reports() {
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [appliedRange, setAppliedRange] = useState<{ start: string; end: string } | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);

  const sessions = useSessionStore();

  // Apply date range filter
  const handleApplyFilter = () => {
    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      toast.error("Start date cannot be after end date");
      return;
    }

    if (!startDate && !endDate) {
      setAppliedRange(null);
      setSelectedIds([]);
      toast.info("Showing all time records");
      return;
    }

    setAppliedRange({ start: startDate, end: endDate });
    setSelectedIds([]);
    toast.success("Filter applied");
  };

  // Reset filter
  const handleResetFilter = () => {
    setStartDate("");
    setEndDate("");
    setAppliedRange(null);
    setSelectedIds([]);
    toast.info("Date filter cleared");
  };

  // Filter sessions based on selected date range
  const filterSessions = () => {
    if (!appliedRange || (!appliedRange.start && !appliedRange.end)) {
      return sessions;
    }

    return sessions.filter((session) => {
      const sessionDate = new Date(session.timestamp);

      if (appliedRange.start) {
        const start = new Date(appliedRange.start);
        start.setHours(0, 0, 0, 0);
        if (sessionDate < start) return false;
      }

      if (appliedRange.end) {
        const end = new Date(appliedRange.end);
        end.setHours(23, 59, 59, 999);
        if (sessionDate > end) return false;
      }

      return true;
    });
  };

  const filteredSessions = filterSessions();

  // Dynamic status display text based on calendar selection
  const getShowingText = () => {
    if (appliedRange?.start && appliedRange?.end) {
      return `${appliedRange.start} to ${appliedRange.end}`;
    }
    if (appliedRange?.start) {
      return `From ${appliedRange.start}`;
    }
    if (appliedRange?.end) {
      return `Until ${appliedRange.end}`;
    }
    return "All Time";
  };

  // Selection Logic
  const isAllSelected = filteredSessions.length > 0 && selectedIds.length === filteredSessions.length;
  const isSomeSelected = selectedIds.length > 0;

  const handleSelectAll = () => {
    if (isAllSelected) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredSessions.map((s) => s.id));
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
        prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id]
    );
  };

  // Delete the selected sessions everywhere: persisted rows go through the
  // backend, then the ids are dropped from the shared store so Dashboard,
  // Analytics, Profile and the analysis pages update immediately.
  const handleDeleteSelected = async () => {
    if (selectedIds.length === 0 || isDeleting) return;
    setIsDeleting(true);
    const ids = [...selectedIds];
    try {
      await deleteReports(ids);
    } catch (err) {
      // Still drop them locally so the UI stays usable offline — but warn
      // that persisted rows may reappear on the next reload.
      toast.warning(
        err instanceof Error
          ? `Server delete failed (${err.message}) — removed locally, may reappear on reload`
          : "Server delete failed — removed locally, may reappear on reload",
      );
    }
    removeSessions(ids);
    setSelectedIds([]);
    setIsDeleting(false);
    toast.success(`Deleted ${ids.length} session${ids.length === 1 ? "" : "s"}`);
  };

  // Target sessions for export: if items are checked, export checked items; otherwise export all filtered
  const targetExportSessions = isSomeSelected
      ? filteredSessions.filter((s) => selectedIds.includes(s.id))
      : filteredSessions;

  // Calculate statistics
  const totalSessions = filteredSessions.length;
  const totalDuration = filteredSessions.reduce((sum, s) => sum + s.duration, 0);
  const avgConfidence = totalSessions > 0
      ? filteredSessions.reduce((sum, s) => sum + s.summary.averageConfidence, 0) / totalSessions
      : 0;

  // Emotion distribution
  const emotionCounts: { [key in Emotion]: number } = {
    happy: 0, sad: 0, angry: 0, neutral: 0
  };

  filteredSessions.forEach((session) => {
    emotionCounts[session.summary.dominantEmotion]++;
  });

  // Generate PDF Report
  const generatePDFReport = () => {
    const doc = new jsPDF();
    doc.setFontSize(20);
    doc.text("Emotion Monitoring Report", 20, 20);
    doc.setFontSize(12);
    doc.text(`Range: ${getShowingText()}`, 20, 30);
    doc.text(`Items Included: ${targetExportSessions.length} sessions`, 20, 37);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 20, 44);

    doc.setFontSize(16);
    doc.text("Summary Statistics", 20, 56);

    autoTable(doc, {
      startY: 61,
      head: [["Metric", "Value"]],
      body: [
        ["Total Sessions Exported", targetExportSessions.length.toString()],
        ["Total Duration", `${Math.round(targetExportSessions.reduce((a, b) => a + b.duration, 0) / 60)} minutes`],
        [
          "Average Confidence",
          `${(
              (targetExportSessions.reduce((a, b) => a + b.summary.averageConfidence, 0) /
                  (targetExportSessions.length || 1)) *
              100
          ).toFixed(1)}%`,
        ],
      ],
    });

    if (targetExportSessions.length > 0) {
      const sessionFinalY = (doc as any).lastAutoTable.finalY || 100;
      doc.setFontSize(16);
      doc.text("Session Details", 20, sessionFinalY + 15);

      autoTable(doc, {
        startY: sessionFinalY + 20,
        head: [["Date", "Type", "Duration", "Dominant Emotion", "Confidence"]],
        body: targetExportSessions.map((s) => [
          new Date(s.timestamp).toLocaleString(), s.type, `${s.duration}s`,
          s.summary.dominantEmotion, `${(s.summary.averageConfidence * 100).toFixed(1)}%`,
        ]),
      });
    }

    doc.save(`emotion-report-${Date.now()}.pdf`);
    toast.success(`PDF report generated (${targetExportSessions.length} sessions)`);
  };

  // Generate CSV Report
  const generateCSVReport = () => {
    let csv = "Session ID,Timestamp,Type,Duration (s),Dominant Emotion,Confidence\n";
    targetExportSessions.forEach((s) => {
      csv += `${s.id},${new Date(s.timestamp).toISOString()},${s.type},${s.duration},${s.summary.dominantEmotion},${s.summary.averageConfidence}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `emotion-data-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${targetExportSessions.length} session(s) to CSV`);
  };

  return (
      <div className="p-8 bg-background min-h-full">
        <div className="max-w-7xl mx-auto">

          {/* Header */}
          <div className="border-b mb-8 pb-6" style={{ borderColor: "var(--border)" }}>
            <div className="flex items-end justify-between gap-4">
              <h1
                  className="font-bold text-foreground leading-tight"
                  style={{ fontFamily: serif, fontSize: "clamp(1.75rem, 3vw, 2.5rem)", letterSpacing: "-0.02em" }}
              >
                Emotion <em style={{ fontStyle: "italic", color: "var(--primary)" }}>Reports</em>
              </h1>
              <div className="flex gap-2.5">
                <Button
                    onClick={generatePDFReport}
                    disabled={totalSessions === 0}
                    className="text-[11px] tracking-[0.12em] uppercase font-normal gap-2"
                    style={{
                      fontFamily: sans, borderRadius: 0, height: "auto", padding: "8px 16px",
                      backgroundColor: "var(--foreground)", color: "var(--background)",
                    }}
                >
                  <Download style={{ width: 13, height: 13 }} />
                  Download PDF {isSomeSelected && `(${selectedIds.length})`}
                </Button>
                <Button
                    variant="outline"
                    onClick={generateCSVReport}
                    disabled={totalSessions === 0}
                    className="text-[11px] tracking-[0.12em] uppercase font-normal gap-2"
                    style={{ fontFamily: sans, borderRadius: 0, height: "auto", padding: "8px 16px", borderColor: "var(--border)" }}
                >
                  <Download style={{ width: 13, height: 13 }} />
                  Export CSV {isSomeSelected && `(${selectedIds.length})`}
                </Button>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-1.5" style={{ fontFamily: sans, fontWeight: 300 }}>
              Generate detailed emotion analysis reports from multimodal data
            </p>
          </div>

          {/* Date Range Component Box */}
          <div
              className="border p-4 mb-8 flex flex-wrap items-center justify-between gap-4"
              style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}
          >
            <div className="flex items-center flex-wrap gap-3">
            <span
                className="text-xs text-muted-foreground uppercase tracking-wider font-normal"
                style={{ fontFamily: sans }}
            >
              Date Range:
            </span>

              <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="[Start Date]"
                  className="w-auto rounded-none border text-xs font-mono bg-background px-3 py-1.5 h-9"
                  style={{ borderColor: "var(--border)", fontFamily: mono }}
              />

              <span className="text-xs text-muted-foreground font-mono" style={{ fontFamily: mono }}>
              to
            </span>

              <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="[End Date]"
                  className="w-auto rounded-none border text-xs font-mono bg-background px-3 py-1.5 h-9"
                  style={{ borderColor: "var(--border)", fontFamily: mono }}
              />

              <Button
                  onClick={handleApplyFilter}
                  variant="outline"
                  className="rounded-none border text-[11px] tracking-[0.14em] uppercase font-normal px-5 h-9"
                  style={{
                    fontFamily: sans,
                    borderColor: "var(--border)",
                    backgroundColor: "transparent",
                  }}
              >
                FILTER
              </Button>

              {appliedRange && (
                  <Button
                      onClick={handleResetFilter}
                      variant="ghost"
                      size="sm"
                      className="rounded-none text-xs text-muted-foreground hover:text-foreground h-9 px-2 gap-1"
                      style={{ fontFamily: sans }}
                  >
                    <X className="size-3.5" />
                    Clear
                  </Button>
              )}
            </div>

            {/* Dynamic Status Display */}
            <div
                className="text-xs font-mono text-muted-foreground tracking-tight"
                style={{ fontFamily: mono }}
            >
              Showing: <span className="text-foreground font-semibold">{getShowingText()}</span>
            </div>
          </div>

          {/* Report Content */}
          {totalSessions === 0 ? (
              <div className="border py-20 text-center" style={{ borderColor: "var(--border)" }}>
                <FileText className="mx-auto mb-4 text-muted-foreground/30" style={{ width: 44, height: 44 }} />
                <h3 className="text-xl font-bold text-foreground mb-2" style={{ fontFamily: serif }}>
                  No data for this period.
                </h3>
                <p className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                  Start a recording session or adjust your date filter to generate reports.
                </p>
              </div>
          ) : (
              <>
                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                  {[
                    { label: "Total Sessions", value: totalSessions, sub: `Range: ${getShowingText()}` },
                    { label: "Total Duration", value: `${Math.round(totalDuration / 60)}m`, sub: "Minutes analyzed" },
                    { label: "Avg Confidence", value: `${(avgConfidence * 100).toFixed(1)}%`, sub: "Model accuracy" },
                  ].map(({ label, value, sub }) => (
                      <div key={label} className="border p-6" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                        <p className="text-[11px] tracking-[0.18em] uppercase text-muted-foreground font-normal mb-2" style={{ fontFamily: sans }}>
                          {label}
                        </p>
                        <div className="text-3xl font-bold text-foreground" style={{ fontFamily: serif }}>
                          {value}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 font-normal" style={{ fontFamily: sans }}>
                          {sub}
                        </p>
                      </div>
                  ))}
                </div>
                
                {/* Session Table */}
                <div className="border mb-8" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                  <div className="px-6 py-4 border-b flex items-center justify-between" style={{ borderColor: "var(--border)" }}>
                <span className="text-[11px] tracking-[0.22em] uppercase text-foreground font-normal" style={{ fontFamily: sans }}>
                  Session History ({filteredSessions.length})
                  {isSomeSelected && (
                      <span className="ml-2 font-mono text-muted-foreground text-[10px]" style={{ fontFamily: mono }}>
                      [{selectedIds.length} Selected]
                    </span>
                  )}
                </span>

                    {/* Select + Delete actions */}
                    <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleSelectAll}
                        className="rounded-none border text-[10px] tracking-[0.14em] uppercase font-normal h-7 px-3 gap-1.5"
                        style={{ fontFamily: sans, borderColor: "var(--border)" }}
                    >
                      {isAllSelected ? (
                          <>
                            <CheckSquare className="size-3 text-primary" /> Deselect All
                          </>
                      ) : (
                          <>
                            <Square className="size-3 text-muted-foreground" /> Select All
                          </>
                      )}
                    </Button>

                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={!isSomeSelected || isDeleting}
                            className="rounded-none border text-[10px] tracking-[0.14em] uppercase font-normal h-7 px-3 gap-1.5 disabled:opacity-40"
                            style={{ fontFamily: sans, borderColor: "var(--border)", color: "#b8312f" }}
                        >
                          {isDeleting ? (
                              <>
                                <Loader2 className="size-3 animate-spin" /> Deleting…
                              </>
                          ) : (
                              <>
                                <Trash2 className="size-3" /> Delete{isSomeSelected ? ` (${selectedIds.length})` : ""}
                              </>
                          )}
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent
                          className="rounded-none border"
                          style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}
                      >
                        <AlertDialogHeader>
                          <AlertDialogTitle style={{ fontFamily: serif }}>
                            Delete {selectedIds.length} session{selectedIds.length === 1 ? "" : "s"}?
                          </AlertDialogTitle>
                          <AlertDialogDescription style={{ fontFamily: sans }}>
                            This permanently removes the selected sessions from the database
                            and every page in the app. This cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel
                              className="rounded-none border"
                              style={{ fontFamily: sans, borderColor: "var(--border)" }}
                          >
                            Cancel
                          </AlertDialogCancel>
                          <AlertDialogAction
                              onClick={handleDeleteSelected}
                              className="rounded-none text-[11px] tracking-[0.12em] uppercase font-normal"
                              style={{ fontFamily: sans, backgroundColor: "#b8312f", color: "#fff" }}
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs" style={{ fontFamily: sans }}>
                      <thead>
                      <tr className="border-b uppercase text-[11px] tracking-wider text-muted-foreground font-normal" style={{ borderColor: "var(--border)" }}>
                        <th className="px-4 py-3.5 w-10 text-center">
                          <input
                              type="checkbox"
                              checked={isAllSelected}
                              onChange={handleSelectAll}
                              className="rounded-none accent-foreground cursor-pointer"
                              title="Select All"
                          />
                        </th>
                        <th className="px-6 py-3.5">Timestamp</th>
                        <th className="px-6 py-3.5">Type</th>
                        <th className="px-6 py-3.5">Duration</th>
                        <th className="px-6 py-3.5">Dominant Emotion</th>
                        <th className="px-6 py-3.5 text-right">Confidence</th>
                      </tr>
                      </thead>
                      <tbody className="divide-y" style={{ borderColor: "var(--border)" }}>
                      {filteredSessions.map((session) => {
                        const dom = session.summary.dominantEmotion;
                        const isSelected = selectedIds.includes(session.id);
                        return (
                            <tr
                                key={session.id}
                                className={`hover:bg-muted/30 transition-colors cursor-pointer ${isSelected ? "bg-muted/40" : ""}`}
                                onClick={() => handleToggleSelect(session.id)}
                            >
                              <td className="px-4 py-3.5 text-center" onClick={(e) => e.stopPropagation()}>
                                <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={() => handleToggleSelect(session.id)}
                                    className="rounded-none accent-foreground cursor-pointer"
                                />
                              </td>
                              <td className="px-6 py-3.5 tabular-nums text-muted-foreground font-normal" style={{ fontFamily: mono }}>
                                {new Date(session.timestamp).toLocaleString()}
                              </td>
                              <td className="px-6 py-3.5 uppercase tracking-wider text-xs font-normal">
                                {session.type}
                              </td>
                              <td className="px-6 py-3.5 tabular-nums font-normal" style={{ fontFamily: mono }}>
                                {session.duration}s
                              </td>
                              <td className="px-6 py-3.5">
                          <span
                              className="inline-block px-2.5 py-1 text-xs font-normal uppercase tracking-wider"
                              style={{
                                backgroundColor: "var(--muted)",
                                color: EMOTION_COLORS[dom],
                              }}
                          >
                            {dom}
                          </span>
                              </td>
                              <td className="px-6 py-3.5 text-right tabular-nums font-normal" style={{ fontFamily: mono }}>
                                {(session.summary.averageConfidence * 100).toFixed(1)}%
                              </td>
                            </tr>
                        );
                      })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
          )}
        </div>
      </div>
  );
}