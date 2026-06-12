"use client";

import type { Substance } from "@/types/api";
import { Badge } from "@/components/Widgets";

export function SubstancesView({ substances, onDialog }: { substances: Substance[]; onDialog: (d: string) => void }) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Substances</h2>
        <div className="flex gap-2">
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => onDialog("enrich-substances")}>Enrich selected</button>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={() => onDialog("add-substance")}>Add CAS</button>
        </div>
      </div>
      <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite">
            <tr>
              <th className="px-4 py-3">CAS</th><th className="px-4 py-3">Primary name</th><th className="px-4 py-3">PubChem</th>
              <th className="px-4 py-3">Formula</th><th className="px-4 py-3">Regulatory</th><th className="px-4 py-3">Manual review</th>
            </tr>
          </thead>
          <tbody>
            {substances.map((s) => (
              <tr key={s.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-ink">{s.cas}</td>
                <td className="px-4 py-3">{s.primary_name ?? "unknown"}</td>
                <td className="px-4 py-3">{s.pubchem_cid ?? "n/a"}</td>
                <td className="px-4 py-3">{s.molecular_formula ?? "n/a"}</td>
                <td className="px-4 py-3"><Badge value={s.regulatory_status ?? "unknown"} /></td>
                <td className="px-4 py-3">{s.requires_manual_review ? "required" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
