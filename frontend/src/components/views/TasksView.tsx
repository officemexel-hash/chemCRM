"use client";

import type { ManualTask } from "@/types/api";
import { Badge } from "@/components/Widgets";

export function TasksView({ tasks, onDialog }: { tasks: ManualTask[]; onDialog: (d: string) => void }) {
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
              <p className="text-sm text-graphite">{t.related_object_type ?? "workflow"} · {t.task_type ?? "review"}</p>
            </div>
            <Badge value={t.status ?? "open"} tone={t.status === "completed" ? "ok" : "warn"} />
          </div>
        ))}
      </div>
    </section>
  );
}
