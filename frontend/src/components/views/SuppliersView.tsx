"use client";

import type { Supplier } from "@/types/api";
import { Badge, Metric } from "@/components/Widgets";

export function SuppliersView({ suppliers, onDialog }: { suppliers: Supplier[]; onDialog: (d: string) => void }) {
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
