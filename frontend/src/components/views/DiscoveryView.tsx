"use client";

import { useState } from "react";
import type { Supplier } from "@/types/api";
import { Badge } from "@/components/Widgets";
import { startDiscovery } from "@/lib/api";

export function DiscoveryView({ suppliers }: { suppliers: Supplier[] }) {
  const [running, setRunning] = useState(false);
  async function run() { setRunning(true); try { await startDiscovery(); } finally { setRunning(false); } }
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Discovery Results</h2>
        <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" type="button" onClick={run} disabled={running}>{running ? "Running..." : "Start Discovery"}</button>
      </div>
      <div className="grid gap-3">
        {suppliers.map((s) => (
          <div key={s.id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-ink">{s.name}</h2>
                <p className="text-sm text-graphite">{s.website ?? "No website"} · {s.country ?? "unknown country"}</p>
              </div>
              <div className="flex gap-2">
                <Badge value={s.company_type ?? "UNKNOWN"} />
                <Badge value={`risk ${s.risk_score}`} tone={Number(s.risk_score) > 30 ? "warn" : "ok"} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
