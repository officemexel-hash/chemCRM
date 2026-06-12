"use client";

import { useState } from "react";
import type { HsCodeEntry, LegalUseDescription, TariffRate, Substance } from "@/types/api";
import { TextField, TextArea } from "@/components/Widgets";
import { lookupHsCode, getDutyRate, getLegalUses, getCustomsText } from "@/lib/api";

export function TariffView({ substances }: { substances: Substance[] }) {
  const firstSubstance = substances[0];
  const [selectedSubstanceId, setSelectedSubstanceId] = useState(firstSubstance?.id ?? "");
  const [cas, setCas] = useState(firstSubstance?.cas ?? "64-17-5");
  const [origin, setOrigin] = useState("CN");
  const [destination, setDestination] = useState("PL");
  const [hsEntries, setHsEntries] = useState<HsCodeEntry[]>([]);
  const [selectedHsCode, setSelectedHsCode] = useState("");
  const [duty, setDuty] = useState<TariffRate | null>(null);
  const [legalUses, setLegalUses] = useState<LegalUseDescription[]>([]);
  const [customsText, setCustomsText] = useState("");
  const [status, setStatus] = useState("Ready");

  async function run() {
    setStatus("Looking up tariff data");
    const entries = await lookupHsCode(cas, selectedSubstanceId || undefined);
    setHsEntries(entries);
    const hsc = entries[0]?.hs_code ?? selectedHsCode;
    setSelectedHsCode(hsc);
    if (hsc) {
      const d = await getDutyRate(hsc, origin, destination);
      setDuty(d);
      if (selectedSubstanceId) {
        const [uses, text] = await Promise.all([getLegalUses(selectedSubstanceId, destination), getCustomsText(selectedSubstanceId, hsc, destination)]);
        setLegalUses(uses); setCustomsText(text.declaration_text);
      }
    }
    setStatus("Loaded");
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Tariff And Customs Screening</h2>
        <div className="flex items-center gap-2"><span className="text-sm text-graphite">{status}</span><button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={run}>Lookup</button></div>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="grid gap-1 text-sm text-graphite">Substance
            <select className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink" value={selectedSubstanceId} onChange={(e) => { setSelectedSubstanceId(e.target.value); const s = substances.find((x) => x.id === e.target.value); if (s?.cas) setCas(s.cas); }}>
              <option value="">Manual CAS</option>
              {substances.map((s) => <option key={s.id} value={s.id}>{s.cas} - {s.primary_name ?? "unknown"}</option>)}
            </select>
          </label>
          <TextField label="CAS" value={cas} onChange={setCas} />
          <TextField label="Origin" value={origin} onChange={setOrigin} />
          <TextField label="Destination" value={destination} onChange={setDestination} />
        </div>
      </section>
      <div className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">HS Candidates</h3>
          <div className="grid gap-2">
            {hsEntries.length ? hsEntries.map((e) => (
              <button key={e.id} className={`rounded-md border p-3 text-left text-sm ${selectedHsCode === e.hs_code ? "border-mint bg-emerald-50" : "border-slate-200 bg-white"}`} type="button" onClick={() => setSelectedHsCode(e.hs_code)}>
                <div className="font-semibold text-ink">{e.hs_code}</div><div className="text-graphite">{e.description ?? "No description"}</div><div className="mt-1 text-xs text-graphite">Source: {e.source_database} | Confidence: {e.confidence ?? "n/a"}</div>
              </button>
            )) : <p className="text-sm text-graphite">Run lookup to see HS suggestions.</p>}
          </div>
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Duty And Declaration Text</h3>
          <div className="grid gap-2 text-sm text-graphite">
            <div><span className="font-semibold text-ink">HS:</span> {selectedHsCode || "n/a"}</div>
            <div><span className="font-semibold text-ink">Duty:</span> {duty?.duty_rate_percent ?? "verify"} {duty?.duty_type ?? ""}</div>
            <div><span className="font-semibold text-ink">Preferential:</span> {duty?.preferential_rate ?? "n/a"}</div>
            <div><span className="font-semibold text-ink">Source:</span> {duty?.source_database ?? "official lookup required"}</div>
            <TextArea label="Customs text draft" value={customsText} onChange={setCustomsText} compact />
          </div>
        </section>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="mb-3 font-semibold text-ink">Legal Use Suggestions</h3>
        <div className="grid gap-2">
          {legalUses.length ? legalUses.map((u) => <div key={u.id} className="rounded-md bg-slate-50 p-3 text-sm text-graphite"><div className="font-medium text-ink">{u.category ?? "use case"}</div>{u.description}</div>) : <p className="text-sm text-graphite">Legal-use drafts appear after a substance lookup.</p>}
        </div>
      </section>
    </section>
  );
}
