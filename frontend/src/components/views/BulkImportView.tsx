"use client";

import React, { useState } from "react";
import type { BulkImportJob, BulkImportItem } from "@/types/api";
import { Badge, Metric } from "@/components/Widgets";
import { uploadBulkImport, processBulkImport, enrichBulkImport, getBulkImportJob, getBulkImportItems } from "@/lib/api";

export function BulkImportView() {
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<BulkImportJob | null>(null);
  const [items, setItems] = useState<BulkImportItem[]>([]);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");

  async function loadItems(jobId: string) { const i = await getBulkImportItems(jobId); setItems(i); }
  async function uploadFile() {
    if (!file) { setError("Choose a CSV/XLSX file first."); return; }
    setError(""); setStatus("Uploading");
    try { const c = await uploadBulkImport(file); setJob(c); await loadItems(c.id); setStatus("Uploaded"); }
    catch { setStatus("Upload failed"); setError("The file could not be uploaded."); }
  }
  async function processJob() {
    if (!job?.id) return; setError(""); setStatus("Processing");
    try { const p = await processBulkImport(job.id); setJob(p); await loadItems(p.id); setStatus("Processed"); }
    catch { setStatus("Processing failed"); setError("The CAS rows could not be processed."); }
  }
  async function enrichJob() {
    if (!job?.id) return; setError(""); setStatus("Enriching");
    try { await enrichBulkImport(job.id); const r = await getBulkImportJob(job.id); setJob(r); await loadItems(job.id); setStatus("Enriched"); }
    catch { setStatus("Enrichment failed"); setError("The imported substances could not be enriched."); }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Bulk CAS Import</h2>
        <span className="text-sm text-graphite">{status}</span>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
          <input className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm" type="file" accept=".csv,.tsv,.xlsx" onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFile(e.target.files?.[0] ?? null)} />
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={uploadFile}>Upload</button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={!job?.id} type="button" onClick={processJob}>Process</button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={!job?.id} type="button" onClick={enrichJob}>Enrich</button>
        </div>
        {error ? <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      </section>
      {job ? <div className="grid gap-3 md:grid-cols-4"><Metric label="Rows" value={job.total_rows ?? 0} /><Metric label="Valid" value={job.valid_rows ?? 0} /><Metric label="Invalid" value={job.invalid_rows ?? 0} /><Metric label="Status" value={job.status ?? "unknown"} /></div> : null}
      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite">
            <tr><th className="px-4 py-3">Row</th><th className="px-4 py-3">CAS raw</th><th className="px-4 py-3">Valid</th><th className="px-4 py-3">Substance</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Error</th></tr>
          </thead>
          <tbody>
            {items.length ? items.map((it) => (
              <tr key={it.id} className="border-t border-slate-100">
                <td className="px-4 py-3">{it.row_number}</td><td className="px-4 py-3 font-medium text-ink">{it.cas_raw}</td><td className="px-4 py-3">{it.cas_valid ? "yes" : "no"}</td>
                <td className="px-4 py-3">{it.substance_id ?? "n/a"}</td><td className="px-4 py-3"><Badge value={it.status} /></td><td className="px-4 py-3 text-graphite">{it.error_message ?? ""}</td>
              </tr>
            )) : <tr><td className="px-4 py-6 text-sm text-graphite" colSpan={6}>Upload a spreadsheet or CSV with CAS numbers to start a batch workflow.</td></tr>}
          </tbody>
        </table>
      </section>
    </section>
  );
}
