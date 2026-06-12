"use client";

import type React from "react";
import { useState } from "react";
import type { Campaign } from "@/types/api";
import { Badge, MessageList } from "@/components/Widgets";

export function CampaignsView({ campaigns, messages, onDialog }: { campaigns: Campaign[]; messages: Array<{ id: string; campaign_id: string; subject?: string | null; channel?: string | null; status?: string | null; policy_decision?: string | null; policy_reasons?: string[] }>; onDialog: (d: string) => void }) {
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
            <p className="mt-3 text-sm text-graphite">Autonomous mode sends only policy-approved low-risk email/form RFQs. Marketplace/internal messenger items become manual approval tasks.</p>
            <div className="mt-4">
              <MessageList messages={messages.filter((m) => m.campaign_id === campaign.id || campaign.id.startsWith("demo"))} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
