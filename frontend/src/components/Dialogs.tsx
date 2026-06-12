"use client";

import { X } from "lucide-react";
import { useState } from "react";
import type { Campaign, Message, Substance, Supplier, ManualTask } from "@/types/api";
import {
  createSubstance, enrichSubstance, createSupplier, classifySupplier,
  createCampaign, generateRfq, runAutonomousCampaign, markTaskCompleted,
} from "@/lib/api";

// ── Reusable Modal shell ──

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-slate-200 bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          <button className="rounded-md p-1 text-graphite hover:bg-slate-100" type="button" onClick={onClose}><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <label className="grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <input className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </label>
  );
}

// ── Add Substance Dialog ──

export function AddSubstanceDialog({ onClose, onCreated }: { onClose: () => void; onCreated: (s: Substance) => void }) {
  const [cas, setCas] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!cas.trim()) { setError("CAS number is required"); return; }
    setLoading(true); setError("");
    try {
      const s = await createSubstance(cas.trim(), name.trim() || undefined);
      onCreated(s);
      onClose();
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  return (
    <Modal title="Add Substance" onClose={onClose}>
      <div className="space-y-3">
        <Field label="CAS number *" value={cas} onChange={setCas} placeholder="64-17-5" />
        <Field label="Primary name (optional)" value={name} onChange={setName} placeholder="Ethanol" />
        {error && <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
        <button className="w-full rounded-md bg-mint px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" disabled={loading} type="button" onClick={submit}>
          {loading ? "Creating..." : "Create Substance"}
        </button>
      </div>
    </Modal>
  );
}

// ── Add Supplier Dialog ──

export function AddSupplierDialog({ onClose, onCreated }: { onClose: () => void; onCreated: (s: Supplier) => void }) {
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [country, setCountry] = useState("");
  const [companyType, setCompanyType] = useState("UNKNOWN");
  const [contactChannel, setContactChannel] = useState("email");
  const [contactValue, setContactValue] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [evidenceText, setEvidenceText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!name.trim()) { setError("Supplier name is required"); return; }
    setLoading(true); setError("");
    try {
      const s = await createSupplier({
        name: name.trim(),
        website: website.trim() || undefined,
        country: country.trim() || undefined,
        company_type: companyType,
        contacts: contactValue.trim() ? [{ channel: contactChannel, value: contactValue.trim(), source_url: sourceUrl.trim(), evidence_text: evidenceText.trim() }] : [],
      });
      onCreated(s);
      onClose();
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  return (
    <Modal title="Add Supplier" onClose={onClose}>
      <div className="space-y-3">
        <Field label="Company name *" value={name} onChange={setName} placeholder="Acme Chemicals Ltd" />
        <Field label="Website" value={website} onChange={setWebsite} placeholder="https://example.com" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Country" value={country} onChange={setCountry} placeholder="PL" />
          <label className="grid gap-1 text-sm text-graphite">
            <span>Company type</span>
            <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={companyType} onChange={(e) => setCompanyType(e.target.value)}>
              {["UNKNOWN", "MANUFACTURER", "AUTHORIZED_DISTRIBUTOR", "TRADER_BROKER", "MARKETPLACE_STORE", "LAB_SUPPLIER", "EXPORT_AGENT"].map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
        </div>
        <hr className="border-slate-200" />
        <p className="text-xs font-semibold text-graphite">Contact (required for RFQ)</p>
        <div className="grid grid-cols-2 gap-3">
          <label className="grid gap-1 text-sm text-graphite">
            <span>Channel</span>
            <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={contactChannel} onChange={(e) => setContactChannel(e.target.value)}>
              {["email", "form", "phone"].map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <Field label="Contact value" value={contactValue} onChange={setContactValue} placeholder="sales@example.com" />
        </div>
        <Field label="Source URL" value={sourceUrl} onChange={setSourceUrl} placeholder="https://example.com/contact" />
        <Field label="Evidence text" value={evidenceText} onChange={setEvidenceText} placeholder="Found via company website contact page" />
        {error && <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
        <button className="w-full rounded-md bg-mint px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" disabled={loading} type="button" onClick={submit}>
          {loading ? "Creating..." : "Create Supplier"}
        </button>
      </div>
    </Modal>
  );
}

// ── Create Campaign Dialog ──

export function CreateCampaignDialog({ substances, onClose, onCreated }: { substances: Substance[]; onClose: () => void; onCreated: (c: Campaign) => void }) {
  const [substanceId, setSubstanceId] = useState(substances[0]?.id ?? "");
  const [quantity, setQuantity] = useState("100 kg");
  const [destination, setDestination] = useState("Poland");
  const [grade, setGrade] = useState("technical grade");
  const [intendedUse, setIntendedUse] = useState("lawful industrial validation");
  const [autoSend, setAutoSend] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!substanceId) { setError("Select a substance"); return; }
    setLoading(true); setError("");
    try {
      const c = await createCampaign({ substance_id: substanceId, quantity, destination_country: destination, required_grade: grade, intended_use: intendedUse, auto_send_enabled: autoSend });
      onCreated(c);
      onClose();
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  return (
    <Modal title="Create RFQ Campaign" onClose={onClose}>
      <div className="space-y-3">
        <label className="grid gap-1 text-sm text-graphite">
          <span>Substance *</span>
          <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={substanceId} onChange={(e) => setSubstanceId(e.target.value)}>
            <option value="">Select...</option>
            {substances.map((s) => <option key={s.id} value={s.id}>{s.cas} - {s.primary_name ?? "unknown"}</option>)}
          </select>
        </label>
        <Field label="Quantity" value={quantity} onChange={setQuantity} />
        <Field label="Destination country" value={destination} onChange={setDestination} />
        <Field label="Required grade" value={grade} onChange={setGrade} />
        <Field label="Intended use" value={intendedUse} onChange={setIntendedUse} />
        <label className="flex items-center gap-2 text-sm text-graphite">
          <input className="h-4 w-4" type="checkbox" checked={autoSend} onChange={(e) => setAutoSend(e.target.checked)} />
          Auto-send enabled (low-risk only)
        </label>
        {error && <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
        <button className="w-full rounded-md bg-mint px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" disabled={loading} type="button" onClick={submit}>
          {loading ? "Creating..." : "Create Campaign"}
        </button>
      </div>
    </Modal>
  );
}

// ── Generate RFQ Dialog ──

export function GenerateRfqDialog({ campaigns, suppliers, onClose, onGenerated }: {
  campaigns: Campaign[]; suppliers: Supplier[]; onClose: () => void;
  onGenerated: (msg: Message) => void;
}) {
  const [campaignId, setCampaignId] = useState(campaigns[0]?.id ?? "");
  const [supplierId, setSupplierId] = useState("");
  const [contactId, setContactId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Message | null>(null);

  const selectedSupplier = suppliers.find((s) => s.id === supplierId);
  const contacts = selectedSupplier?.contacts ?? [];

  async function submit() {
    if (!campaignId || !supplierId || !contactId) { setError("All fields required"); return; }
    setLoading(true); setError("");
    try {
      const msg = await generateRfq(campaignId, supplierId, contactId);
      setResult(msg);
      onGenerated(msg);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  return (
    <Modal title="Generate RFQ Draft" onClose={onClose}>
      <div className="space-y-3">
        <label className="grid gap-1 text-sm text-graphite">
          <span>Campaign *</span>
          <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={campaignId} onChange={(e) => setCampaignId(e.target.value)}>
            <option value="">Select...</option>
            {campaigns.map((c) => <option key={c.id} value={c.id}>{c.id.slice(0, 8)} - {c.quantity ?? "-"}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm text-graphite">
          <span>Supplier *</span>
          <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={supplierId} onChange={(e) => { setSupplierId(e.target.value); setContactId(""); }}>
            <option value="">Select...</option>
            {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.country ?? "?"})</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm text-graphite">
          <span>Contact *</span>
          <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={contactId} onChange={(e) => setContactId(e.target.value)} disabled={!supplierId}>
            <option value="">Select...</option>
            {contacts.map((c) => <option key={c.id} value={c.id}>{c.channel}: {c.value}</option>)}
          </select>
        </label>
        {error && <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
        {result && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm">
            <div className="font-semibold text-emerald-800">RFQ Generated</div>
            <div className="mt-1 text-emerald-700">Subject: {result.subject}</div>
            <div className="text-emerald-700">Status: {result.status}</div>
            <div className="text-emerald-700">Policy: {result.policy_decision}</div>
          </div>
        )}
        <button className="w-full rounded-md bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50" disabled={loading} type="button" onClick={submit}>
          {loading ? "Generating..." : "Generate RFQ Draft"}
        </button>
      </div>
    </Modal>
  );
}

// ── Autonomous Run Dialog ──

export function AutonomousRunDialog({ campaigns, onClose, onRan }: {
  campaigns: Campaign[]; onClose: () => void;
  onRan: (result: { campaign_id: string; generated: number; sent: number; blocked: number }) => void;
}) {
  const [campaignId, setCampaignId] = useState(campaigns[0]?.id ?? "");
  const [dryRun, setDryRun] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Awaited<ReturnType<typeof runAutonomousCampaign>> | null>(null);

  async function submit() {
    if (!campaignId) { setError("Select a campaign"); return; }
    setLoading(true); setError("");
    try {
      const r = await runAutonomousCampaign(campaignId, { dry_run: dryRun });
      setResult(r);
      onRan(r);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  return (
    <Modal title="Autonomous Campaign Run" onClose={onClose}>
      <div className="space-y-3">
        <label className="grid gap-1 text-sm text-graphite">
          <span>Campaign *</span>
          <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={campaignId} onChange={(e) => setCampaignId(e.target.value)}>
            <option value="">Select...</option>
            {campaigns.map((c) => <option key={c.id} value={c.id}>{c.id.slice(0, 8)} - {c.quantity ?? "-"}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-graphite">
          <input className="h-4 w-4" type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
          Dry run (no messages sent)
        </label>
        {error && <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
        {result && (
          <div className="grid grid-cols-3 gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3">
            <div className="text-center"><div className="text-lg font-bold text-emerald-800">{result.generated}</div><div className="text-xs text-emerald-700">Generated</div></div>
            <div className="text-center"><div className="text-lg font-bold text-amber-800">{result.requires_approval ?? 0}</div><div className="text-xs text-amber-700">Need Approval</div></div>
            <div className="text-center"><div className="text-lg font-bold text-red-800">{result.blocked}</div><div className="text-xs text-red-700">Blocked</div></div>
          </div>
        )}
        <button className="w-full rounded-md bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50" disabled={loading} type="button" onClick={submit}>
          {loading ? "Running..." : "Run Autonomous Campaign"}
        </button>
      </div>
    </Modal>
  );
}

// ── Enrich Substances Dialog ──

export function EnrichSubstancesDialog({ substances, onClose, onEnriched }: {
  substances: Substance[]; onClose: () => void;
  onEnriched: (updated: Substance) => void;
}) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  function toggle(id: string) {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  }

  async function enrich() {
    setLoading(true); setStatus("Enriching...");
    for (const id of selectedIds) {
      try { const updated = await enrichSubstance(id); onEnriched(updated); setStatus(`Done: ${selectedIds.size} substances`); }
      catch { setStatus(`Failed on ${id}`); }
    }
    setLoading(false);
  }

  return (
    <Modal title="Enrich Substances" onClose={onClose}>
      <div className="space-y-3">
        <p className="text-sm text-graphite">Select substances to enrich with PubChem data</p>
        <div className="max-h-64 space-y-1 overflow-y-auto">
          {substances.map((s) => (
            <label key={s.id} className="flex items-center gap-2 rounded-md p-2 text-sm hover:bg-slate-50">
              <input className="h-4 w-4" type="checkbox" checked={selectedIds.has(s.id)} onChange={() => toggle(s.id)} />
              <span className="font-medium text-ink">{s.cas}</span>
              <span className="text-graphite">{s.primary_name ?? "unknown"}</span>
            </label>
          ))}
        </div>
        {status && <div className="rounded-md bg-slate-50 p-2 text-sm text-graphite">{status}</div>}
        <button className="w-full rounded-md bg-mint px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" disabled={loading || selectedIds.size === 0} type="button" onClick={enrich}>
          {loading ? "Enriching..." : `Enrich ${selectedIds.size} selected`}
        </button>
      </div>
    </Modal>
  );
}

// ── Classify Suppliers Dialog ──

export function ClassifySuppliersDialog({ suppliers, onClose, onClassified }: {
  suppliers: Supplier[]; onClose: () => void;
  onClassified: (updated: { id: string; company_type: string; supplier_score: number; risk_score: number; risk_level: string }) => void;
}) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  function toggle(id: string) {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  }

  async function classify() {
    setLoading(true);
    for (const id of selectedIds) {
      try { const r = await classifySupplier(id); onClassified({ id, ...r }); setStatus(`Classified: ${selectedIds.size}`); }
      catch { setStatus(`Failed on ${id}`); }
    }
    setLoading(false);
  }

  return (
    <Modal title="Classify Suppliers" onClose={onClose}>
      <div className="space-y-3">
        <p className="text-sm text-graphite">Run AI classifier on selected suppliers</p>
        <div className="max-h-64 space-y-1 overflow-y-auto">
          {suppliers.map((s) => (
            <label key={s.id} className="flex items-center gap-2 rounded-md p-2 text-sm hover:bg-slate-50">
              <input className="h-4 w-4" type="checkbox" checked={selectedIds.has(s.id)} onChange={() => toggle(s.id)} />
              <span className="font-medium text-ink">{s.name}</span>
              <span className="text-graphite">{s.company_type ?? "UNKNOWN"}</span>
            </label>
          ))}
        </div>
        {status && <div className="rounded-md bg-slate-50 p-2 text-sm text-graphite">{status}</div>}
        <button className="w-full rounded-md bg-mint px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" disabled={loading || selectedIds.size === 0} type="button" onClick={classify}>
          {loading ? "Classifying..." : `Classify ${selectedIds.size} selected`}
        </button>
      </div>
    </Modal>
  );
}

// ── Mark Task Completed Dialog ──

export function CompleteTaskDialog({ tasks, onClose, onCompleted }: {
  tasks: ManualTask[]; onClose: () => void;
  onCompleted: (taskId: string) => void;
}) {
  const [loading, setLoading] = useState<string | null>(null);

  async function complete(taskId: string) {
    setLoading(taskId);
    try { await markTaskCompleted(taskId); onCompleted(taskId); }
    finally { setLoading(null); }
  }

  return (
    <Modal title="Complete Tasks" onClose={onClose}>
      <div className="space-y-2">
        {tasks.filter((t) => t.status !== "completed").length === 0 && <p className="text-sm text-graphite">No open tasks.</p>}
        {tasks.filter((t) => t.status !== "completed").map((t) => (
          <div key={t.id} className="flex items-center justify-between rounded-md border border-slate-200 p-3">
            <div>
              <div className="text-sm font-medium text-ink">{t.title ?? t.task_type}</div>
              <div className="text-xs text-graphite">{t.status}</div>
            </div>
            <button className="rounded-md bg-mint px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50" disabled={loading === t.id} type="button" onClick={() => complete(t.id)}>
              {loading === t.id ? "..." : "Complete"}
            </button>
          </div>
        ))}
        <button className="w-full rounded-md border border-slate-300 bg-white px-4 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
