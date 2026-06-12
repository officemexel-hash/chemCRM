"use client";

import { useState } from "react";
import type { SourcingBatch, SourcingReport } from "@/types/api";
import { API_BASE_URL } from "@/lib/api";
import { Badge, Metric, TextField, TextArea } from "@/components/Widgets";

const sourcingChannels = [
  ["legal_search", "Legal search"], ["contact_form", "Contact forms"], ["alibaba_internal", "Alibaba"],
  ["made_in_china_internal", "Made-in-China"], ["molbase_internal", "Molbase"], ["indiamart_internal", "IndiaMART"],
  ["whatsapp_business", "WhatsApp Business"], ["telegram_bot", "Telegram Bot"],
  ["signal_manual", "Signal manual"], ["threema_gateway", "Threema Gateway"], ["wickr_manual", "Wickr manual"]
] as const;

export function SourcingView() {
  const [batchName, setBatchName] = useState("CAS sourcing batch");
  const [csvText, setCsvText] = useState("CAS,quantity\n64-17-5,100 kg\n7732-18-5,200 kg");
  const [quantity, setQuantity] = useState("100 kg");
  const [destinationCountry, setDestinationCountry] = useState("Poland");
  const [requiredGrade, setRequiredGrade] = useState("technical grade");
  const [intendedUse, setIntendedUse] = useState("lawful industrial validation");
  const [channels, setChannels] = useState<string[]>(["legal_search", "contact_form", "alibaba_internal", "indiamart_internal"]);
  const [batch, setBatch] = useState<SourcingBatch | null>(null);
  const [report, setReport] = useState<SourcingReport | null>(null);
  const [status, setStatus] = useState("Ready");

  function toggleChannel(ch: string) { setChannels((c) => c.includes(ch) ? c.filter((x) => x !== ch) : [...c, ch]); }

  async function importBatch() {
    setStatus("Importing"); setBatch(null); setReport(null);
    const res = await fetch(`${API_BASE_URL}/sourcing/batches`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: batchName, csv_text: csvText, quantity, destination_country: destinationCountry, required_grade: requiredGrade, intended_use: intendedUse, channels, create_campaigns: true, auto_send_enabled: false }),
    });
    if (!res.ok) { setStatus("Import failed"); return; }
    const c = await res.json() as SourcingBatch; setBatch(c); setStatus("Imported");
    const rr = await fetch(`${API_BASE_URL}/sourcing/batches/${c.batch_id}/report`);
    if (rr.ok) setReport(await rr.json() as SourcingReport);
  }

  const summary = batch?.summary;
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Sourcing Batch</h2>
        <div className="flex items-center gap-2"><span className="text-sm text-graphite">{status}</span><button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={importBatch}>Import CAS</button></div>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">CAS Table</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Batch name" value={batchName} onChange={setBatchName} />
            <TextField label="Quantity" value={quantity} onChange={setQuantity} />
            <TextField label="Destination country" value={destinationCountry} onChange={setDestinationCountry} />
            <TextField label="Grade" value={requiredGrade} onChange={setRequiredGrade} />
          </div>
          <TextArea label="Intended use" value={intendedUse} onChange={setIntendedUse} compact />
          <TextArea label="Paste CAS table" value={csvText} onChange={setCsvText} />
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Channels</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {sourcingChannels.map(([v, l]) => (
              <label key={v} className="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-graphite">
                <input checked={channels.includes(v)} className="h-4 w-4" type="checkbox" onChange={() => toggleChannel(v)} />{l}
              </label>
            ))}
          </div>
          <div className="mt-4 grid gap-2 text-sm text-graphite">
            <div className="font-semibold text-ink">Run mode</div>
            <div>Forms and marketplace chats become reviewed tasks or drafts unless an official compliant integration is configured.</div>
            <div>Messenger channels require official API flow and consent evidence; Signal and Wickr stay manual-only.</div>
          </div>
        </section>
      </div>
      {summary ? <div className="grid gap-3 md:grid-cols-4 xl:grid-cols-8"><Metric label="Inputs" value={summary.total_inputs} /><Metric label="Valid" value={summary.valid} /><Metric label="Invalid" value={summary.invalid} /><Metric label="Duplicates" value={summary.duplicates} /><Metric label="Substances" value={summary.substances_created} /><Metric label="Campaigns" value={summary.campaigns_created} /><Metric label="Tasks" value={summary.manual_tasks_created} /><Metric label="Queries" value={summary.queries_generated} /></div> : null}
      {batch ? (
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <table className="w-full min-w-[940px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-graphite"><tr><th className="px-4 py-3">CAS</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Campaign</th><th className="px-4 py-3">Queries</th><th className="px-4 py-3">Tasks</th><th className="px-4 py-3">Notes</th></tr></thead>
            <tbody>{batch.items.map((item, i) => (<tr key={`${item.raw_cas}-${i}`} className="border-t border-slate-100"><td className="px-4 py-3 font-medium text-ink">{item.cas ?? item.raw_cas}</td><td className="px-4 py-3"><Badge value={item.status} tone={item.status === "ready" ? "ok" : "warn"} /></td><td className="px-4 py-3">{item.campaign_id ? item.campaign_id.slice(0, 8) : "n/a"}</td><td className="px-4 py-3">{item.queries.length}</td><td className="px-4 py-3">{item.tasks.length}</td><td className="px-4 py-3 text-graphite">{item.errors.join("; ") || item.tasks.map((t) => t.channel).filter(Boolean).join(", ")}</td></tr>))}</tbody>
          </table>
        </div>
      ) : null}
      {report ? (
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Batch Report</h3>
          <div className="grid gap-3 md:grid-cols-4"><Metric label="Campaigns" value={report.campaign_ids.length} /><Metric label="Manual tasks" value={report.manual_task_ids.length} /><Metric label="Outbound" value={report.outbound_messages} /><Metric label="Quotes" value={report.quotes} /></div>
          <div className="mt-4 grid gap-2">{Object.entries(report.channel_plan).map(([ch, plan]) => (<div key={ch} className="rounded-md bg-slate-50 p-3 text-sm text-graphite"><span className="font-semibold text-ink">{ch.replaceAll("_", " ")}</span>: {plan}</div>))}</div>
        </section>
      ) : null}
    </section>
  );
}
