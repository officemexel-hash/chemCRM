"use client";

import {
  AlertTriangle,
  BarChart3,
  Beaker,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileText,
  Globe,
  Inbox,
  MailCheck,
  MessageSquareText,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Truck,
  Upload,
  Users
} from "lucide-react";
import type React from "react";
import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, loadDashboardData, uploadBulkImport, processBulkImport, enrichBulkImport, getBulkImportJob, getBulkImportItems, getSubstanceIntelligence, createManufacturingAnalysis, listManufacturingAnalyses, lookupHsCode, getDutyRate, getResponsibilityMatrix, getIncotermsForTransport, getLegalUses, getCustomsText, batchApproveMessages, listDocuments, downloadDocument, generateReport, getRanking, createCampaign, startDiscovery, markQuoteReviewed } from "@/lib/api";
import { AddSubstanceDialog, AddSupplierDialog, CreateCampaignDialog, GenerateRfqDialog, AutonomousRunDialog, EnrichSubstancesDialog, ClassifySuppliersDialog, CompleteTaskDialog } from "@/components/Dialogs";
import type {
  AppSettings,
  BatchApproveResponse,
  BulkImportItem,
  BulkImportJob,
  Campaign,
  ControlledQuestion,
  ConversationSimulation,
  CustomsDutyResponse,
  GeneratedDocumentMeta,
  HsCodeEntry,
  IncotermsGuide,
  LegalUseDescription,
  LetterOfIntentResponse,
  ManualTask,
  ManufacturingAnalysis,
  Message,
  PurchaseOrderResponse,
  QuoteComparisonRow,
  RankingRow,
  ResponsePlaybookRule,
  ResponsibilityMatrixRow,
  SafetyOverrideState,
  SubstanceAnalogsResponse,
  SourcingBatch,
  SourcingReport,
  Substance,
  SubstanceSourcingProfile,
  Supplier,
  TariffRate,
} from "@/types/api";

type DashboardData = {
  substances: Substance[];
  suppliers: Supplier[];
  campaigns: Campaign[];
  outboundMessages: Message[];
  inboundMessages: Message[];
  tasks: ManualTask[];
  comparison: QuoteComparisonRow[];
};

const emptyData: DashboardData = {
  substances: [],
  suppliers: [],
  campaigns: [],
  outboundMessages: [],
  inboundMessages: [],
  tasks: [],
  comparison: []
};

const tabs = [
  { id: "dashboard", label: "Dashboard", icon: ClipboardCheck },
  { id: "import", label: "Import CAS", icon: Upload },
  { id: "sourcing", label: "Sourcing", icon: FileText },
  { id: "intelligence", label: "Intelligence", icon: BarChart3 },
  { id: "documents", label: "Docs", icon: FileText },
  { id: "substances", label: "Substances", icon: Beaker },
  { id: "discovery", label: "Discovery", icon: Search },
  { id: "suppliers", label: "Suppliers", icon: Users },
  { id: "campaigns", label: "RFQ", icon: MessageSquareText },
  { id: "inbox", label: "Inbox", icon: Inbox },
  { id: "quotes", label: "Quotes", icon: Truck },
  { id: "tariff", label: "Tariff", icon: Globe },
  { id: "reports", label: "Reports", icon: BarChart3 },
  { id: "tasks", label: "Tasks", icon: AlertTriangle },
  { id: "settings", label: "Settings", icon: Settings }
] as const;

