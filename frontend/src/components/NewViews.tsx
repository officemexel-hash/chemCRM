"use client";

// ── Rebrand View ──
// Supplier COA/SDS rebranding is disabled by design (compliance boundary).
// Store original supplier documents as evidence and generate only your own
// LOI, PO, RFQ, or report documents.

export function RebrandView() {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      Supplier COA/SDS rebranding is disabled. Store original supplier documents as evidence and generate only your own LOI, PO, RFQ, or report documents.
    </div>
  );
}
