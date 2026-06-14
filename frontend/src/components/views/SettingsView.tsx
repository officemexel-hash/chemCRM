"use client";

import { useEffect, useState } from "react";
import type { AppSettings, ControlledQuestion, ConversationSimulation, ResponsePlaybookRule, SafetyOverrideState } from "@/types/api";
import { API_BASE_URL } from "@/lib/api";
import { Badge, TextField, TextArea } from "@/components/Widgets";

const defaultSettings: AppSettings = {
  company: { legal_name: "", trading_name: "", registration_number: "", vat_number: "", eori_number: "", website: "", address: "", country: "" },
  sender: { name: "", title: "", email: "", phone: "", department: "Procurement", signature: "" },
  default_destination_country: "", default_intended_use: "", default_incoterms: ["EXW", "FOB", "CIF", "DAP", "DDP"],
  controlled_questions: [], response_playbook: [], training_scenarios: [], require_human_approval_for_simulated_responses: true,
};

export function SettingsView() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [saveStatus, setSaveStatus] = useState("Not saved");
  const [supplierMessage, setSupplierMessage] = useState("We can quote USD 12/kg, MOQ 25 kg, but COA and SDS are not available before payment.");
  const [simulation, setSimulation] = useState<ConversationSimulation | null>(null);
  const [adminToken, setAdminToken] = useState("");
  const [overrideReason, setOverrideReason] = useState("Testing own local workflow behavior with mock-only sends.");
  const [overrideMinutes, setOverrideMinutes] = useState("60");
  const [safetyOverride, setSafetyOverride] = useState<SafetyOverrideState | null>(null);
  const [overrideStatus, setOverrideStatus] = useState("Admin token required");

  useEffect(() => {
    fetch(`${API_BASE_URL}/settings/app`)
      .then((r) => r.ok ? r.json() : defaultSettings)
      .then((p: AppSettings) => setSettings({ ...defaultSettings, ...p }))
      .catch(() => setSettings(defaultSettings));
  }, []);

  async function loadSafetyOverride(token = adminToken) {
    if (!token) { setOverrideStatus("Admin token required"); return; }
    const r = await fetch(`${API_BASE_URL}/safety-override`, { headers: { Authorization: `Bearer ${token}` } });
    if (!r.ok) { setOverrideStatus("Cannot load override state"); return; }
    setSafetyOverride(await r.json() as SafetyOverrideState); setOverrideStatus("Loaded");
  }

  async function save() {
    setSaveStatus("Saving");
    const r = await fetch(`${API_BASE_URL}/settings/app`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...settings, sender: { ...settings.sender, email: settings.sender.email || null } }) });
    if (!r.ok) { setSaveStatus("Save failed"); return; }
    setSettings({ ...defaultSettings, ...await r.json() as AppSettings }); setSaveStatus("Saved");
  }

  async function runSimulation() {
    const r = await fetch(`${API_BASE_URL}/conversation-simulator/simulate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ supplier_name: "Demo Supplier", supplier_message: supplierMessage, channel: "manual", stage: "training" }) });
    if (r.ok) setSimulation(await r.json() as ConversationSimulation);
  }

  async function updateSafety(enabled: boolean) {
    if (!adminToken) { setOverrideStatus("Admin token required"); return; }
    setOverrideStatus(enabled ? "Enabling" : "Disabling");
    const r = await fetch(`${API_BASE_URL}/safety-override`, { method: "PUT", headers: { Authorization: `Bearer ${adminToken}`, "Content-Type": "application/json" }, body: JSON.stringify({ enabled, reason: overrideReason, expires_in_minutes: Number.parseInt(overrideMinutes, 10) || 60, confirm_test_only: true }) });
    if (!r.ok) { setOverrideStatus("Override update failed"); return; }
    setSafetyOverride(await r.json() as SafetyOverrideState); setOverrideStatus(enabled ? "Override active" : "Override disabled");
  }

  function updateQ(index: number, patch: Partial<ControlledQuestion>) { const n = [...settings.controlled_questions]; n[index] = { ...n[index], ...patch }; setSettings({ ...settings, controlled_questions: n }); }
  function addQ() { setSettings({ ...settings, controlled_questions: [...settings.controlled_questions, { key: `question_${settings.controlled_questions.length + 1}`, category: "general", text: "", required: true, risk_weight: 0 }] }); }
  function updateR(index: number, patch: Partial<ResponsePlaybookRule>) { const n = [...settings.response_playbook]; n[index] = { ...n[index], ...patch }; setSettings({ ...settings, response_playbook: n }); }
  function addR() { setSettings({ ...settings, response_playbook: [...settings.response_playbook, { name: `Rule ${settings.response_playbook.length + 1}`, trigger_terms: [], supplier_intent: "unknown", recommended_action: "manual_review", response_template: "", creates_manual_task: true, block_if_matched: false }] }); }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Enterprise Settings</h2>
        <div className="flex items-center gap-2"><span className="text-sm text-graphite">{saveStatus}</span><button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={save}>Save</button></div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Company Identity</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Legal name" value={settings.company.legal_name} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, legal_name: v } })} />
            <TextField label="Trading name" value={settings.company.trading_name ?? ""} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, trading_name: v } })} />
            <TextField label="Registration number" value={settings.company.registration_number ?? ""} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, registration_number: v } })} />
            <TextField label="VAT number" value={settings.company.vat_number ?? ""} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, vat_number: v } })} />
            <TextField label="Website" value={settings.company.website ?? ""} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, website: v } })} />
            <TextField label="Country" value={settings.company.country ?? ""} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, country: v } })} />
          </div>
          <div className="mt-3 grid gap-2 text-sm text-graphite">
            <span>Company Logo</span>
            <input type="file" accept="image/*" onChange={async (e) => { const f = e.target.files?.[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); const r = await fetch(`${API_BASE_URL}/settings/app/logo`, { method: "POST", body: fd }); if (r.ok) { const d = await r.json(); setSettings({ ...settings, logo_url: d.logo_url }); } }} />
            {settings.logo_url && <div className="flex items-center gap-2"><img src={`${API_BASE_URL}${settings.logo_url}`} alt="Logo" className="h-10 rounded border" /><span className="text-xs text-graphite">{settings.logo_url}</span></div>}
          </div>
          <label className="mt-3 flex items-center gap-2 text-sm text-graphite">
            <input className="h-4 w-4" type="checkbox" checked={settings.pubchem_enabled ?? false} onChange={(e) => setSettings({ ...settings, pubchem_enabled: e.target.checked })} />
            Use real PubChem enrichment (requires internet)
          </label>
          <TextArea label="Address" value={settings.company.address ?? ""} onChange={(v) => setSettings({ ...settings, company: { ...settings.company, address: v } })} />
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Sender Persona</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Name" value={settings.sender.name} onChange={(v) => setSettings({ ...settings, sender: { ...settings.sender, name: v } })} />
            <TextField label="Title" value={settings.sender.title ?? ""} onChange={(v) => setSettings({ ...settings, sender: { ...settings.sender, title: v } })} />
            <TextField label="Email" value={settings.sender.email ?? ""} onChange={(v) => setSettings({ ...settings, sender: { ...settings.sender, email: v } })} />
            <TextField label="Phone" value={settings.sender.phone ?? ""} onChange={(v) => setSettings({ ...settings, sender: { ...settings.sender, phone: v } })} />
          </div>
          <TextArea label="Signature" value={settings.sender.signature ?? ""} onChange={(v) => setSettings({ ...settings, sender: { ...settings.sender, signature: v } })} />
        </section>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold text-ink">Controlled RFQ Questions</h3><button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={addQ}>Add question</button></div>
        <div className="grid gap-3">
          {settings.controlled_questions.map((q, i) => (
            <div key={`${q.key}-${i}`} className="grid gap-2 rounded-md bg-slate-50 p-3 md:grid-cols-[140px_140px_1fr_90px]">
              <TextField label="Key" value={q.key} onChange={(v) => updateQ(i, { key: v })} />
              <TextField label="Category" value={q.category} onChange={(v) => updateQ(i, { category: v })} />
              <TextArea label="Question" value={q.text} onChange={(v) => updateQ(i, { text: v })} compact />
              <label className="flex items-end gap-2 pb-2 text-sm text-graphite"><input checked={q.required} className="h-4 w-4" type="checkbox" onChange={(e) => updateQ(i, { required: e.target.checked })} />Required</label>
            </div>
          ))}
        </div>
      </section>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold text-ink">Response Playbook</h3><button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={addR}>Add rule</button></div>
        <div className="grid gap-3">
          {settings.response_playbook.map((r, i) => (
            <div key={`${r.name}-${i}`} className="grid gap-3 rounded-md bg-slate-50 p-3 xl:grid-cols-[1fr_1fr_1fr]">
              <TextField label="Rule name" value={r.name} onChange={(v) => updateR(i, { name: v })} />
              <TextField label="Recommended action" value={r.recommended_action} onChange={(v) => updateR(i, { recommended_action: v })} />
              <TextField label="Intent" value={r.supplier_intent} onChange={(v) => updateR(i, { supplier_intent: v })} />
              <TextArea compact label="Trigger terms, comma-separated" value={r.trigger_terms.join(", ")} onChange={(v) => updateR(i, { trigger_terms: v.split(",").map((x) => x.trim()).filter(Boolean) })} />
              <TextArea compact label="Response template" value={r.response_template} onChange={(v) => updateR(i, { response_template: v })} />
              <div className="flex items-end gap-4 pb-2 text-sm text-graphite">
                <label className="flex items-center gap-2"><input checked={r.creates_manual_task} className="h-4 w-4" type="checkbox" onChange={(e) => updateR(i, { creates_manual_task: e.target.checked })} />Manual task</label>
                <label className="flex items-center gap-2"><input checked={r.block_if_matched} className="h-4 w-4" type="checkbox" onChange={(e) => updateR(i, { block_if_matched: e.target.checked })} />Block</label>
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="mb-3 font-semibold text-ink">Conversation Simulator</h3>
        <TextArea label="Supplier message" value={supplierMessage} onChange={setSupplierMessage} />
        <button className="mt-3 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={runSimulation}>Simulate response</button>
        {simulation ? (
          <div className="mt-4 grid gap-3 xl:grid-cols-2">
            <div className="rounded-md bg-slate-50 p-3 text-sm">
              <div className="font-semibold text-ink">Recommended action: {simulation.recommended_action}</div>
              <div className="mt-1 text-graphite">Intent: {simulation.detected_intent}</div>
              <div className="mt-1 text-graphite">Missing: {simulation.missing_controlled_questions.join(", ") || "none"}</div>
              <div className="mt-1 text-graphite">Red flags: {simulation.red_flags.join(", ") || "none"}</div>
            </div>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-md bg-slate-950 p-3 text-xs text-white">{simulation.response_body}</pre>
          </div>
        ) : null}
      </section>
      <section className="rounded-md border border-red-200 bg-white p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div><h3 className="font-semibold text-ink">Test-Only Safety Override</h3><p className="mt-1 text-sm text-graphite">Requires admin bearer token. Never enables real external sends, portal login, CAPTCHA bypass, account registration, or fraud/evasion.</p></div>
          <Badge value={safetyOverride?.active ? "active" : "strict"} tone={safetyOverride?.active ? "warn" : "ok"} />
        </div>
        <div className="grid gap-3 xl:grid-cols-[1.4fr_1fr]">
          <div className="grid gap-3">
            <TextArea compact label="Admin bearer token" value={adminToken} onChange={setAdminToken} />
            <TextArea compact label="Reason" value={overrideReason} onChange={setOverrideReason} />
            <TextField label="TTL minutes" value={overrideMinutes} onChange={setOverrideMinutes} />
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => loadSafetyOverride()}>Load state</button>
              <button className="rounded-md bg-amber px-3 py-2 text-sm font-medium text-white hover:bg-amber-700" type="button" onClick={() => updateSafety(true)}>Enable test override</button>
              <button className="rounded-md bg-danger px-3 py-2 text-sm font-medium text-white hover:bg-red-700" type="button" onClick={() => updateSafety(false)}>Disable</button>
            </div>
            <p className="text-sm text-graphite">{overrideStatus}</p>
          </div>
          <div className="rounded-md bg-slate-50 p-3 text-sm text-graphite">
            <div className="font-semibold text-ink">State</div>
            <div>Mode: {safetyOverride?.mode ?? "unknown"}</div>
            <div>Enabled by: {safetyOverride?.enabled_by ?? "n/a"}</div>
            <div>Expires: {safetyOverride?.expires_at ?? "n/a"}</div>
            <div className="mt-3 font-semibold text-ink">Hard blocks</div>
            <div className="mt-1">{safetyOverride?.hard_blocks.join(", ") ?? "invalid CAS, fraud/evasion, real external send, portal/CAPTCHA bypass"}</div>
          </div>
        </div>
      </section>
    </section>
  );
}