export function DashboardApp() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]["id"]>("dashboard");
  const [data, setData] = useState<DashboardData>(emptyData);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState<string | null>(null);

  const refresh = () => loadDashboardData().then(setData);

  useEffect(() => {
    refresh();
    setLoading(false);
  }, []);

  const riskAlerts = useMemo(
    () =>
      data.suppliers.filter((supplier) => ["high", "elevated", "unknown"].includes(String(supplier.risk_level))).length +
      data.substances.filter((substance) => substance.requires_manual_review).length,
    [data]
  );

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal text-ink">Chemical Sourcing RFQ CRM</h1>
            <p className="mt-1 text-sm text-graphite">Legal B2B procurement workflow with RFQ approval controls</p>
          </div>
          <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            <ShieldCheck size={16} />
            Policy engine active
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-5 px-5 py-5 lg:grid-cols-[220px_1fr]">
        <nav className="h-fit border-r border-slate-200 pr-0 lg:pr-4">
          <div className="grid gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex h-10 items-center gap-2 rounded-md px-3 text-left text-sm transition ${
                    active ? "bg-ink text-white" : "text-graphite hover:bg-white"
                  }`}
                  title={tab.label}
                >
                  <Icon size={17} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        <main className="min-w-0">
          {loading ? (
            <div className="flex h-40 items-center justify-center gap-2 text-graphite">
              <RefreshCw className="animate-spin" size={18} />
              Loading workspace data
            </div>
          ) : (
            <>
              {activeTab === "dashboard" && <DashboardView data={data} riskAlerts={riskAlerts} />}
              {activeTab === "import" && <BulkImportView />}
              {activeTab === "sourcing" && <SourcingView />}
              {activeTab === "intelligence" && <SubstanceIntelligenceView substances={data.substances} />}
              {activeTab === "documents" && <DocumentsView />}
              {activeTab === "substances" && <SubstancesView substances={data.substances} onDialog={setDialog} />}
              {activeTab === "discovery" && <DiscoveryView suppliers={data.suppliers} />}
              {activeTab === "suppliers" && <SuppliersView suppliers={data.suppliers} onDialog={setDialog} />}
              {activeTab === "campaigns" && <CampaignsView campaigns={data.campaigns} messages={data.outboundMessages} onDialog={setDialog} />}
              {activeTab === "inbox" && <InboxView inbound={data.inboundMessages} outbound={data.outboundMessages} />}
              {activeTab === "quotes" && <QuotesView rows={data.comparison} />}
              {activeTab === "tariff" && <TariffView substances={data.substances} />}
              {activeTab === "reports" && <ReportsView campaigns={data.campaigns} />}
              {activeTab === "tasks" && <TasksView tasks={data.tasks} onDialog={setDialog} />}
              {activeTab === "settings" && <SettingsView />}
            </>
          )}
        </main>
      </div>

      {dialog === "add-substance" && <AddSubstanceDialog onClose={() => setDialog(null)} onCreated={(s) => { setData((d) => ({ ...d, substances: [s, ...d.substances] })); }} />}
      {dialog === "add-supplier" && <AddSupplierDialog onClose={() => setDialog(null)} onCreated={(s) => { setData((d) => ({ ...d, suppliers: [s, ...d.suppliers] })); }} />}
      {dialog === "create-campaign" && <CreateCampaignDialog substances={data.substances} onClose={() => setDialog(null)} onCreated={(c) => { setData((d) => ({ ...d, campaigns: [c, ...d.campaigns] })); }} />}
      {dialog === "generate-rfq" && <GenerateRfqDialog campaigns={data.campaigns} suppliers={data.suppliers} onClose={() => setDialog(null)} onGenerated={(msg) => { setData((d) => ({ ...d, outboundMessages: [msg, ...d.outboundMessages] })); }} />}
      {dialog === "autonomous-run" && <AutonomousRunDialog campaigns={data.campaigns} onClose={() => setDialog(null)} onRan={() => refresh()} />}
      {dialog === "enrich-substances" && <EnrichSubstancesDialog substances={data.substances} onClose={() => setDialog(null)} onEnriched={(updated) => { setData((d) => ({ ...d, substances: d.substances.map((s) => s.id === updated.id ? updated : s) })); }} />}
      {dialog === "classify-suppliers" && <ClassifySuppliersDialog suppliers={data.suppliers} onClose={() => setDialog(null)} onClassified={(r) => { setData((d) => ({ ...d, suppliers: d.suppliers.map((s) => s.id === r.id ? { ...s, company_type: r.company_type, supplier_score: r.supplier_score, risk_score: r.risk_score, risk_level: r.risk_level } : s) })); }} />}
      {dialog === "complete-tasks" && <CompleteTaskDialog tasks={data.tasks} onClose={() => setDialog(null)} onCompleted={(id) => { setData((d) => ({ ...d, tasks: d.tasks.map((t) => t.id === id ? { ...t, status: "completed" } : t) })); }} />}
    </div>
  );
}

function DashboardView({ data, riskAlerts }: { data: DashboardData; riskAlerts: number }) {
  const bestQuote = data.comparison.find((row) => row.best_quote) ?? data.comparison[0];
  return (
    <section className="space-y-5">
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Stat label="Substances" value={data.substances.length} icon={<Beaker size={18} />} />
        <Stat label="Suppliers" value={data.suppliers.length} icon={<Users size={18} />} />
        <Stat label="Campaigns" value={data.campaigns.length} icon={<MessageSquareText size={18} />} />
        <Stat label="New replies" value={data.inboundMessages.length} icon={<Inbox size={18} />} />
        <Stat label="Quotes" value={data.comparison.length} icon={<FileText size={18} />} />
        <Stat label="Risk alerts" value={riskAlerts} icon={<AlertTriangle size={18} />} tone={riskAlerts ? "warn" : "ok"} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink">Active RFQ Messages</h2>
            <MailCheck size={18} className="text-mint" />
          </div>
          <MessageList messages={data.outboundMessages} />
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink">Best Quote</h2>
            <Truck size={18} className="text-mint" />
          </div>
          {bestQuote ? (
            <div className="grid gap-2 text-sm">
              <div className="text-lg font-semibold text-ink">{bestQuote.supplier}</div>
              <div className="text-2xl font-bold text-mint">
                {bestQuote.price} {bestQuote.currency}/{bestQuote.unit}
              </div>
              <div className="grid grid-cols-2 gap-2 text-graphite">
                <span>MOQ: {bestQuote.moq ?? "n/a"}</span>
                <span>Incoterms: {bestQuote.incoterms ?? "n/a"}</span>
                <span>Lead time: {bestQuote.lead_time ?? "n/a"}</span>
                <span>Risk: {bestQuote.risk_level ?? "n/a"}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-graphite">No parsed quotes yet.</p>
          )}
        </section>
      </div>
    </section>
  );
}

function BulkImportView() {
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<BulkImportJob | null>(null);
  const [items, setItems] = useState<BulkImportItem[]>([]);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");

  async function loadItems(jobId: string) {
    const loadedItems = await getBulkImportItems(jobId);
    setItems(loadedItems);
  }

  async function uploadFile() {
    if (!file) {
      setError("Choose a CSV/XLSX file first.");
      return;
    }
    setError("");
    setStatus("Uploading");
    try {
      const created = await uploadBulkImport(file);
      setJob(created);
      await loadItems(created.id);
      setStatus("Uploaded");
    } catch {
      setStatus("Upload failed");
      setError("The file could not be uploaded.");
    }
  }

  async function processJob() {
    if (!job?.id) return;
    setError("");
    setStatus("Processing");
    try {
      const processed = await processBulkImport(job.id);
      setJob(processed);
      await loadItems(processed.id);
      setStatus("Processed");
    } catch {
      setStatus("Processing failed");
      setError("The CAS rows could not be processed.");
    }
  }

  async function enrichJob() {
    if (!job?.id) return;
    setError("");
    setStatus("Enriching");
    try {
      await enrichBulkImport(job.id);
      const refreshed = await getBulkImportJob(job.id);
      setJob(refreshed);
      await loadItems(job.id);
      setStatus("Enriched");
    } catch {
      setStatus("Enrichment failed");
      setError("The imported substances could not be enriched.");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Bulk CAS Import</h2>
        <span className="text-sm text-graphite">{status}</span>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
          <input
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            type="file"
            accept=".csv,.tsv,.xlsx"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)}
          />
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={uploadFile}>
            Upload
          </button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={!job?.id} type="button" onClick={processJob}>
            Process
          </button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={!job?.id} type="button" onClick={enrichJob}>
            Enrich
          </button>
        </div>
        {error ? <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      </section>

      {job ? (
        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Rows" value={job.total_rows ?? 0} />
          <Metric label="Valid" value={job.valid_rows ?? 0} />
          <Metric label="Invalid" value={job.invalid_rows ?? 0} />
          <Metric label="Status" value={job.status ?? "unknown"} />
        </div>
      ) : null}

      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite">
            <tr>
              <th className="px-4 py-3">Row</th>
              <th className="px-4 py-3">CAS raw</th>
              <th className="px-4 py-3">Valid</th>
              <th className="px-4 py-3">Substance</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Error</th>
            </tr>
          </thead>
          <tbody>
            {items.length ? (
              items.map((item) => (
                <tr key={item.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{item.row_number}</td>
                  <td className="px-4 py-3 font-medium text-ink">{item.cas_raw}</td>
                  <td className="px-4 py-3">{item.cas_valid ? "yes" : "no"}</td>
                  <td className="px-4 py-3">{item.substance_id ?? "n/a"}</td>
                  <td className="px-4 py-3"><Badge value={item.status} /></td>
                  <td className="px-4 py-3 text-graphite">{item.error_message ?? ""}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-6 text-sm text-graphite" colSpan={6}>Upload a spreadsheet or CSV with CAS numbers to start a batch workflow.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </section>
  );
}

const sourcingChannels = [
  ["legal_search", "Legal search"],
  ["contact_form", "Contact forms"],
  ["alibaba_internal", "Alibaba"],
  ["made_in_china_internal", "Made-in-China"],
  ["molbase_internal", "Molbase"],
  ["indiamart_internal", "IndiaMART"],
  ["whatsapp_business", "WhatsApp Business"],
  ["telegram_bot", "Telegram Bot"],
  ["signal_manual", "Signal manual"],
  ["threema_gateway", "Threema Gateway"],
  ["wickr_manual", "Wickr manual"]
] as const;

function SourcingView() {
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

  function toggleChannel(channel: string) {
    setChannels((current) =>
      current.includes(channel) ? current.filter((item) => item !== channel) : [...current, channel]
    );
  }

  async function importBatch() {
    setStatus("Importing");
    setBatch(null);
    setReport(null);
    const response = await fetch(`${API_BASE_URL}/sourcing/batches`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: batchName,
        csv_text: csvText,
        quantity,
        destination_country: destinationCountry,
        required_grade: requiredGrade,
        intended_use: intendedUse,
        channels,
        create_campaigns: true,
        auto_send_enabled: false
      })
    });
    if (!response.ok) {
      setStatus("Import failed");
      return;
    }
    const created = (await response.json()) as SourcingBatch;
    setBatch(created);
    setStatus("Imported");

    const reportResponse = await fetch(`${API_BASE_URL}/sourcing/batches/${created.batch_id}/report`);
    if (reportResponse.ok) {
      setReport((await reportResponse.json()) as SourcingReport);
    }
  }

  const summary = batch?.summary;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Sourcing Batch</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-graphite">{status}</span>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={importBatch}>
            Import CAS
          </button>
        </div>
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
            {sourcingChannels.map(([value, label]) => (
              <label key={value} className="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-graphite">
                <input
                  checked={channels.includes(value)}
                  className="h-4 w-4"
                  type="checkbox"
                  onChange={() => toggleChannel(value)}
                />
                {label}
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

      {summary ? (
        <div className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
          <Metric label="Inputs" value={summary.total_inputs} />
          <Metric label="Valid" value={summary.valid} />
          <Metric label="Invalid" value={summary.invalid} />
          <Metric label="Duplicates" value={summary.duplicates} />
          <Metric label="Substances" value={summary.substances_created} />
          <Metric label="Campaigns" value={summary.campaigns_created} />
          <Metric label="Tasks" value={summary.manual_tasks_created} />
          <Metric label="Queries" value={summary.queries_generated} />
        </div>
      ) : null}

      {batch ? (
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <table className="w-full min-w-[940px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-graphite">
              <tr>
                <th className="px-4 py-3">CAS</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Campaign</th>
                <th className="px-4 py-3">Queries</th>
                <th className="px-4 py-3">Tasks</th>
                <th className="px-4 py-3">Notes</th>
              </tr>
            </thead>
            <tbody>
              {batch.items.map((item, index) => (
                <tr key={`${item.raw_cas}-${index}`} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-ink">{item.cas ?? item.raw_cas}</td>
                  <td className="px-4 py-3"><Badge value={item.status} tone={item.status === "ready" ? "ok" : "warn"} /></td>
                  <td className="px-4 py-3">{item.campaign_id ? item.campaign_id.slice(0, 8) : "n/a"}</td>
                  <td className="px-4 py-3">{item.queries.length}</td>
                  <td className="px-4 py-3">{item.tasks.length}</td>
                  <td className="px-4 py-3 text-graphite">{item.errors.join("; ") || item.tasks.map((task) => task.channel).filter(Boolean).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {report ? (
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Batch Report</h3>
          <div className="grid gap-3 md:grid-cols-4">
            <Metric label="Campaigns" value={report.campaign_ids.length} />
            <Metric label="Manual tasks" value={report.manual_task_ids.length} />
            <Metric label="Outbound" value={report.outbound_messages} />
            <Metric label="Quotes" value={report.quotes} />
          </div>
          <div className="mt-4 grid gap-2">
            {Object.entries(report.channel_plan).map(([channel, plan]) => (
              <div key={channel} className="rounded-md bg-slate-50 p-3 text-sm text-graphite">
                <span className="font-semibold text-ink">{channel.replaceAll("_", " ")}</span>: {plan}
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

function SubstanceIntelligenceView({ substances }: { substances: Substance[] }) {
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

  const selectedSubstance = substances.find((item) => item.id === selectedId);

  async function loadProfile(substanceId = selectedId) {
    if (!substanceId) return;
    setStatus("Loading intelligence");
    const loadedProfile = await getSubstanceIntelligence(substanceId);
    const loadedAnalyses = await listManufacturingAnalyses(substanceId);
    setProfile(loadedProfile);
    setAnalyses(loadedAnalyses);
    setAnalysis(loadedAnalyses[0] ?? null);
    setStatus(loadedProfile ? "Loaded" : "No profile data");
  }

  async function runAnalysis() {
    if (!selectedId) return;
    setStatus("Analyzing production cost model");
    try {
      const result = await createManufacturingAnalysis(selectedId, {
        target_quantity: targetQuantity,
        target_grade: targetGrade,
        intended_use: intendedUse,
        destination_country: destinationCountry,
        include_raw_material_sourcing: true,
        create_raw_material_tasks: createTasks,
        save_to_crm: true,
      });
      setAnalysis(result);
      setAnalyses([result, ...analyses.filter((item) => item.id !== result.id)]);
      setStatus("Analysis saved");
    } catch {
      setStatus("Analysis failed");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Substance Intelligence</h2>
          <p className="text-sm text-graphite">Supplier database, contact history, offer terms, Incoterms and production cost scoping.</p>
        </div>
        <span className="text-sm text-graphite">{status}</span>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto]">
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink"
            value={selectedId}
            onChange={(event) => {
              setSelectedId(event.target.value);
              setProfile(null);
              setAnalysis(null);
            }}
          >
            <option value="">Select substance</option>
            {substances.map((substance) => (
              <option key={substance.id} value={substance.id}>
                {substance.cas} - {substance.primary_name ?? "unknown"}
              </option>
            ))}
          </select>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50" disabled={!selectedId} type="button" onClick={() => loadProfile()}>
            Load Profile
          </button>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50" disabled={!selectedId} type="button" onClick={runAnalysis}>
            Analyze Cost
          </button>
        </div>
      </section>

      {selectedSubstance ? (
        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="CAS" value={selectedSubstance.cas} />
          <Metric label="Substance" value={selectedSubstance.primary_name ?? "unknown"} />
          <Metric label="Regulatory" value={selectedSubstance.regulatory_status ?? "unknown"} />
          <Metric label="Manual review" value={selectedSubstance.requires_manual_review ? "required" : "no"} />
        </div>
      ) : null}

      {profile ? (
        <>
          <div className="grid gap-3 md:grid-cols-5">
            <Metric label="Suppliers" value={profile.summary.supplier_count} />
            <Metric label="Contacts" value={profile.summary.contact_count} />
            <Metric label="Quotes" value={profile.summary.quote_count} />
            <Metric label="Offers" value={profile.summary.offer_count} />
            <Metric label="Best price" value={profile.summary.best_price ? `${profile.summary.best_price} ${profile.summary.best_price_currency ?? ""}/${profile.summary.best_price_unit ?? ""}` : "n/a"} />
          </div>

          {profile.open_questions.length ? (
            <section className="rounded-md border border-amber-200 bg-amber-50 p-4">
              <h3 className="mb-2 font-semibold text-ink">Open Questions</h3>
              <div className="grid gap-2">
                {profile.open_questions.map((question) => (
                  <div key={question} className="text-sm text-amber-900">{question}</div>
                ))}
              </div>
            </section>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <section className="rounded-md border border-slate-200 bg-white p-4">
              <h3 className="mb-3 font-semibold text-ink">Supplier Records</h3>
              <div className="grid gap-3">
                {profile.suppliers.length ? profile.suppliers.map((supplier) => (
                  <div key={supplier.id} className="rounded-md border border-slate-200 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="font-semibold text-ink">{supplier.name}</div>
                        <div className="text-sm text-graphite">{supplier.country ?? "unknown"} · {supplier.company_type ?? "UNKNOWN"} · risk {supplier.risk_level ?? "unknown"}</div>
                      </div>
                      <Badge value={`score ${supplier.supplier_score ?? 0}`} tone={Number(supplier.risk_score ?? 0) > 30 ? "warn" : "ok"} />
                    </div>
                    <div className="mt-3 grid gap-2 text-sm text-graphite">
                      <div><span className="font-medium text-ink">Contacts:</span> {supplier.contacts.map((contact) => `${contact.channel}: ${contact.value}`).join("; ") || "none"}</div>
                      <div><span className="font-medium text-ink">Packaging:</span> {supplier.quoted_packaging.join("; ") || "missing"}</div>
                      <div><span className="font-medium text-ink">Incoterms:</span> {supplier.quoted_incoterms.join(", ") || "missing"}</div>
                    </div>
                    {supplier.quotes.length ? (
                      <div className="mt-3 overflow-hidden rounded-md border border-slate-100">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 text-graphite">
                            <tr>
                              <th className="px-2 py-2">Price</th>
                              <th className="px-2 py-2">MOQ</th>
                              <th className="px-2 py-2">Incoterms</th>
                              <th className="px-2 py-2">Transport</th>
                              <th className="px-2 py-2">Packaging</th>
                              <th className="px-2 py-2">Lead time</th>
                            </tr>
                          </thead>
                          <tbody>
                            {supplier.quotes.map((quote) => (
                              <tr key={quote.id} className="border-t border-slate-100">
                                <td className="px-2 py-2">{quote.price ?? "n/a"} {quote.currency ?? ""}/{quote.unit ?? ""}</td>
                                <td className="px-2 py-2">{quote.moq ?? "n/a"}</td>
                                <td className="px-2 py-2">{quote.incoterms ?? "n/a"}</td>
                                <td className="px-2 py-2">{quote.transport_mode ?? "n/a"}</td>
                                <td className="px-2 py-2">{quote.packaging ?? "n/a"}</td>
                                <td className="px-2 py-2">{quote.lead_time ?? "n/a"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                    {supplier.contact_history.length ? (
                      <div className="mt-3 grid gap-2">
                        {supplier.contact_history.slice(0, 3).map((item) => (
                          <div key={item.id} className="rounded-md bg-slate-50 p-2 text-xs text-graphite">
                            <span className="font-medium text-ink">{item.direction}</span> · {item.channel ?? "channel"} · {item.status ?? "status"} · {item.subject ?? "no subject"}
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                )) : <p className="text-sm text-graphite">No suppliers are linked to this substance yet.</p>}
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-4">
              <h3 className="mb-3 font-semibold text-ink">Incoterms By Transport</h3>
              <div className="grid gap-2">
                {profile.incoterms_by_transport.map((item) => (
                  <div key={item.transport_mode} className="rounded-md bg-slate-50 p-3 text-sm">
                    <div className="font-semibold text-ink">{item.transport_mode}</div>
                    <div className="mt-1 text-graphite">{item.recommended_incoterms.join(", ")}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </>
      ) : (
        <section className="rounded-md border border-slate-200 bg-white p-4 text-sm text-graphite">
          Load a substance profile to build the substance-centered supplier and quote database.
        </section>
      )}

      <div className="grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">Production Cost Scoping</h3>
          <TextField label="Target quantity" value={targetQuantity} onChange={setTargetQuantity} />
          <TextField label="Target grade" value={targetGrade} onChange={setTargetGrade} />
          <TextField label="Destination country" value={destinationCountry} onChange={setDestinationCountry} />
          <TextArea label="Intended lawful use" value={intendedUse} onChange={setIntendedUse} compact />
          <label className="mt-3 flex items-center gap-2 text-sm text-graphite">
            <input checked={createTasks} type="checkbox" onChange={(event) => setCreateTasks(event.target.checked)} />
            Create manual tasks for input material sourcing queries
          </label>
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold text-ink">Latest Analysis</h3>
            <Badge value={analysis?.status ?? "not generated"} tone={analysis?.blocked_reasons?.length ? "warn" : "ok"} />
          </div>
          {analysis ? (
            <div className="grid gap-3 text-sm text-graphite">
              {analysis.process_overview ? <p>{analysis.process_overview}</p> : null}
              {analysis.blocked_reasons.length ? (
                <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-amber-900">
                  {analysis.blocked_reasons.join("; ")}
                </div>
              ) : null}
              <div className="grid gap-2 md:grid-cols-2">
                <InfoList title="Equipment classes" items={analysis.required_equipment} primaryKey="category" secondaryKey="examples" />
                <InfoList title="Input materials" items={analysis.input_materials} primaryKey="name" secondaryKey="role" />
                <InfoList title="Cost drivers" items={analysis.cost_drivers} primaryKey="name" secondaryKey="impact" />
                <InfoList title="Sourcing queries" items={analysis.sourcing_queries} primaryKey="material" secondaryKey="query" />
              </div>
              {analysis.safety_notes.length ? (
                <div className="rounded-md bg-slate-50 p-3 text-xs">
                  {analysis.safety_notes.join(" ")}
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-graphite">Run analysis to create a safe manufacturing feasibility and input-material cost model.</p>
          )}
          {analyses.length > 1 ? (
            <div className="mt-3 text-xs text-graphite">Saved analyses: {analyses.length}</div>
          ) : null}
        </section>
      </div>
    </section>
  );
}

const transportModes = ["sea", "air", "road", "rail", "courier", "multimodal"];
const incotermsOptions = ["EXW", "FCA", "FOB", "CIF", "CFR", "FAS", "CPT", "CIP", "DAP", "DDP"];

function DocumentsView() {
  const [supplierName, setSupplierName] = useState("Demo Supplier Ltd");
  const [supplierAddress, setSupplierAddress] = useState("Supplier address");
  const [supplierContact, setSupplierContact] = useState("Sales team");
  const [recipientName, setRecipientName] = useState("Sales team");
  const [substanceName, setSubstanceName] = useState("Ethanol");
  const [substanceCas, setSubstanceCas] = useState("64-17-5");
  const [quantity, setQuantity] = useState("100");
  const [unit, setUnit] = useState("kg");
  const [pricePerUnit, setPricePerUnit] = useState("12.50");
  const [currency, setCurrency] = useState("USD");
  const [destinationCountry, setDestinationCountry] = useState("PL");
  const [originCountry, setOriginCountry] = useState("CN");
  const [intendedUse, setIntendedUse] = useState("Industrial solvent for coatings validation.");
  const [transportMode, setTransportMode] = useState("sea");
  const [incoterms, setIncoterms] = useState("CIF");
  const [deliveryAddress, setDeliveryAddress] = useState("Warsaw, Poland");
  const [paymentTerms, setPaymentTerms] = useState("T/T 30% advance, 70% against shipping documents");
  const [specialRequirements, setSpecialRequirements] = useState("COA, SDS/MSDS, specification sheet and compliant invoice required before shipment.");
  const [hsCode, setHsCode] = useState("");
  const [customsDutyRate, setCustomsDutyRate] = useState("");
  const [legalUseDescription, setLegalUseDescription] = useState("");
  const [customs, setCustoms] = useState<CustomsDutyResponse | null>(null);
  const [analogs, setAnalogs] = useState<SubstanceAnalogsResponse | null>(null);
  const [incotermsGuide, setIncotermsGuide] = useState<IncotermsGuide | null>(null);
  const [loi, setLoi] = useState<LetterOfIntentResponse | null>(null);
  const [po, setPo] = useState<PurchaseOrderResponse | null>(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [status, setStatus] = useState("Ready");

  useEffect(() => {
    fetch(`${API_BASE_URL}/documents/incoterms-guide?transport_mode=${encodeURIComponent(transportMode)}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: IncotermsGuide | null) => {
        if (payload) {
          setIncotermsGuide(payload);
          if (!payload.available_incoterms.includes(incoterms)) {
            setIncoterms(payload.available_incoterms[0] ?? "FCA");
          }
        }
      })
      .catch(() => setIncotermsGuide(null));
  }, [transportMode]);

  async function lookupCustoms() {
    setStatus("Looking up customs");
    const response = await fetch(`${API_BASE_URL}/documents/customs-duty`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cas: substanceCas,
        substance_name: substanceName,
        hs_code: hsCode,
        origin_country: originCountry,
        destination_country: destinationCountry
      })
    });
    if (!response.ok) {
      setStatus("Customs lookup failed");
      return;
    }
    const payload = (await response.json()) as CustomsDutyResponse;
    setCustoms(payload);
    setHsCode(payload.hs_code === "unknown" ? "" : payload.hs_code);
    setCustomsDutyRate(payload.duty_rate);
    setLegalUseDescription(payload.legal_uses[0] ?? "");
    setStatus("Customs estimate loaded");
  }

  async function findAnalogs() {
    setStatus("Finding analogs");
    const response = await fetch(`${API_BASE_URL}/documents/substance-analogs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cas: substanceCas,
        primary_name: substanceName,
        target_application: intendedUse
      })
    });
    if (!response.ok) {
      setStatus("Analog lookup failed");
      return;
    }
    setAnalogs((await response.json()) as SubstanceAnalogsResponse);
    setStatus("Analogs loaded");
  }

  async function generateLoi() {
    setStatus("Generating LOI");
    const response = await fetch(`${API_BASE_URL}/documents/letter-of-intent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient_name: recipientName,
        recipient_company: supplierName,
        substance_name: substanceName,
        substance_cas: substanceCas,
        quantity: `${quantity} ${unit}`,
        intended_use: intendedUse,
        destination_country: destinationCountry,
        save_to_crm: true
      })
    });
    if (!response.ok) {
      setStatus("LOI generation failed");
      return;
    }
    const payload = (await response.json()) as LetterOfIntentResponse;
    setLoi(payload);
    setPreviewHtml(payload.html);
    setStatus("LOI generated");
  }

  async function generatePo() {
    setStatus("Generating PO");
    const response = await fetch(`${API_BASE_URL}/documents/purchase-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        supplier_name: supplierName,
        supplier_address: supplierAddress,
        supplier_contact: supplierContact,
        substance_name: substanceName,
        substance_cas: substanceCas,
        quantity,
        unit,
        price_per_unit: pricePerUnit,
        currency,
        incoterms,
        transport_mode: transportMode,
        payment_terms: paymentTerms,
        delivery_address: deliveryAddress,
        special_requirements: specialRequirements,
        hs_code: hsCode,
        customs_duty_rate: customsDutyRate,
        legal_use_description: legalUseDescription,
        save_to_crm: true
      })
    });
    if (!response.ok) {
      setStatus("PO generation failed");
      return;
    }
    const payload = (await response.json()) as PurchaseOrderResponse;
    setPo(payload);
    setPreviewHtml(payload.html);
    setStatus("PO generated");
  }

  async function downloadGeneratedDocument(documentId: string, fallbackName: string) {
    setStatus("Preparing download");
    try {
      const blob = await downloadDocument(documentId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${fallbackName}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setStatus("Download ready");
    } catch {
      setStatus("Download failed");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Documents, Customs, Analogs</h2>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-graphite">{status}</span>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={lookupCustoms}>
            Customs
          </button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={findAnalogs}>
            Analogs
          </button>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={generateLoi}>
            LOI
          </button>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={generatePo}>
            PO
          </button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_0.95fr]">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">Order Data</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Supplier" value={supplierName} onChange={setSupplierName} />
            <TextField label="Supplier contact" value={supplierContact} onChange={setSupplierContact} />
            <TextField label="Recipient name" value={recipientName} onChange={setRecipientName} />
            <TextField label="Substance" value={substanceName} onChange={setSubstanceName} />
            <TextField label="CAS" value={substanceCas} onChange={setSubstanceCas} />
            <TextField label="Quantity" value={quantity} onChange={setQuantity} />
            <TextField label="Unit" value={unit} onChange={setUnit} />
            <TextField label="Price per unit" value={pricePerUnit} onChange={setPricePerUnit} />
            <TextField label="Currency" value={currency} onChange={setCurrency} />
            <TextField label="Origin country" value={originCountry} onChange={setOriginCountry} />
            <TextField label="Destination country" value={destinationCountry} onChange={setDestinationCountry} />
            <TextField label="HS code" value={hsCode} onChange={setHsCode} />
            <SelectField label="Transport" value={transportMode} options={transportModes} onChange={setTransportMode} />
            <SelectField label="Incoterms" value={incoterms} options={incotermsGuide?.available_incoterms ?? incotermsOptions} onChange={setIncoterms} />
          </div>
          <TextArea label="Supplier address" value={supplierAddress} onChange={setSupplierAddress} compact />
          <TextArea label="Delivery address" value={deliveryAddress} onChange={setDeliveryAddress} compact />
          <TextArea label="Intended lawful use" value={intendedUse} onChange={setIntendedUse} compact />
          <TextArea label="Payment terms" value={paymentTerms} onChange={setPaymentTerms} compact />
          <TextArea label="Special requirements" value={specialRequirements} onChange={setSpecialRequirements} compact />
          <TextArea label="Customs duty estimate" value={customsDutyRate} onChange={setCustomsDutyRate} compact />
          <TextArea label="Legal use description for review" value={legalUseDescription} onChange={setLegalUseDescription} compact />
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Document Preview</h3>
          <div className="mb-3 grid gap-2 md:grid-cols-2">
            <Metric label="LOI" value={loi?.generated_document_id ? "saved" : loi ? "generated" : "none"} />
            <Metric label="PO" value={po?.generated_document_id ? "saved" : po ? "generated" : "none"} />
          </div>
          <div className="mb-3 flex flex-wrap gap-2">
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!loi?.generated_document_id}
              type="button"
              onClick={() => loi?.generated_document_id && downloadGeneratedDocument(loi.generated_document_id, "letter-of-intent")}
            >
              <Download className="h-4 w-4" />
              Download LOI
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!po?.generated_document_id}
              type="button"
              onClick={() => po?.generated_document_id && downloadGeneratedDocument(po.generated_document_id, po.po_number || "purchase-order")}
            >
              <Download className="h-4 w-4" />
              Download PO
            </button>
          </div>
          {previewHtml ? (
            <iframe className="h-[560px] w-full rounded-md border border-slate-200 bg-white" srcDoc={previewHtml} title="Document preview" />
          ) : (
            <p className="text-sm text-graphite">Generate LOI or PO to preview letterhead document.</p>
          )}
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Customs</h3>
          {customs ? (
            <div className="grid gap-2 text-sm text-graphite">
              <div><span className="font-semibold text-ink">HS:</span> {customs.hs_code}</div>
              <div><span className="font-semibold text-ink">Duty:</span> {customs.duty_rate}</div>
              <div><span className="font-semibold text-ink">VAT:</span> {customs.vat_rate}</div>
              <div><span className="font-semibold text-ink">Confidence:</span> {customs.confidence}</div>
              <div><span className="font-semibold text-ink">Review:</span> {customs.manual_review_required ? "required" : "not required"}</div>
              <div>{customs.hs_code_description}</div>
              {customs.source_url ? <a className="text-mint underline" href={customs.source_url} target="_blank">Official source</a> : null}
            </div>
          ) : (
            <p className="text-sm text-graphite">Run customs lookup to populate HS, duty and legal uses.</p>
          )}
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Legal Uses</h3>
          {customs?.legal_uses.length ? (
            <div className="grid gap-2">
              {customs.legal_uses.map((use) => (
                <div key={use} className="rounded-md bg-slate-50 p-2 text-sm text-graphite">{use}</div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-graphite">No legal-use suggestions loaded.</p>
          )}
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Analogs</h3>
          {analogs?.analogs.length ? (
            <div className="grid gap-2">
              {analogs.analogs.map((analog) => (
                <div key={analog.cas} className="rounded-md bg-slate-50 p-3 text-sm">
                  <div className="font-semibold text-ink">{analog.name} / {analog.cas}</div>
                  <div className="mt-1 text-graphite">{analog.price_indication}</div>
                  <div className="mt-1 text-graphite">{analog.functional_similarity}</div>
                  <div className="mt-1 text-xs text-graphite">{analog.similarity_basis.join(", ")}</div>
                </div>
              ))}
              <p className="text-sm text-graphite">{analogs.recommendation}</p>
            </div>
          ) : (
            <p className="text-sm text-graphite">Run analog lookup to see substitutes.</p>
          )}
        </section>
      </div>
    </section>
  );
}

function SubstancesView({ substances, onDialog }: { substances: Substance[]; onDialog: (d: string) => void }) {
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
              <th className="px-4 py-3">CAS</th>
              <th className="px-4 py-3">Primary name</th>
              <th className="px-4 py-3">PubChem</th>
              <th className="px-4 py-3">Formula</th>
              <th className="px-4 py-3">Regulatory</th>
              <th className="px-4 py-3">Manual review</th>
            </tr>
          </thead>
          <tbody>
            {substances.map((item) => (
              <tr key={item.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-ink">{item.cas}</td>
                <td className="px-4 py-3">{item.primary_name ?? "unknown"}</td>
                <td className="px-4 py-3">{item.pubchem_cid ?? "n/a"}</td>
                <td className="px-4 py-3">{item.molecular_formula ?? "n/a"}</td>
                <td className="px-4 py-3"><Badge value={item.regulatory_status ?? "unknown"} /></td>
                <td className="px-4 py-3">{item.requires_manual_review ? "required" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DiscoveryView({ suppliers }: { suppliers: Supplier[] }) {
  const [running, setRunning] = useState(false);
  async function run() { setRunning(true); try { await startDiscovery(); } finally { setRunning(false); } }
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Discovery Results</h2>
        <div className="flex gap-2">
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" type="button" onClick={run} disabled={running}>{running ? "Running..." : "Start Discovery"}</button>
        </div>
      </div>
      <div className="grid gap-3">
        {suppliers.map((supplier) => (
          <div key={supplier.id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-ink">{supplier.name}</h2>
                <p className="text-sm text-graphite">{supplier.website ?? "No website"} · {supplier.country ?? "unknown country"}</p>
              </div>
              <div className="flex gap-2">
                <Badge value={supplier.company_type ?? "UNKNOWN"} />
                <Badge value={`risk ${supplier.risk_score}`} tone={Number(supplier.risk_score) > 30 ? "warn" : "ok"} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function SuppliersView({ suppliers, onDialog }: { suppliers: Supplier[]; onDialog: (d: string) => void }) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Suppliers</h2>
        <div className="flex gap-2">
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => onDialog("classify-suppliers")}>Classify</button>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={() => onDialog("add-supplier")}>Add Supplier</button>
        </div>
      </div>
      <div className="grid gap-3 xl:grid-cols-2">
        {suppliers.map((supplier) => (
          <div key={supplier.id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold text-ink">{supplier.name}</h2>
                <p className="text-sm text-graphite">{supplier.country ?? "unknown"} · {supplier.company_type ?? "UNKNOWN"}</p>
              </div>
              <Badge value={supplier.risk_level ?? "unknown"} tone={supplier.risk_level === "low" ? "ok" : "warn"} />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
              <Metric label="Supplier score" value={supplier.supplier_score} />
              <Metric label="Risk score" value={supplier.risk_score} />
              <Metric label="Contacts" value={supplier.contacts?.length ?? 0} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CampaignsView({ campaigns, messages, onDialog }: { campaigns: Campaign[]; messages: Message[]; onDialog: (d: string) => void }) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">RFQ Campaigns</h2>
        <div className="flex gap-2">
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => onDialog("generate-rfq")}>Generate RFQ</button>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={() => onDialog("autonomous-run")}>Autonomous Run</button>
        </div>
      </div>
      <div className="grid gap-4">
        {campaigns.map((campaign) => (
          <div key={campaign.id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-ink">{campaign.quantity ?? "Quantity TBD"} · {campaign.destination_country ?? "Destination TBD"}</h2>
                <p className="text-sm text-graphite">{campaign.required_grade ?? "Grade TBD"} · {campaign.intended_use ?? "Intended use required"}</p>
              </div>
              <Badge value={campaign.auto_send_enabled ? "auto-send enabled" : "approval first"} tone={campaign.auto_send_enabled ? "ok" : "warn"} />
            </div>
            <p className="mt-3 text-sm text-graphite">
              Autonomous mode sends only policy-approved low-risk email/form RFQs. Marketplace/internal messenger items become manual approval tasks.
            </p>
            <div className="mt-4">
              <MessageList messages={messages.filter((message) => message.campaign_id === campaign.id || campaign.id.startsWith("demo"))} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function InboxView({ inbound, outbound }: { inbound: Message[]; outbound: Message[] }) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Inbox</h2>
        <span className="text-sm text-graphite">{inbound.length} inbound · {outbound.length} outbound</span>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h2 className="mb-3 font-semibold text-ink">Inbound</h2>
          <MessageList messages={inbound} empty="No inbound messages yet." />
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h2 className="mb-3 font-semibold text-ink">Outbound Queue</h2>
          <MessageList messages={outbound} />
        </section>
      </div>
    </section>
  );
}

function QuotesView({ rows }: { rows: QuoteComparisonRow[] }) {
  const [reviewing, setReviewing] = useState<string | null>(null);
  async function review(quoteId: string) { setReviewing(quoteId); try { await markQuoteReviewed(quoteId); } finally { setReviewing(null); } }
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Quote Comparison</h2>
        <div className="flex gap-2">
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={() => rows[0] && review(rows[0].quote_id)} disabled={reviewing !== null}>{reviewing ? "Reviewing..." : "Mark reviewed"}</button>
        </div>
      </div>
      <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite">
            <tr>
              <th className="px-4 py-3">Supplier</th>
              <th className="px-4 py-3">Price/kg</th>
              <th className="px-4 py-3">MOQ</th>
              <th className="px-4 py-3">Incoterms</th>
              <th className="px-4 py-3">Lead time</th>
              <th className="px-4 py-3">Docs</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.quote_id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-ink">
                  {row.best_quote && <CheckCircle2 className="mr-2 inline text-mint" size={16} />}
                  {row.supplier}
                </td>
                <td className="px-4 py-3">{row.price ?? "n/a"} {row.currency}/{row.unit}</td>
                <td className="px-4 py-3">{row.moq ?? "n/a"}</td>
                <td className="px-4 py-3">{row.incoterms ?? "n/a"}</td>
                <td className="px-4 py-3">{row.lead_time ?? "n/a"}</td>
                <td className="px-4 py-3">{row.coa_available ? "COA" : "no COA"} / {row.sds_available ? "SDS" : "no SDS"}</td>
                <td className="px-4 py-3"><Badge value={row.risk_level ?? "unknown"} tone={row.risk_level === "low" ? "ok" : "warn"} /></td>
                <td className="px-4 py-3">{row.confidence ?? "n/a"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function TariffView({ substances }: { substances: Substance[] }) {
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

  async function runTariffLookup() {
    setStatus("Looking up tariff data");
    const entries = await lookupHsCode(cas, selectedSubstanceId || undefined);
    setHsEntries(entries);
    const hsCode = entries[0]?.hs_code ?? selectedHsCode;
    setSelectedHsCode(hsCode);

    if (hsCode) {
      const loadedDuty = await getDutyRate(hsCode, origin, destination);
      setDuty(loadedDuty);
      if (selectedSubstanceId) {
        const [uses, text] = await Promise.all([
          getLegalUses(selectedSubstanceId, destination),
          getCustomsText(selectedSubstanceId, hsCode, destination)
        ]);
        setLegalUses(uses);
        setCustomsText(text.declaration_text);
      }
    }
    setStatus("Loaded");
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Tariff And Customs Screening</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-graphite">{status}</span>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={runTariffLookup}>
            Lookup
          </button>
        </div>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="grid gap-1 text-sm text-graphite">
            Substance
            <select
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink"
              value={selectedSubstanceId}
              onChange={(event) => {
                const value = event.target.value;
                setSelectedSubstanceId(value);
                const selected = substances.find((item) => item.id === value);
                if (selected?.cas) setCas(selected.cas);
              }}
            >
              <option value="">Manual CAS</option>
              {substances.map((substance) => (
                <option key={substance.id} value={substance.id}>{substance.cas} - {substance.primary_name ?? "unknown"}</option>
              ))}
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
            {hsEntries.length ? hsEntries.map((entry) => (
              <button
                key={entry.id}
                className={`rounded-md border p-3 text-left text-sm ${selectedHsCode === entry.hs_code ? "border-mint bg-emerald-50" : "border-slate-200 bg-white"}`}
                type="button"
                onClick={() => setSelectedHsCode(entry.hs_code)}
              >
                <div className="font-semibold text-ink">{entry.hs_code}</div>
                <div className="text-graphite">{entry.description ?? "No description"}</div>
                <div className="mt-1 text-xs text-graphite">Source: {entry.source_database} | Confidence: {entry.confidence ?? "n/a"}</div>
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
          {legalUses.length ? legalUses.map((use) => (
            <div key={use.id} className="rounded-md bg-slate-50 p-3 text-sm text-graphite">
              <div className="font-medium text-ink">{use.category ?? "use case"}</div>
              {use.description}
            </div>
          )) : <p className="text-sm text-graphite">Legal-use drafts appear after a substance lookup.</p>}
        </div>
      </section>
    </section>
  );
}

function ReportsView({ campaigns }: { campaigns: Campaign[] }) {
  const [campaignId, setCampaignId] = useState(campaigns[0]?.id ?? "");
  const [ranking, setRanking] = useState<RankingRow[]>([]);
  const [generated, setGenerated] = useState<GeneratedDocumentMeta | null>(null);
  const [status, setStatus] = useState("Ready");

  async function loadRanking() {
    if (!campaignId) return;
    setStatus("Loading ranking");
    setRanking(await getRanking(campaignId));
    setStatus("Ranking loaded");
  }

  async function createReport() {
    if (!campaignId) return;
    setStatus("Generating report");
    try {
      const document = await generateReport(campaignId, "pdf");
      setGenerated(document);
      setStatus("Report generated");
    } catch {
      setStatus("Report failed");
    }
  }

  async function downloadReport() {
    if (!generated?.id) return;
    setStatus("Preparing download");
    try {
      const blob = await downloadDocument(generated.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `rfq-report-${generated.id}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setStatus("Download ready");
    } catch {
      setStatus("Download failed");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Reports</h2>
        <span className="text-sm text-graphite">{status}</span>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
          <select className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink" value={campaignId} onChange={(event) => setCampaignId(event.target.value)}>
            <option value="">Select campaign</option>
            {campaigns.map((campaign) => (
              <option key={campaign.id} value={campaign.id}>{campaign.quantity ?? "Quantity TBD"} - {campaign.destination_country ?? "Destination TBD"}</option>
            ))}
          </select>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={!campaignId} type="button" onClick={loadRanking}>
            Load ranking
          </button>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50" disabled={!campaignId} type="button" onClick={createReport}>
            Generate PDF
          </button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={!generated?.id} type="button" onClick={downloadReport}>
            Download
          </button>
        </div>
      </section>

      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-graphite">
            <tr>
              <th className="px-4 py-3">Rank</th>
              <th className="px-4 py-3">Supplier</th>
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Recommendation</th>
            </tr>
          </thead>
          <tbody>
            {ranking.length ? ranking.map((row) => (
              <tr key={row.quote_id} className="border-t border-slate-100">
                <td className="px-4 py-3">{row.rank}</td>
                <td className="px-4 py-3 font-medium text-ink">{row.supplier_name}</td>
                <td className="px-4 py-3">{row.total_score}</td>
                <td className="px-4 py-3">{row.price ?? "n/a"} {row.currency ?? ""}</td>
                <td className="px-4 py-3">{row.risk_score}</td>
                <td className="px-4 py-3"><Badge value={row.recommended ? "recommended" : "review"} tone={row.recommended ? "ok" : "warn"} /></td>
              </tr>
            )) : (
              <tr>
                <td className="px-4 py-6 text-sm text-graphite" colSpan={6}>Load a campaign ranking to generate procurement reports.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </section>
  );
}

function TasksView({ tasks, onDialog }: { tasks: ManualTask[]; onDialog: (d: string) => void }) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Manual Tasks</h2>
        <div className="flex gap-2">
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={() => onDialog("complete-tasks")}>Complete</button>
        </div>
      </div>
      <div className="grid gap-3">
        {tasks.map((task) => (
          <div key={task.id} className="flex items-center justify-between rounded-md border border-slate-200 bg-white p-4">
            <div>
              <h2 className="font-semibold text-ink">{task.title ?? task.task_type ?? "Manual task"}</h2>
              <p className="text-sm text-graphite">{task.related_object_type ?? "workflow"} · {task.task_type ?? "review"}</p>
            </div>
            <Badge value={task.status ?? "open"} tone={task.status === "completed" ? "ok" : "warn"} />
          </div>
        ))}
      </div>
    </section>
  );
}

