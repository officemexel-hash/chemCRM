"use client";

import React from "react";
import { AlertTriangle, Beaker, FileText, Inbox, MessageSquareText, Truck, Users } from "lucide-react";
import type { Campaign, ManualTask, Message, QuoteComparisonRow, Substance, Supplier } from "@/types/api";
import { Stat, Metric, Badge, MessageList } from "@/components/Widgets";

export type DashboardData = {
  substances: Substance[];
  suppliers: Supplier[];
  campaigns: Campaign[];
  outboundMessages: Message[];
  inboundMessages: Message[];
  tasks: ManualTask[];
  comparison: QuoteComparisonRow[];
};

export function DashboardView({ data, riskAlerts }: { data: DashboardData; riskAlerts: number }) {
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
            <Truck size={18} className="text-mint" />
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
              <div className="text-2xl font-bold text-mint">{bestQuote.price} {bestQuote.currency}/{bestQuote.unit}</div>
              <div className="grid grid-cols-2 gap-2 text-graphite">
                <span>MOQ: {bestQuote.moq ?? "n/a"}</span><span>Incoterms: {bestQuote.incoterms ?? "n/a"}</span>
                <span>Lead time: {bestQuote.lead_time ?? "n/a"}</span><span>Risk: {bestQuote.risk_level ?? "n/a"}</span>
              </div>
            </div>
          ) : <p className="text-sm text-graphite">No parsed quotes yet.</p>}
        </section>
      </div>
    </section>
  );
}
