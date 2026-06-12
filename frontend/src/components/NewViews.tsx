"use client";

import { useState } from "react";
import {
  uploadBulkImport, processBulkImport, enrichBulkImport, getBulkImportJob, getBulkImportItems,
  lookupHsCode, getDutyRate, getResponsibilityMatrix, getLegalUses, generateReport, getRanking, downloadDocument,
} from "@/lib/api";
import type {
  BulkImportJob, BulkImportItem, Campaign, GeneratedDocumentMeta, HsCodeEntry,
  LegalUseDescription, RankingRow, ResponsibilityMatrixRow, Substance, TariffRate,
} from "@/types/api";

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <div className="text-xs text-graphite">{label}</div>
      <div className="mt-1 font-semibold text-ink">{value}</div>
    </div>
  );
}

function Badge({ value, tone = "neutral" }: { value: string; tone?: "ok" | "warn" | "neutral" }) {
  const cls = tone === "ok" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : tone === "warn" ? "border-amber-200 bg-amber-50 text-amber-800" : "border-slate-200 bg-slate-50 text-graphite";
  return <span className={"inline-flex rounded-md border px-2 py-1 text-xs font-medium " + cls}>{value}</span>;
}

// ── Bulk Import View ──

export function BulkImportView() {
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<BulkImportJob | null>(null);
  const [items, setItems] = useState<BulkImportItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true); setError("");
    try { const r = await uploadBulkImport(file); setJob(r); setItems(await getBulkImportItems(r.id)); }
    catch { setError("Upload failed"); } finally { setLoading(false); }
  };
  const handleProcess = async () => {
    if (!job) return; setLoading(true);
    try { setJob(await processBulkImport(job.id)); setItems(await getBulkImportItems(job.id)); }
    catch { setError("Processing failed"); } finally { setLoading(false); }
  };
  const handleEnrich = async () => {
    if (!job) return; setLoading(true);
    try { await enrichBulkImport(job.id); setJob(await getBulkImportJob(job.id)); }
    catch { setError("Enrichment failed"); } finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">Bulk CAS Import</h2>
      <p className="text-sm text-graphite">Upload CSV/Excel with CAS numbers. Validates, creates substances, enriches from PubChem.</p>
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium text-graphite">File (.csv or .xlsx)</label>
          <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:bg-ink file:px-3 file:py-2 file:text-sm file:text-white" />
        </div>
        <button onClick={handleUpload} disabled={!file || loading} className="rounded-md bg-ink px-4 py-2 text-sm text-white disabled:opacity-50">{loading ? "..." : "Upload"}</button>
      </div>
      {error && <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {job && (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            <Metric label="Total" value={job.total_rows} />
            <Metric label="Valid" value={job.valid_rows} />
            <Metric label="Invalid" value={job.invalid_rows} />
            <Metric label="Status" value={job.status} />
          </div>
          {job.status === "pending" && <button onClick={handleProcess} disabled={loading} className="rounded-md bg-emerald-600 px-4 py-2 text-sm text-white">Process</button>}
          {job.status === "completed" && job.valid_rows > 0 && <button onClick={handleEnrich} disabled={loading} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white">Enrich from PubChem</button>}
          {items.length > 0 && (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-sm">
                <thead><tr className="bg-slate-50"><th className="px-3 py-2 text-left text-xs font-medium">Row</th><th className="px-3 py-2 text-left text-xs font-medium">CAS</th><th className="px-3 py-2 text-left text-xs font-medium">Valid</th><th className="px-3 py-2 text-left text-xs font-medium">Status</th></tr></thead>
                <tbody>{items.map((it) => (<tr key={it.id} className="border-t"><td className="px-3 py-2">{it.row_number}</td><td className="px-3 py-2 font-mono">{it.cas_raw}</td><td className="px-3 py-2">{it.cas_valid ? "OK" : "X"}</td><td className="px-3 py-2"><Badge value={it.status} tone={it.status === "created" ? "ok" : it.status === "invalid" ? "warn" : "neutral"} /></td></tr>))}</tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Tariff View ──

export function TariffView({ substances }: { substances: Substance[] }) {
  const [selSub, setSelSub] = useState("");
  const [hsCodes, setHsCodes] = useState<HsCodeEntry[]>([]);
  const [dutyRate, setDutyRate] = useState<TariffRate | null>(null);
  const [legalUses, setLegalUses] = useState<LegalUseDescription[]>([]);
  const [resp, setResp] = useState<ResponsibilityMatrixRow[]>([]);
  const [hsIn, setHsIn] = useState("");
  const [originIn, setOriginIn] = useState("CN");
  const [destIn, setDestIn] = useState("PL");
  const [incIn, setIncIn] = useState("FOB");

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-semibold text-ink">Tariff and Customs Intelligence</h2>
      <div className="rounded-md border p-4 space-y-3">
        <h3 className="text-sm font-semibold text-ink">HS Code Lookup</h3>
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="mb-1 block text-xs text-graphite">Substance</label>
            <select value={selSub} onChange={(e) => setSelSub(e.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
              <option value="">Select...</option>
              {substances.map((s) => <option key={s.id} value={s.id}>{s.primary_name || s.cas} ({s.cas})</option>)}
            </select>
          </div>
          <button onClick={async () => { const s = substances.find(x => x.id === selSub); if (s) { const c = await lookupHsCode(s.cas); setHsCodes(c); if (c[0]) setHsIn(c[0].hs_code); } }} className="rounded-md bg-ink px-4 py-2 text-sm text-white">Lookup</button>
        </div>
        {hsCodes.length > 0 && (
          <div className="overflow-x-auto rounded-md border">
            <table className="w-full text-sm">
              <thead><tr className="bg-slate-50"><th className="px-3 py-2 text-left text-xs font-medium">HS Code</th><th className="px-3 py-2 text-left text-xs font-medium">Description</th><th className="px-3 py-2 text-left text-xs font-medium">Conf.</th></tr></thead>
              <tbody>{hsCodes.map((c) => (<tr key={c.id} className="border-t cursor-pointer hover:bg-slate-50" onClick={() => setHsIn(c.hs_code)}><td className="px-3 py-2 font-mono">{c.hs_code}</td><td className="px-3 py-2">{c.description}</td><td className="px-3 py-2">{c.confidence ? (Number(c.confidence) * 100).toFixed(0) + "%" : "-"}</td></tr>))}</tbody>
            </table>
          </div>
        )}
      </div>
      <div className="rounded-md border p-4 space-y-3">
        <h3 className="text-sm font-semibold text-ink">Duty Rate</h3>
        <div className="grid grid-cols-4 gap-3">
          <div><label className="mb-1 block text-xs text-graphite">HS Code</label><input value={hsIn} onChange={(e) => setHsIn(e.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></div>
          <div><label className="mb-1 block text-xs text-graphite">Origin</label><input value={originIn} onChange={(e) => setOriginIn(e.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" maxLength={2} /></div>
          <div><label className="mb-1 block text-xs text-graphite">Dest.</label><input value={destIn} onChange={(e) => setDestIn(e.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" maxLength={2} /></div>
          <button onClick={async () => { if (hsIn) setDutyRate(await getDutyRate(hsIn, originIn, destIn)); }} className="self-end rounded-md bg-ink px-4 py-2 text-sm text-white">Check</button>
        </div>
        {dutyRate && (<div className="grid grid-cols-3 gap-3"><Metric label="Duty Rate" value={dutyRate.duty_rate_percent ? dutyRate.duty_rate_percent + "%" : "N/A"} /><Metric label="Preferential" value={dutyRate.preferential_rate ? dutyRate.preferential_rate + "%" : "N/A"} /><Metric label="Source" value={dutyRate.source_database} /></div>)}
      </div>
      <div className="rounded-md border p-4 space-y-3">
        <h3 className="text-sm font-semibold text-ink">Incoterms Responsibility ({incIn})</h3>
        <div className="flex items-end gap-3">
          <input value={incIn} onChange={(e) => setIncIn(e.target.value.toUpperCase())} className="w-32 rounded-md border px-3 py-2 text-sm" maxLength={3} />
          <button onClick={async () => setResp(await getResponsibilityMatrix(incIn))} className="rounded-md bg-ink px-4 py-2 text-sm text-white">Show</button>
        </div>
        {resp.length > 0 && (
          <table className="w-full text-sm">
            <thead><tr className="bg-slate-50"><th className="px-3 py-2 text-left text-xs font-medium">Cost</th><th className="px-3 py-2 text-left text-xs font-medium">Responsible</th></tr></thead>
            <tbody>{resp.map((r, i) => (<tr key={i} className="border-t"><td className="px-3 py-2 capitalize">{r.cost_type.replace(/_/g, " ")}</td><td className="px-3 py-2"><Badge value={r.responsible_party} tone={r.responsible_party === "seller" ? "ok" : "warn"} /></td></tr>))}</tbody>
          </table>
        )}
      </div>
      <div className="rounded-md border p-4 space-y-3">
        <h3 className="text-sm font-semibold text-ink">Legal Use Descriptions</h3>
        <button onClick={async () => { if (selSub) setLegalUses(await getLegalUses(selSub, destIn)); }} disabled={!selSub} className="rounded-md bg-ink px-4 py-2 text-sm text-white disabled:opacity-50">Get Suggestions</button>
        {legalUses.map((u) => (<div key={u.id} className="mt-2 rounded-md bg-slate-50 p-3 text-sm"><div className="font-medium text-ink">{u.description}</div><div className="mt-1 text-xs text-graphite">{u.category || "General"} {u.destination_country ? " - " + u.destination_country : " - Universal"}</div></div>))}
      </div>
    </div>
  );
}

// ── Reports View ──

export function ReportsView({ campaigns }: { campaigns: Campaign[] }) {
  const [selCamp, setSelCamp] = useState("");
  const [ranking, setRanking] = useState<RankingRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [rDoc, setRDoc] = useState<GeneratedDocumentMeta | null>(null);

  const dl = async (id: string) => {
    const b = await downloadDocument(id);
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u;
    a.download = "report." + (b.type.includes("pdf") ? "pdf" : "xlsx");
    a.click();
    URL.revokeObjectURL(u);
  };

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-semibold text-ink">Reports and Rankings</h2>
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="mb-1 block text-xs text-graphite">Campaign</label>
          <select value={selCamp} onChange={(e) => setSelCamp(e.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
            <option value="">Select...</option>
            {campaigns.map((c) => <option key={c.id} value={c.id}>{c.id.slice(0, 8)} - {c.quantity || "-"}</option>)}
          </select>
        </div>
        <button onClick={async () => { if (!selCamp) return; setLoading(true); try { setRDoc(await generateReport(selCamp, "pdf")); } finally { setLoading(false); } }} disabled={!selCamp || loading} className="rounded-md bg-ink px-4 py-2 text-sm text-white disabled:opacity-50">PDF</button>
        <button onClick={async () => { if (!selCamp) return; setLoading(true); try { setRDoc(await generateReport(selCamp, "xlsx")); } finally { setLoading(false); } }} disabled={!selCamp || loading} className="rounded-md bg-emerald-600 px-4 py-2 text-sm text-white disabled:opacity-50">Excel</button>
        <button onClick={async () => { if (selCamp) setRanking(await getRanking(selCamp)); }} disabled={!selCamp} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50">Ranking</button>
      </div>
      {rDoc && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 flex items-center justify-between">
          <div className="text-sm font-medium text-emerald-800">Report ready ({rDoc.file_size_bytes ? (rDoc.file_size_bytes / 1024).toFixed(1) + "KB" : ""})</div>
          <button onClick={() => dl(rDoc.id)} className="rounded-md bg-emerald-600 px-4 py-2 text-sm text-white">Download</button>
        </div>
      )}
      {ranking.length > 0 && (
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full text-sm">
            <thead><tr className="bg-slate-50"><th className="px-3 py-2 text-left text-xs font-medium">#</th><th className="px-3 py-2 text-left text-xs font-medium">Supplier</th><th className="px-3 py-2 text-left text-xs font-medium">Price</th><th className="px-3 py-2 text-left text-xs font-medium">Score</th><th className="px-3 py-2 text-left text-xs font-medium">Quality</th><th className="px-3 py-2 text-left text-xs font-medium">Risk</th><th className="px-3 py-2 text-left text-xs font-medium">Docs</th></tr></thead>
            <tbody>{ranking.map((r) => (
              <tr key={r.quote_id} className={"border-t" + (r.recommended ? " bg-emerald-50" : "")}>
                <td className="px-3 py-2 font-bold">{r.rank}{r.recommended ? " *" : ""}</td>
                <td className="px-3 py-2">{r.supplier_name}</td>
                <td className="px-3 py-2">{r.price || "-"} {r.currency || ""}</td>
                <td className="px-3 py-2 font-semibold">{r.total_score}</td>
                <td className="px-3 py-2">{r.supplier_quality_score}</td>
                <td className="px-3 py-2">{r.risk_score}</td>
                <td className="px-3 py-2">{r.document_completeness.toFixed(0)}%</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Rebrand MSDS/COA View ──

export function RebrandView() {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      Supplier COA/SDS rebranding is disabled. Store original supplier documents as evidence and generate only your own LOI, PO, RFQ, or report documents.
    </div>
  );
}
