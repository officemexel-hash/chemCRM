"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import type { CustomsDutyResponse, IncotermsGuide, LetterOfIntentResponse, PurchaseOrderResponse, SubstanceAnalogsResponse } from "@/types/api";
import { API_BASE_URL, downloadDocument } from "@/lib/api";
import { Metric, TextField, TextArea, SelectField } from "@/components/Widgets";

const transportModes = ["sea", "air", "road", "rail", "courier", "multimodal"];
const incotermsOptions = ["EXW", "FCA", "FOB", "CIF", "CFR", "FAS", "CPT", "CIP", "DAP", "DDP"];

export function DocumentsView() {
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
      .then((r) => r.ok ? r.json() : null)
      .then((p: IncotermsGuide | null) => { if (p) { setIncotermsGuide(p); if (!p.available_incoterms.includes(incoterms)) setIncoterms(p.available_incoterms[0] ?? "FCA"); } })
      .catch(() => setIncotermsGuide(null));
  }, [transportMode]);

  async function lookupCustoms() {
    setStatus("Looking up customs");
    const r = await fetch(`${API_BASE_URL}/documents/customs-duty`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cas: substanceCas, substance_name: substanceName, hs_code: hsCode, origin_country: originCountry, destination_country: destinationCountry }) });
    if (!r.ok) { setStatus("Customs lookup failed"); return; }
    const p = await r.json() as CustomsDutyResponse; setCustoms(p); setHsCode(p.hs_code === "unknown" ? "" : p.hs_code); setCustomsDutyRate(p.duty_rate); setLegalUseDescription(p.legal_uses[0] ?? ""); setStatus("Customs estimate loaded");
  }
  async function findAnalogs() {
    setStatus("Finding analogs");
    const r = await fetch(`${API_BASE_URL}/documents/substance-analogs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cas: substanceCas, primary_name: substanceName, target_application: intendedUse }) });
    if (!r.ok) { setStatus("Analog lookup failed"); return; }
    setAnalogs(await r.json() as SubstanceAnalogsResponse); setStatus("Analogs loaded");
  }
  async function generateLoi() {
    setStatus("Generating LOI");
    const r = await fetch(`${API_BASE_URL}/documents/letter-of-intent`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ recipient_name: recipientName, recipient_company: supplierName, substance_name: substanceName, substance_cas: substanceCas, quantity: `${quantity} ${unit}`, intended_use: intendedUse, destination_country: destinationCountry, save_to_crm: true }) });
    if (!r.ok) { setStatus("LOI generation failed"); return; }
    const p = await r.json() as LetterOfIntentResponse; setLoi(p); setPreviewHtml(p.html); setStatus("LOI generated");
  }
  async function generatePo() {
    setStatus("Generating PO");
    const r = await fetch(`${API_BASE_URL}/documents/purchase-order`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ supplier_name: supplierName, supplier_address: supplierAddress, supplier_contact: supplierContact, substance_name: substanceName, substance_cas: substanceCas, quantity, unit, price_per_unit: pricePerUnit, currency, incoterms, transport_mode: transportMode, payment_terms: paymentTerms, delivery_address: deliveryAddress, special_requirements: specialRequirements, hs_code: hsCode, customs_duty_rate: customsDutyRate, legal_use_description: legalUseDescription, save_to_crm: true }) });
    if (!r.ok) { setStatus("PO generation failed"); return; }
    const p = await r.json() as PurchaseOrderResponse; setPo(p); setPreviewHtml(p.html); setStatus("PO generated");
  }
  async function dl(docId: string, fallback: string) { setStatus("Preparing download"); try { const b = await downloadDocument(docId); const u = URL.createObjectURL(b); const a = document.createElement("a"); a.href = u; a.download = `${fallback}.pdf`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(u); setStatus("Download ready"); } catch { setStatus("Download failed"); } }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Documents, Customs, Analogs</h2>
        <div className="flex flex-wrap items-center gap-2"><span className="text-sm text-graphite">{status}</span><button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={lookupCustoms}>Customs</button><button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50" type="button" onClick={findAnalogs}>Analogs</button><button className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" type="button" onClick={generateLoi}>LOI</button><button className="rounded-md bg-mint px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700" type="button" onClick={generatePo}>PO</button></div>
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
          <div className="mb-3 grid gap-2 md:grid-cols-2"><Metric label="LOI" value={loi?.generated_document_id ? "saved" : loi ? "generated" : "none"} /><Metric label="PO" value={po?.generated_document_id ? "saved" : po ? "generated" : "none"} /></div>
          <div className="mb-3 flex flex-wrap gap-2">
            <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" disabled={!loi?.generated_document_id} type="button" onClick={() => loi?.generated_document_id && dl(loi.generated_document_id, "letter-of-intent")}><Download className="h-4 w-4" />Download LOI</button>
            <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50" disabled={!po?.generated_document_id} type="button" onClick={() => po?.generated_document_id && dl(po.generated_document_id, po.po_number || "purchase-order")}><Download className="h-4 w-4" />Download PO</button>
          </div>
          {previewHtml ? <iframe className="h-[560px] w-full rounded-md border border-slate-200 bg-white" srcDoc={previewHtml} title="Document preview" /> : <p className="text-sm text-graphite">Generate LOI or PO to preview letterhead document.</p>}
        </section>
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Customs</h3>
          {customs ? <div className="grid gap-2 text-sm text-graphite"><div><span className="font-semibold text-ink">HS:</span> {customs.hs_code}</div><div><span className="font-semibold text-ink">Duty:</span> {customs.duty_rate}</div><div><span className="font-semibold text-ink">VAT:</span> {customs.vat_rate}</div><div><span className="font-semibold text-ink">Confidence:</span> {customs.confidence}</div><div><span className="font-semibold text-ink">Review:</span> {customs.manual_review_required ? "required" : "not required"}</div><div>{customs.hs_code_description}</div>{customs.source_url ? <a className="text-mint underline" href={customs.source_url} target="_blank">Official source</a> : null}</div> : <p className="text-sm text-graphite">Run customs lookup to populate HS, duty and legal uses.</p>}
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Legal Uses</h3>
          {customs?.legal_uses.length ? <div className="grid gap-2">{customs.legal_uses.map((u) => <div key={u} className="rounded-md bg-slate-50 p-2 text-sm text-graphite">{u}</div>)}</div> : <p className="text-sm text-graphite">No legal-use suggestions loaded.</p>}
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-ink">Analogs</h3>
          {analogs?.analogs.length ? <div className="grid gap-2">{analogs.analogs.map((a) => <div key={a.cas} className="rounded-md bg-slate-50 p-3 text-sm"><div className="font-semibold text-ink">{a.name} / {a.cas}</div><div className="mt-1 text-graphite">{a.price_indication}</div><div className="mt-1 text-graphite">{a.functional_similarity}</div><div className="mt-1 text-xs text-graphite">{a.similarity_basis.join(", ")}</div></div>)}<p className="text-sm text-graphite">{analogs.recommendation}</p></div> : <p className="text-sm text-graphite">Run analog lookup to see substitutes.</p>}
        </section>
      </div>
    </section>
  );
}
