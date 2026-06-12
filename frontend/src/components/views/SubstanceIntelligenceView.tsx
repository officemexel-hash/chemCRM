"use client";

import { useState } from "react";
import type { Substance, SubstanceSourcingProfile, ManufacturingAnalysis } from "@/types/api";
import { Badge, Metric, TextField, TextArea, InfoList } from "@/components/Widgets";
import { getSubstanceIntelligence, createManufacturingAnalysis, listManufacturingAnalyses } from "@/lib/api";

export function SubstanceIntelligenceView({ substances }: { substances: Substance[] }) {
  const [selectedId, setSelectedId] = useState(substances[0]?.id ?? "");
  const [profile, setProfile] = useState<SubstanceSourcingProfile | null>(null);
  const [analyses, setAnalyses] = useState<ManufacturingAnalysis[]>([]);
  const [analysis, setAnalysis] = useState<ManufacturingAnalysis | null>(null);
  const [targetQuantity, setTargetQuantity] = useState("1000 kg/month");
  const [targetGrade, setTargetGrade] = useState("technical grade");
  const [destinationCountry, setDestinationCountry] = useState("PL");
  const [intendedUse, setIntendedUse] = useState("Lawful industrial validation.");
  const [createTasks, setCreateTasks] = useState(true);
  const [status, setStatus] = useState("Ready");
  const selectedSubstance = substances.find((s) => s.id === selectedId);

  async function loadProfile(sid = selectedId) {
    if (!sid) return; setStatus("Loading intelligence");
    const p = await getSubstanceIntelligence(sid);
    const a = await listManufacturingAnalyses(sid);
    setProfile(p); setAnalyses(a); setAnalysis(a[0] ?? null);
    setStatus(p ? "Loaded" : "No profile data");
  }
  async function runAnalysis() {
    if (!selectedId) return; setStatus("Analyzing production cost model");
    try {
      const r = await createManufacturingAnalysis(selectedId, { target_quantity: targetQuantity, target_grade: targetGrade, intended_use: intendedUse, destination_country: destinationCountry, include_raw_material_sourcing: true, create_raw_material_tasks: createTasks, save_to_crm: true });
      setAnalysis(r); setAnalyses([r, ...analyses.filter((a) => a.id !== r.id)]); setStatus("Analysis saved");
    } catch { setStatus("Analysis failed"); }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h2 className="text-lg font-semibold text-ink">Substance Intelligence</h2><p className="text-sm text-graphite">Supplier database, contact history, offer terms, Incoterms and production cost scoping.</p></div>
        <span className="text-sm text-graphite">{status}</span>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto]">
          <select className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink" value={selectedId} onChange={(e) => { setSelectedId(e.target.value); setProfile(null); setAnalysis(null); }}>
            <option value="">Select substance</option>
            {substances.map((s) => <option key={s.id} value={s.id}>{s.cas} - {s.primary_name ?? "unknown"}</option>)}
          </select>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50" disabled={!selectedId} type="button" onClick={() => loadProfile()}>Load Profile</button>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50" disabled={!selectedId} type="button" onClick={runAnalysis}>Analyze Cost</button>
        </div>
      </section>
      {selectedSubstance ? <div className="grid gap-3 md:grid-cols-4"><Metric label="CAS" value={selectedSubstance.cas} /><Metric label="Substance" value={selectedSubstance.primary_name ?? "unknown"} /><Metric label="Regulatory" value={selectedSubstance.regulatory_status ?? "unknown"} /><Metric label="Manual review" value={selectedSubstance.requires_manual_review ? "required" : "no"} /></div> : null}
      {profile ? (
        <>
          <div className="grid gap-3 md:grid-cols-5"><Metric label="Suppliers" value={profile.summary.supplier_count} /><Metric label="Contacts" value={profile.summary.contact_count} /><Metric label="Quotes" value={profile.summary.quote_count} /><Metric label="Offers" value={profile.summary.offer_count} /><Metric label="Best price" value={profile.summary.best_price ? `${profile.summary.best_price} ${profile.summary.best_price_currency ?? ""}/${profile.summary.best_price_unit ?? ""}` : "n/a"} /></div>
          {profile.open_questions.length ? <section className="rounded-md border border-amber-200 bg-amber-50 p-4"><h3 className="mb-2 font-semibold text-ink">Open Questions</h3><div className="grid gap-2">{profile.open_questions.map((q) => <div key={q} className="text-sm text-amber-900">{q}</div>)}</div></section> : null}
          <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <section className="rounded-md border border-slate-200 bg-white p-4">
              <h3 className="mb-3 font-semibold text-ink">Supplier Records</h3>
              <div className="grid gap-3">
                {profile.suppliers.length ? profile.suppliers.map((sup) => (
                  <div key={sup.id} className="rounded-md border border-slate-200 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div><div className="font-semibold text-ink">{sup.name}</div><div className="text-sm text-graphite">{sup.country ?? "unknown"} · {sup.company_type ?? "UNKNOWN"} · risk {sup.risk_level ?? "unknown"}</div></div>
                      <Badge value={`score ${sup.supplier_score ?? 0}`} tone={Number(sup.risk_score ?? 0) > 30 ? "warn" : "ok"} />
                    </div>
                    <div className="mt-3 grid gap-2 text-sm text-graphite">
                      <div><span className="font-medium text-ink">Contacts:</span> {sup.contacts.map((c) => `${c.channel}: ${c.value}`).join("; ") || "none"}</div>
                      <div><span className="font-medium text-ink">Packaging:</span> {sup.quoted_packaging.join("; ") || "missing"}</div>
                      <div><span className="font-medium text-ink">Incoterms:</span> {sup.quoted_incoterms.join(", ") || "missing"}</div>
                    </div>
                    {sup.quotes.length ? <div className="mt-3 overflow-hidden rounded-md border border-slate-100"><table className="w-full text-left text-xs"><thead className="bg-slate-50 text-graphite"><tr><th className="px-2 py-2">Price</th><th className="px-2 py-2">MOQ</th><th className="px-2 py-2">Incoterms</th><th className="px-2 py-2">Transport</th><th className="px-2 py-2">Packaging</th><th className="px-2 py-2">Lead time</th></tr></thead><tbody>{sup.quotes.map((q) => (<tr key={q.id} className="border-t border-slate-100"><td className="px-2 py-2">{q.price ?? "n/a"} {q.currency ?? ""}/{q.unit ?? ""}</td><td className="px-2 py-2">{q.moq ?? "n/a"}</td><td className="px-2 py-2">{q.incoterms ?? "n/a"}</td><td className="px-2 py-2">{q.transport_mode ?? "n/a"}</td><td className="px-2 py-2">{q.packaging ?? "n/a"}</td><td className="px-2 py-2">{q.lead_time ?? "n/a"}</td></tr>))}</tbody></table></div> : null}
                    {sup.contact_history.length ? <div className="mt-3 grid gap-2">{sup.contact_history.slice(0, 3).map((h) => (<div key={h.id} className="rounded-md bg-slate-50 p-2 text-xs text-graphite"><span className="font-medium text-ink">{h.direction}</span> · {h.channel ?? "channel"} · {h.status ?? "status"} · {h.subject ?? "no subject"}</div>))}</div> : null}
                  </div>
                )) : <p className="text-sm text-graphite">No suppliers are linked to this substance yet.</p>}
              </div>
            </section>
            <section className="rounded-md border border-slate-200 bg-white p-4"><h3 className="mb-3 font-semibold text-ink">Incoterms By Transport</h3><div className="grid gap-2">{profile.incoterms_by_transport.map((item) => (<div key={item.transport_mode} className="rounded-md bg-slate-50 p-3 text-sm"><div className="font-semibold text-ink">{item.transport_mode}</div><div className="mt-1 text-graphite">{item.recommended_incoterms.join(", ")}</div></div>))}</div></section>
          </div>
        </>
      ) : <section className="rounded-md border border-slate-200 bg-white p-4 text-sm text-graphite">Load a substance profile to build the substance-centered supplier and quote database.</section>}
      <div className="grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">Production Cost Scoping</h3>
          <TextField label="Target quantity" value={targetQuantity} onChange={setTargetQuantity} />
          <TextField label="Target grade" value={targetGrade} onChange={setTargetGrade} />
          <TextField label="Destination country" value={destinationCountry} onChange={setDestinationCountry} />
          <TextArea label="Intended lawful use" value={intendedUse} onChange={setIntendedUse} compact />
          <label className="mt-3 flex items-center gap-2 text-sm text-graphite"><input checked={createTasks} type="checkbox" onChange={(e) => setCreateTasks(e.target.checked)} />Create manual tasks for input material sourcing queries</label>
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold text-ink">Latest Analysis</h3><Badge value={analysis?.status ?? "not generated"} tone={analysis?.blocked_reasons?.length ? "warn" : "ok"} /></div>
          {analysis ? (
            <div className="grid gap-3 text-sm text-graphite">
              {analysis.process_overview ? <p>{analysis.process_overview}</p> : null}
              {analysis.blocked_reasons.length ? <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-amber-900">{analysis.blocked_reasons.join("; ")}</div> : null}
              <div className="grid gap-2 md:grid-cols-2"><InfoList title="Equipment classes" items={analysis.required_equipment} primaryKey="category" secondaryKey="examples" /><InfoList title="Input materials" items={analysis.input_materials} primaryKey="name" secondaryKey="role" /><InfoList title="Cost drivers" items={analysis.cost_drivers} primaryKey="name" secondaryKey="impact" /><InfoList title="Sourcing queries" items={analysis.sourcing_queries} primaryKey="material" secondaryKey="query" /></div>
              {analysis.safety_notes.length ? <div className="rounded-md bg-slate-50 p-3 text-xs">{analysis.safety_notes.join(" ")}</div> : null}
            </div>
          ) : <p className="text-sm text-graphite">Run analysis to create a safe manufacturing feasibility and input-material cost model.</p>}
          {analyses.length > 1 ? <div className="mt-3 text-xs text-graphite">Saved analyses: {analyses.length}</div> : null}
        </section>
      </div>
    </section>
  );
}
