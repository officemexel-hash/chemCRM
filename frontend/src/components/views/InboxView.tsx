"use client";

import type { Message } from "@/types/api";
import { MessageList } from "@/components/Widgets";

export function InboxView({ inbound, outbound }: { inbound: Message[]; outbound: Message[] }) {
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