const defaultSettings: AppSettings = {
  company: {
    legal_name: "",
    trading_name: "",
    registration_number: "",
    vat_number: "",
    eori_number: "",
    website: "",
    address: "",
    country: ""
  },
  sender: {
    name: "",
    title: "",
    email: "",
    phone: "",
    department: "Procurement",
    signature: ""
  },
  default_destination_country: "",
  default_intended_use: "",
  default_incoterms: ["EXW", "FOB", "CIF", "DAP", "DDP"],
  controlled_questions: [],
  response_playbook: [],
  training_scenarios: [],
  require_human_approval_for_simulated_responses: true
};

function SettingsView() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [saveStatus, setSaveStatus] = useState("Not saved");
  const [supplierMessage, setSupplierMessage] = useState(
    "We can quote USD 12/kg, MOQ 25 kg, but COA and SDS are not available before payment."
  );
  const [simulation, setSimulation] = useState<ConversationSimulation | null>(null);
  const [adminToken, setAdminToken] = useState("");
  const [overrideReason, setOverrideReason] = useState("Testing own local workflow behavior with mock-only sends.");
  const [overrideMinutes, setOverrideMinutes] = useState("60");
  const [safetyOverride, setSafetyOverride] = useState<SafetyOverrideState | null>(null);
  const [overrideStatus, setOverrideStatus] = useState("Admin token required");

  useEffect(() => {
    fetch(`${API_BASE_URL}/settings/app`)
      .then((response) => (response.ok ? response.json() : defaultSettings))
      .then((payload: AppSettings) => setSettings({ ...defaultSettings, ...payload }))
      .catch(() => setSettings(defaultSettings));
  }, []);

  async function loadSafetyOverride(token = adminToken) {
    if (!token) {
      setOverrideStatus("Admin token required");
      return;
    }
    const response = await fetch(`${API_BASE_URL}/safety-override`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!response.ok) {
      setOverrideStatus("Cannot load override state");
      return;
    }
    setSafetyOverride((await response.json()) as SafetyOverrideState);
    setOverrideStatus("Loaded");
  }

  async function saveSettings() {
    setSaveStatus("Saving");
    const payload: AppSettings = {
      ...settings,
      sender: {
        ...settings.sender,
        email: settings.sender.email || null
      }
    };
    const response = await fetch(`${API_BASE_URL}/settings/app`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      setSaveStatus("Save failed");
      return;
    }
    const saved = (await response.json()) as AppSettings;
    setSettings({ ...defaultSettings, ...saved });
    setSaveStatus("Saved");
  }

  async function runSimulation() {
    const response = await fetch(`${API_BASE_URL}/conversation-simulator/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        supplier_name: "Demo Supplier",
        supplier_message: supplierMessage,
        channel: "manual",
        stage: "training"
      })
    });
    if (response.ok) {
      setSimulation((await response.json()) as ConversationSimulation);
    }
  }

  async function updateSafetyOverride(enabled: boolean) {
    if (!adminToken) {
      setOverrideStatus("Admin token required");
      return;
    }
    setOverrideStatus(enabled ? "Enabling" : "Disabling");
    const response = await fetch(`${API_BASE_URL}/safety-override`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${adminToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        enabled,
        reason: overrideReason,
        expires_in_minutes: Number.parseInt(overrideMinutes, 10) || 60,
        confirm_test_only: true
      })
    });
    if (!response.ok) {
      setOverrideStatus("Override update failed");
      return;
    }
    setSafetyOverride((await response.json()) as SafetyOverrideState);
    setOverrideStatus(enabled ? "Override active" : "Override disabled");
  }

  function updateQuestion(index: number, patch: Partial<ControlledQuestion>) {
    const next = [...settings.controlled_questions];
    next[index] = { ...next[index], ...patch };
    setSettings({ ...settings, controlled_questions: next });
  }

  function addQuestion() {
    setSettings({
      ...settings,
      controlled_questions: [
        ...settings.controlled_questions,
        {
          key: `question_${settings.controlled_questions.length + 1}`,
          category: "general",
          text: "",
          required: true,
          risk_weight: 0
        }
      ]
    });
  }

  function updateRule(index: number, patch: Partial<ResponsePlaybookRule>) {
    const next = [...settings.response_playbook];
    next[index] = { ...next[index], ...patch };
    setSettings({ ...settings, response_playbook: next });
  }

  function addRule() {
    setSettings({
      ...settings,
      response_playbook: [
        ...settings.response_playbook,
        {
          name: `Rule ${settings.response_playbook.length + 1}`,
          trigger_terms: [],
          supplier_intent: "unknown",
          recommended_action: "manual_review",
          response_template: "",
          creates_manual_task: true,
          block_if_matched: false
        }
      ]
    });
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Enterprise Settings</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-graphite">{saveStatus}</span>
          <button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={saveSettings}>
            Save
          </button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Company Identity</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Legal name" value={settings.company.legal_name} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, legal_name: value } })} />
            <TextField label="Trading name" value={settings.company.trading_name ?? ""} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, trading_name: value } })} />
            <TextField label="Registration number" value={settings.company.registration_number ?? ""} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, registration_number: value } })} />
            <TextField label="VAT number" value={settings.company.vat_number ?? ""} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, vat_number: value } })} />
            <TextField label="Website" value={settings.company.website ?? ""} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, website: value } })} />
            <TextField label="Country" value={settings.company.country ?? ""} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, country: value } })} />
          </div>
          <TextArea label="Address" value={settings.company.address ?? ""} onChange={(value) => setSettings({ ...settings, company: { ...settings.company, address: value } })} />
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Sender Persona</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Name" value={settings.sender.name} onChange={(value) => setSettings({ ...settings, sender: { ...settings.sender, name: value } })} />
            <TextField label="Title" value={settings.sender.title ?? ""} onChange={(value) => setSettings({ ...settings, sender: { ...settings.sender, title: value } })} />
            <TextField label="Email" value={settings.sender.email ?? ""} onChange={(value) => setSettings({ ...settings, sender: { ...settings.sender, email: value } })} />
            <TextField label="Phone" value={settings.sender.phone ?? ""} onChange={(value) => setSettings({ ...settings, sender: { ...settings.sender, phone: value } })} />
          </div>
          <TextArea label="Signature" value={settings.sender.signature ?? ""} onChange={(value) => setSettings({ ...settings, sender: { ...settings.sender, signature: value } })} />
        </section>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-ink">Controlled RFQ Questions</h3>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={addQuestion}>
            Add question
          </button>
        </div>
        <div className="grid gap-3">
          {settings.controlled_questions.map((question, index) => (
            <div key={`${question.key}-${index}`} className="grid gap-2 rounded-md bg-slate-50 p-3 md:grid-cols-[140px_140px_1fr_90px]">
              <TextField label="Key" value={question.key} onChange={(value) => updateQuestion(index, { key: value })} />
              <TextField label="Category" value={question.category} onChange={(value) => updateQuestion(index, { category: value })} />
              <TextArea label="Question" value={question.text} onChange={(value) => updateQuestion(index, { text: value })} compact />
              <label className="flex items-end gap-2 pb-2 text-sm text-graphite">
                <input
                  checked={question.required}
                  className="h-4 w-4"
                  type="checkbox"
                  onChange={(event) => updateQuestion(index, { required: event.target.checked })}
                />
                Required
              </label>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-ink">Response Playbook</h3>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={addRule}>
            Add rule
          </button>
        </div>
        <div className="grid gap-3">
          {settings.response_playbook.map((rule, index) => (
            <div key={`${rule.name}-${index}`} className="grid gap-3 rounded-md bg-slate-50 p-3 xl:grid-cols-[1fr_1fr_1fr]">
              <TextField label="Rule name" value={rule.name} onChange={(value) => updateRule(index, { name: value })} />
              <TextField label="Recommended action" value={rule.recommended_action} onChange={(value) => updateRule(index, { recommended_action: value })} />
              <TextField label="Intent" value={rule.supplier_intent} onChange={(value) => updateRule(index, { supplier_intent: value })} />
              <TextArea
                compact
                label="Trigger terms, comma-separated"
                value={rule.trigger_terms.join(", ")}
                onChange={(value) => updateRule(index, { trigger_terms: value.split(",").map((item) => item.trim()).filter(Boolean) })}
              />
              <TextArea compact label="Response template" value={rule.response_template} onChange={(value) => updateRule(index, { response_template: value })} />
              <div className="flex items-end gap-4 pb-2 text-sm text-graphite">
                <label className="flex items-center gap-2">
                  <input
                    checked={rule.creates_manual_task}
                    className="h-4 w-4"
                    type="checkbox"
                    onChange={(event) => updateRule(index, { creates_manual_task: event.target.checked })}
                  />
                  Manual task
                </label>
                <label className="flex items-center gap-2">
                  <input
                    checked={rule.block_if_matched}
                    className="h-4 w-4"
                    type="checkbox"
                    onChange={(event) => updateRule(index, { block_if_matched: event.target.checked })}
                  />
                  Block
                </label>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="mb-3 font-semibold text-ink">Conversation Simulator</h3>
        <TextArea label="Supplier message" value={supplierMessage} onChange={setSupplierMessage} />
        <button className="mt-3 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={runSimulation}>
          Simulate response
        </button>
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
          <div>
            <h3 className="font-semibold text-ink">Test-Only Safety Override</h3>
            <p className="mt-1 text-sm text-graphite">Requires admin bearer token. Never enables real external sends, portal login, CAPTCHA bypass, account registration, or fraud/evasion.</p>
          </div>
          <Badge value={safetyOverride?.active ? "active" : "strict"} tone={safetyOverride?.active ? "warn" : "ok"} />
        </div>
        <div className="grid gap-3 xl:grid-cols-[1.4fr_1fr]">
          <div className="grid gap-3">
            <TextArea compact label="Admin bearer token" value={adminToken} onChange={setAdminToken} />
            <TextArea compact label="Reason" value={overrideReason} onChange={setOverrideReason} />
            <TextField label="TTL minutes" value={overrideMinutes} onChange={setOverrideMinutes} />
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={() => loadSafetyOverride()}>
                Load state
              </button>
              <button className="rounded-md bg-amber px-3 py-2 text-sm font-medium text-white hover:bg-amber-700" type="button" onClick={() => updateSafetyOverride(true)}>
                Enable test override
              </button>
              <button className="rounded-md bg-danger px-3 py-2 text-sm font-medium text-white hover:bg-red-700" type="button" onClick={() => updateSafetyOverride(false)}>
                Disable
              </button>
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

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <input
        className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function SelectField({ label, value, options, onChange }: { label: string; value: string; options: readonly string[]; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <select
        className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option.toUpperCase()}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextArea({ label, value, onChange, compact = false }: { label: string; value: string; onChange: (value: string) => void; compact?: boolean }) {
  return (
    <label className="mt-3 grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <textarea
        className={`rounded-md border border-slate-300 bg-white px-3 py-2 text-ink outline-none focus:border-mint ${compact ? "min-h-20" : "min-h-28"}`}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function Stat({ label, value, icon, tone }: { label: string; value: number; icon: React.ReactNode; tone?: "ok" | "warn" }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className={`mb-3 inline-flex rounded-md p-2 ${tone === "warn" ? "bg-amber-50 text-amber" : "bg-emerald-50 text-mint"}`}>
        {icon}
      </div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      <div className="text-sm text-graphite">{label}</div>
    </div>
  );
}

function MessageList({ messages, empty = "No messages." }: { messages: Message[]; empty?: string }) {
  if (!messages.length) return <p className="text-sm text-graphite">{empty}</p>;
  return (
    <div className="grid gap-2">
      {messages.map((message) => (
        <div key={message.id} className="rounded-md border border-slate-100 bg-slate-50 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-ink">{message.subject ?? "No subject"}</div>
              <div className="text-xs text-graphite">{message.channel ?? "channel"} · {message.status ?? "draft"}</div>
            </div>
            <Badge value={message.policy_decision ?? "not evaluated"} tone={message.policy_decision === "ALLOW_AUTO_SEND" ? "ok" : "warn"} />
          </div>
          {message.policy_reasons?.length ? (
            <p className="mt-2 text-xs text-graphite">{message.policy_reasons.join("; ")}</p>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <div className="text-xs text-graphite">{label}</div>
      <div className="mt-1 font-semibold text-ink">{value}</div>
    </div>
  );
}

function Badge({ value, tone = "neutral" }: { value: string; tone?: "ok" | "warn" | "neutral" }) {
  const classes =
    tone === "ok"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : tone === "warn"
        ? "border-amber-200 bg-amber-50 text-amber-800"
        : "border-slate-200 bg-slate-50 text-graphite";
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium ${classes}`}>{value}</span>;
}

function InfoList({
  title,
  items,
  primaryKey,
  secondaryKey,
}: {
  title: string;
  items: Array<Record<string, unknown>>;
  primaryKey: string;
  secondaryKey: string;
}) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <div className="mb-2 font-semibold text-ink">{title}</div>
      <div className="grid gap-2">
        {items.length ? items.map((item, index) => (
          <div key={`${title}-${index}`} className="text-xs text-graphite">
            <div className="font-medium text-ink">{String(item[primaryKey] ?? "item")}</div>
            <div>{formatInfoValue(item[secondaryKey])}</div>
          </div>
        )) : <div className="text-xs text-graphite">No data yet.</div>}
      </div>
    </div>
  );
}

function formatInfoValue(value: unknown): string {
  if (Array.isArray(value)) return value.map((item) => String(item)).join(", ");
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
