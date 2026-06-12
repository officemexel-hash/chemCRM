"use client";

import { useState } from "react";
import type { Campaign, GeneratedDocumentMeta, RankingRow } from "@/types/api";
import { Badge } from "@/components/Widgets";
import { generateReport, getRanking, downloadDocument } from "@/lib/api";

export function ReportsView({ campaigns }: { campaigns: Campaign[] }) {
  const [campaignId, setCampaignId] = useState(campaigns[0]?.id ?? "");
  const [ranking, setRanking] = useState<RankingRow[]>([]);
  const [generated, setGenerated] = useState<GeneratedDocumentMeta | null>(null);
  const [status, setStatus] = useState("Ready");

  async function loadRanking() { if (!campaignId) return; setStatus("Loading ranking"); setRanking(await getRanking(campaignId)); setStatus("Ranking loaded"); }
  async function createReport() { if (!campaignId) return; setStatus("Generating report"); try { setGenerated(await generateReport(campaignId, "pdf")); setStatus("Report generated"); } catch { setStatus("Report failed"); } }
  async function dl() { if (!generated?.id) return; setStatus("Preparing download"); try { const b = await downloadDocument(generated.id); const u = URL.createObjectURL(b); const a = document.createElement("a"); a.href = u; a.download = `rfq-report-${generated.id}.pdf`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(u); setStatus("Download ready"); } catch { setStatus("Download failed"); } }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold text-ink">Reports</h2><span className="text-sm text-graphite">{status}</span></div>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
          <select className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink" value={campaignId} onChange={(e) => setCampaignId(e.target.value)}>
            <option value="">Select campaign</option>
            {campaigns.map((c) => <option key={c.id} value={c.id}>{c.quantity ?? "Quantity TBD"} - {c.destination_country ?? "Destination TBD"}</option>)}
          </select>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" disabled={!campaignId} type="button" onClick={loadRanking}>Load ranking</button>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50" disabled={!campaignId} type="button" onClick={createReport}>Generate PDF</button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" disabled={!generated?.id} type="button" onClick={dl}>Download</button>
        </div>
      </section>
      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite"><tr><th className="px-4 py-3">Rank</th><th className="px-4 py-3">Supplier</th><th className="px-4 py-3">Score</th><th className="px-4 py-3">Price</th><th className="px-4 py-3">Risk</th><th className="px-4 py-3">Recommendation</th></tr></thead>
          <tbody>
            {ranking.length ? ranking.map((r) => (<tr key={r.quote_id} className="border-t border-slate-100"><td className="px-4 py-3">{r.rank}</td><td className="px-4 py-3 font-medium text-ink">{r.supplier_name}</td><td className="px-4 py-3">{r.total_score}</td><td className="px-4 py-3">{r.price ?? "n/a"} {r.currency ?? ""}</td><td className="px-4 py-3">{r.risk_score}</td><td className="px-4 py-3"><Badge value={r.recommended ? "recommended" : "review"} tone={r.recommended ? "ok" : "warn"} /></td></tr>)) : <tr><td className="px-4 py-6 text-sm text-graphite" colSpan={6}>Load a campaign ranking to generate procurement reports.</td></tr>}
          </tbody>
        </table>
      </section>
    </section>
  );
}
