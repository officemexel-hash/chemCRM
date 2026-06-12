"use client";

import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import type { QuoteComparisonRow } from "@/types/api";
import { Badge } from "@/components/Widgets";
import { markQuoteReviewed } from "@/lib/api";

export function QuotesView({ rows }: { rows: QuoteComparisonRow[] }) {
  const [reviewing, setReviewing] = useState<string | null>(null);
  async function review(qid: string) { setReviewing(qid); try { await markQuoteReviewed(qid); } finally { setReviewing(null); } }
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Quote Comparison</h2>
        <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" type="button" onClick={() => rows[0] && review(rows[0].quote_id)} disabled={reviewing !== null}>{reviewing ? "Reviewing..." : "Mark reviewed"}</button>
      </div>
      <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite">
            <tr>
              <th className="px-4 py-3">Supplier</th><th className="px-4 py-3">Price/kg</th><th className="px-4 py-3">MOQ</th>
              <th className="px-4 py-3">Incoterms</th><th className="px-4 py-3">Lead time</th><th className="px-4 py-3">Docs</th>
              <th className="px-4 py-3">Risk</th><th className="px-4 py-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.quote_id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-ink">{r.best_quote && <CheckCircle2 className="mr-2 inline text-mint" size={16} />}{r.supplier}</td>
                <td className="px-4 py-3">{r.price ?? "n/a"} {r.currency}/{r.unit}</td>
                <td className="px-4 py-3">{r.moq ?? "n/a"}</td>
                <td className="px-4 py-3">{r.incoterms ?? "n/a"}</td>
                <td className="px-4 py-3">{r.lead_time ?? "n/a"}</td>
                <td className="px-4 py-3">{r.coa_available ? "COA" : "no COA"} / {r.sds_available ? "SDS" : "no SDS"}</td>
                <td className="px-4 py-3"><Badge value={r.risk_level ?? "unknown"} tone={r.risk_level === "low" ? "ok" : "warn"} /></td>
                <td className="px-4 py-3">{r.confidence ?? "n/a"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
