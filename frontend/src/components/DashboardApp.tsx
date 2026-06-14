"use client";

import {
  AlertTriangle, BarChart3, Beaker, ClipboardCheck, FileText, Globe, Inbox,
  MessageSquareText, RefreshCw, ScanEye, Search, Settings, ShieldCheck, Truck, Upload, Users
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { loadDashboardData } from "@/lib/api";
import { AddSubstanceDialog, AddSupplierDialog, CreateCampaignDialog, GenerateRfqDialog, AutonomousRunDialog, EnrichSubstancesDialog, ClassifySuppliersDialog, CompleteTaskDialog } from "@/components/Dialogs";
import type { Campaign, ManualTask, Message, QuoteComparisonRow, Substance, Supplier } from "@/types/api";

import { DashboardView } from "@/components/views/DashboardView";
import type { DashboardData } from "@/components/views/DashboardView";
import { BulkImportView } from "@/components/views/BulkImportView";
import { SourcingView } from "@/components/views/SourcingView";
import { SubstanceIntelligenceView } from "@/components/views/SubstanceIntelligenceView";
import { DocumentsView } from "@/components/views/DocumentsView";
import { SubstancesView } from "@/components/views/SubstancesView";
import { DiscoveryView } from "@/components/views/DiscoveryView";
import { SuppliersView } from "@/components/views/SuppliersView";
import { CampaignsView } from "@/components/views/CampaignsView";
import { InboxView } from "@/components/views/InboxView";
import { QuotesView } from "@/components/views/QuotesView";
import { TariffView } from "@/components/views/TariffView";
import { ReportsView } from "@/components/views/ReportsView";
import { TasksView } from "@/components/views/TasksView";
import { SettingsView } from "@/components/views/SettingsView";
import { RebrandView } from "@/components/NewViews";

const emptyData: DashboardData = {
  substances: [], suppliers: [], campaigns: [], outboundMessages: [], inboundMessages: [], tasks: [], comparison: [],
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
  { id: "rebrand", label: "Rebrand", icon: ScanEye },
  { id: "settings", label: "Settings", icon: Settings },
] as const;

export function DashboardApp() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]["id"]>("dashboard");
  const [data, setData] = useState<DashboardData>(emptyData);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState<string | null>(null);

  const refresh = () => loadDashboardData().then(setData);

  useEffect(() => { refresh().finally(() => setLoading(false)); }, []);

  const riskAlerts = useMemo(
    () => data.suppliers.filter((s) => ["high", "elevated", "unknown"].includes(String(s.risk_level))).length +
      data.substances.filter((s) => s.requires_manual_review).length,
    [data],
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
            <ShieldCheck size={16} /> Policy engine active
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
                <button key={tab.id} type="button" onClick={() => setActiveTab(tab.id)}
                  className={`flex h-10 items-center gap-2 rounded-md px-3 text-left text-sm transition ${active ? "bg-ink text-white" : "text-graphite hover:bg-white"}`}
                  title={tab.label}>
                  <Icon size={17} /><span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        <main className="min-w-0">
          {loading ? (
            <div className="flex h-40 items-center justify-center gap-2 text-graphite">
              <RefreshCw className="animate-spin" size={18} /> Loading workspace data
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
              {activeTab === "tasks" && <TasksView tasks={data.tasks} onDialog={setDialog} onUpdated={(t) => { setData((d) => ({ ...d, tasks: d.tasks.map((x) => x.id === t.id ? { ...x, assigned_to: t.assigned_to, status: t.status, title: t.title } : x) })); }} />}
              {activeTab === "rebrand" && <RebrandView />}
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
      {dialog === "enrich-substances" && <EnrichSubstancesDialog substances={data.substances} onClose={() => setDialog(null)} onEnriched={(u) => { setData((d) => ({ ...d, substances: d.substances.map((s) => s.id === u.id ? u : s) })); }} />}
      {dialog === "classify-suppliers" && <ClassifySuppliersDialog suppliers={data.suppliers} onClose={() => setDialog(null)} onClassified={(r) => { setData((d) => ({ ...d, suppliers: d.suppliers.map((s) => s.id === r.id ? { ...s, company_type: r.company_type, supplier_score: r.supplier_score, risk_score: r.risk_score, risk_level: r.risk_level } : s) })); }} />}
      {dialog === "complete-tasks" && <CompleteTaskDialog tasks={data.tasks} onClose={() => setDialog(null)} onCompleted={(id) => { setData((d) => ({ ...d, tasks: d.tasks.map((t) => t.id === id ? { ...t, status: "completed" } : t) })); }} />}
    </div>
  );
}
