"use client";

import React from "react";

export function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <input className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

export function SelectField({ label, value, options, onChange }: { label: string; value: string; options: readonly string[]; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <select className="h-10 rounded-md border border-slate-300 bg-white px-3 text-ink outline-none focus:border-mint" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o} value={o}>{o.toUpperCase()}</option>)}
      </select>
    </label>
  );
}

export function TextArea({ label, value, onChange, compact = false }: { label: string; value: string; onChange: (value: string) => void; compact?: boolean }) {
  return (
    <label className="mt-3 grid gap-1 text-sm text-graphite">
      <span>{label}</span>
      <textarea className={`rounded-md border border-slate-300 bg-white px-3 py-2 text-ink outline-none focus:border-mint ${compact ? "min-h-20" : "min-h-28"}`} value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

export function Stat({ label, value, icon, tone }: { label: string; value: number; icon: React.ReactNode; tone?: "ok" | "warn" }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className={`mb-3 inline-flex rounded-md p-2 ${tone === "warn" ? "bg-amber-50 text-amber" : "bg-emerald-50 text-mint"}`}>{icon}</div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      <div className="text-sm text-graphite">{label}</div>
    </div>
  );
}

export function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <div className="text-xs text-graphite">{label}</div>
      <div className="mt-1 font-semibold text-ink">{value}</div>
    </div>
  );
}

export function Badge({ value, tone = "neutral" }: { value: string; tone?: "ok" | "warn" | "neutral" }) {
  const cls = tone === "ok" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : tone === "warn" ? "border-amber-200 bg-amber-50 text-amber-800" : "border-slate-200 bg-slate-50 text-graphite";
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium ${cls}`}>{value}</span>;
}

export function MessageList({ messages, empty = "No messages." }: { messages: Array<{ id: string; subject?: string | null; channel?: string | null; status?: string | null; policy_decision?: string | null; policy_reasons?: string[] }>; empty?: string }) {
  if (!messages.length) return <p className="text-sm text-graphite">{empty}</p>;
  return (
    <div className="grid gap-2">
      {messages.map((m) => (
        <div key={m.id} className="rounded-md border border-slate-100 bg-slate-50 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-ink">{m.subject ?? "No subject"}</div>
              <div className="text-xs text-graphite">{m.channel ?? "channel"} · {m.status ?? "draft"}</div>
            </div>
            <Badge value={m.policy_decision ?? "not evaluated"} tone={m.policy_decision === "ALLOW_AUTO_SEND" ? "ok" : "warn"} />
          </div>
          {m.policy_reasons?.length ? <p className="mt-2 text-xs text-graphite">{m.policy_reasons.join("; ")}</p> : null}
        </div>
      ))}
    </div>
  );
}

export function InfoList({ title, items, primaryKey, secondaryKey }: { title: string; items: Array<Record<string, unknown>>; primaryKey: string; secondaryKey: string }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <div className="mb-2 font-semibold text-ink">{title}</div>
      <div className="grid gap-2">
        {items.length ? items.map((item, i) => (
          <div key={`${title}-${i}`} className="text-xs text-graphite">
            <div className="font-medium text-ink">{String(item[primaryKey] ?? "item")}</div>
            <div>{formatInfoValue(item[secondaryKey])}</div>
          </div>
        )) : <div className="text-xs text-graphite">No data yet.</div>}
      </div>
    </div>
  );
}

export function formatInfoValue(value: unknown): string {
  if (Array.isArray(value)) return value.map((v) => String(v)).join(", ");
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
