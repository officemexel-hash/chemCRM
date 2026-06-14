"use client";

import { useState } from "react";
import type { Supplier } from "@/types/api";
import { Badge } from "@/components/Widgets";
import { startDiscovery, importDiscoveryUrls } from "@/lib/api";

export function DiscoveryView({ suppliers }: { suppliers: Supplier[] }) {
  const [running, setRunning] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [urlsText, setUrlsText] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState("");

  async function run() { setRunning(true); try { await startDiscovery(); } finally { setRunning(false); } }

  async function importUrls() {
    const urls = urlsText.split("\n").map((l) => l.trim()).filter(Boolean);
    if (!urls.length) return;
    setImporting(true); setImportResult("");
    try { const r = await importDiscoveryUrls(urls); setImportResult(`Imported ${r.imported} URLs`); setUrlsText(""); }
    catch { setImportResult("Import failed"); }
    finally { setImporting(false); }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Discovery Results</h2>
        <div className="flex gap-2">
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => setImportOpen(true)}>Import URLs</button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" type="button" onClick={run} disabled={running}>{running ? "Running..." : "Start Discovery"}</button>
        </div>
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
      {importOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setImportOpen(false)}>
          <div className="w-full max-w-lg rounded-lg border border-slate-200 bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-3 font-semibold text-ink">Import Supplier URLs</h3>
            <label className="grid gap-1 text-sm text-graphite">
              <span>Paste URLs (one per line)</span>
              <textarea className="min-h-32 rounded-md border border-slate-300 bg-white px-3 py-2 text-ink outline-none focus:border-mint" value={urlsText} onChange={(e) => setUrlsText(e.target.value)} placeholder="https://supplier1.example&#10;https://supplier2.example" />
            </label>
            {importResult && <div className="mt-2 rounded-md bg-slate-50 p-2 text-sm text-graphite">{importResult}</div>}
            <div className="mt-3 flex justify-end gap-2">
              <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => setImportOpen(false)}>Cancel</button>
              <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" type="button" onClick={importUrls} disabled={importing}>{importing ? "Importing..." : "Import"}</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
