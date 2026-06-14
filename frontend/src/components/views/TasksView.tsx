"use client";

import { useState } from "react";
import type { ManualTask } from "@/types/api";
import { Badge } from "@/components/Widgets";
import { patchTask } from "@/lib/api";

export function TasksView({ tasks, onDialog, onUpdated }: { tasks: ManualTask[]; onDialog: (d: string) => void; onUpdated: (t: ManualTask) => void }) {
  const [assignOpen, setAssignOpen] = useState<string | null>(null);
  const [assignName, setAssignName] = useState("");
  const [saving, setSaving] = useState(false);

  async function assign(taskId: string) {
    if (!assignName.trim()) return;
    setSaving(true);
    try { const u = await patchTask(taskId, { assigned_to: assignName.trim() }); onUpdated(u); setAssignOpen(null); setAssignName(""); }
    finally { setSaving(false); }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Manual Tasks</h2>
        <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={() => onDialog("complete-tasks")}>Complete</button>
      </div>
      <div className="grid gap-3">
        {tasks.map((t) => (
          <div key={t.id} className="flex items-center justify-between rounded-md border border-slate-200 bg-white p-4">
            <div>
              <h2 className="font-semibold text-ink">{t.title ?? t.task_type ?? "Manual task"}</h2>
              <p className="text-sm text-graphite">{t.related_object_type ?? "workflow"} · {t.task_type ?? "review"}{t.assigned_to ? ` · assigned to ${t.assigned_to}` : ""}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge value={t.status ?? "open"} tone={t.status === "completed" ? "ok" : "warn"} />
              {t.status !== "completed" && (
                <button className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-ink hover:bg-slate-50" type="button" onClick={() => { setAssignOpen(t.id); setAssignName(t.assigned_to ?? ""); }}>
                  Assign
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {assignOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setAssignOpen(null)}>
          <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-3 font-semibold text-ink">Assign Task</h3>
            <label className="grid gap-1 text-sm text-graphite">
              <span>Assign to</span>
              <input className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={assignName} onChange={(e) => setAssignName(e.target.value)} placeholder="e.g. John from procurement" onKeyDown={(e) => e.key === "Enter" && assign(assignOpen)} />
            </label>
            <div className="mt-3 flex justify-end gap-2">
              <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => setAssignOpen(null)}>Cancel</button>
              <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" type="button" onClick={() => assign(assignOpen)} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
