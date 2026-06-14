import type {
  BulkImportJob,
  BulkImportItem,
  Campaign,
  GeneratedDocumentMeta,
  HsCodeEntry,
  LegalUseDescription,
  ManualTask,
  ManufacturingAnalysis,
  ManufacturingAnalysisRequest,
  Message,
  QuoteComparisonRow,
  RankingRow,
  ResponsibilityMatrixRow,
  Substance,
  SubstanceSourcingProfile,
  Supplier,
  TariffRate,
  BatchApproveResponse,
} from "@/types/api";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function loadDashboardData() {
  const [substances, suppliers, campaigns, outboundMessages, inboundMessages, tasks] = await Promise.all([
    apiGet<Substance[]>("/substances", demoSubstances),
    apiGet<Supplier[]>("/suppliers", demoSuppliers),
    apiGet<Campaign[]>("/campaigns", demoCampaigns),
    apiGet<Message[]>("/messages/outbound", demoMessages),
    apiGet<Message[]>("/messages/inbound", []),
    apiGet<ManualTask[]>("/manual-tasks", demoTasks)
  ]);

  let comparison: QuoteComparisonRow[] = demoComparison;
  if (campaigns[0]?.id && !campaigns[0].id.startsWith("demo")) {
    comparison = await apiGet<QuoteComparisonRow[]>(`/campaigns/${campaigns[0].id}/comparison`, demoComparison);
  }

  return { substances, suppliers, campaigns, outboundMessages, inboundMessages, tasks, comparison };
}

export const demoSubstances: Substance[] = [
  {
    id: "demo-substance-1",
    cas: "64-17-5",
    primary_name: "Ethanol",
    pubchem_cid: "702",
    molecular_formula: "C2H6O",
    regulatory_status: "unreviewed",
    requires_manual_review: false,
    synonyms: [{ id: "s1", synonym: "ethyl alcohol" }],
    regulatory_flags: []
  },
  {
    id: "demo-substance-2",
    cas: "7732-18-5",
    primary_name: "Water",
    pubchem_cid: "962",
    molecular_formula: "H2O",
    regulatory_status: "unreviewed",
    requires_manual_review: false,
    synonyms: [{ id: "s2", synonym: "purified water" }],
    regulatory_flags: []
  }
];

export const demoSuppliers: Supplier[] = [
  {
    id: "demo-supplier-1",
    name: "Acme Chemical Manufacturer",
    website: "https://acme.example",
    country: "PL",
    company_type: "MANUFACTURER",
    supplier_score: 95,
    risk_score: 0,
    risk_level: "low",
    contacts: [{ id: "c1", company_id: "demo-supplier-1", channel: "email", value: "sales@acme.example" }]
  },
  {
    id: "demo-supplier-2",
    name: "Euro Lab Supplies",
    website: "https://eurolab.example",
    country: "DE",
    company_type: "LAB_SUPPLIER",
    supplier_score: 70,
    risk_score: 10,
    risk_level: "low",
    contacts: [{ id: "c2", company_id: "demo-supplier-2", channel: "form", value: "/contact" }]
  },
  {
    id: "demo-supplier-3",
    name: "Global Trading Demo",
    website: "https://globaltrading.example",
    country: "NL",
    company_type: "TRADER_BROKER",
    supplier_score: 35,
    risk_score: 30,
    risk_level: "unknown",
    contacts: [{ id: "c3", company_id: "demo-supplier-3", channel: "email", value: "sales@globaltrading.example" }]
  }
];

export const demoCampaigns: Campaign[] = [
  {
    id: "demo-campaign-1",
    substance_id: "demo-substance-1",
    quantity: "100 kg",
    destination_country: "Poland",
    required_grade: "technical grade",
    intended_use: "lawful industrial validation",
    status: "active",
    auto_send_enabled: false
  }
];

export const demoMessages: Message[] = [
  {
    id: "demo-message-1",
    campaign_id: "demo-campaign-1",
    company_id: "demo-supplier-1",
    channel: "email",
    subject: "RFQ: Ethanol / CAS 64-17-5",
    status: "requires_approval",
    policy_decision: "REQUIRES_APPROVAL",
    policy_reasons: ["Demo campaign auto-send disabled."]
  },
  {
    id: "demo-message-2",
    campaign_id: "demo-campaign-1",
    company_id: "demo-supplier-2",
    channel: "email",
    subject: "RFQ: Ethanol / CAS 64-17-5",
    status: "draft",
    policy_decision: "DRAFT_ONLY",
    policy_reasons: ["Draft pending review."]
  }
];

export const demoComparison: QuoteComparisonRow[] = [
  {
    quote_id: "demo-quote-1",
    supplier: "Acme Chemical Manufacturer",
    country: "PL",
    price: 12.5,
    currency: "USD",
    unit: "kg",
    moq: "25 kg",
    incoterms: "EXW",
    lead_time: "14 days",
    payment_terms: "TT",
    coa_available: true,
    sds_available: true,
    reach_status: "available",
    adr_class: null,
    risk_level: "low",
    confidence: 0.75,
    best_quote: true
  }
];

export const demoTasks: ManualTask[] = [
  { id: "demo-task-1", task_type: "approval_needed", title: "Approve RFQ draft", status: "open" },
  { id: "demo-task-2", task_type: "regulatory_review", title: "Review unknown substance flag", status: "open" }
];

// ── Bulk Import API ──

export async function uploadBulkImport(file: File): Promise<BulkImportJob> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/bulk-import/upload`, { method: "POST", body: formData });
  if (!response.ok) throw new Error("Upload failed");
  return response.json();
}

export async function processBulkImport(jobId: string): Promise<BulkImportJob> {
  const response = await fetch(`${API_BASE_URL}/bulk-import/${jobId}/process`, { method: "POST" });
  if (!response.ok) throw new Error("Processing failed");
  return response.json();
}

export async function enrichBulkImport(jobId: string): Promise<{ enriched: number; total: number }> {
  const response = await fetch(`${API_BASE_URL}/bulk-import/${jobId}/enrich`, { method: "POST" });
  if (!response.ok) throw new Error("Enrichment failed");
  return response.json();
}

export async function getBulkImportJob(jobId: string): Promise<BulkImportJob> {
  return apiGet<BulkImportJob>(`/bulk-import/${jobId}`, {} as BulkImportJob);
}

export async function getBulkImportItems(jobId: string): Promise<BulkImportItem[]> {
  return apiGet<BulkImportItem[]>(`/bulk-import/${jobId}/items`, []);
}

export async function getSubstanceIntelligence(substanceId: string): Promise<SubstanceSourcingProfile | null> {
  return apiGet<SubstanceSourcingProfile | null>(`/substances/${substanceId}/intelligence`, null);
}

export async function createManufacturingAnalysis(
  substanceId: string,
  payload: ManufacturingAnalysisRequest,
): Promise<ManufacturingAnalysis> {
  const response = await fetch(`${API_BASE_URL}/substances/${substanceId}/manufacturing-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Manufacturing analysis failed");
  return response.json();
}

export async function listManufacturingAnalyses(substanceId: string): Promise<ManufacturingAnalysis[]> {
  return apiGet<ManufacturingAnalysis[]>(`/substances/${substanceId}/manufacturing-analyses`, []);
}

// ── Tariff / HS Code API ──

export async function lookupHsCode(cas?: string, substanceId?: string): Promise<HsCodeEntry[]> {
  const params = new URLSearchParams();
  if (cas) params.set("cas", cas);
  if (substanceId) params.set("substance_id", substanceId);
  return apiGet<HsCodeEntry[]>(`/tariff/hs-code/lookup?${params}`, []);
}

export async function getDutyRate(hsCode: string, origin: string, destination: string): Promise<TariffRate | null> {
  return apiGet<TariffRate | null>(`/tariff/duty-rate?hs_code=${hsCode}&origin=${origin}&destination=${destination}`, null);
}

export async function getResponsibilityMatrix(incoterms: string): Promise<ResponsibilityMatrixRow[]> {
  return apiGet<ResponsibilityMatrixRow[]>(`/tariff/incoterms/${incoterms}/responsibility-matrix`, []);
}

export async function getIncotermsForTransport(transportType: string): Promise<{ transport_type: string; recommended_incoterms: string[] }> {
  return apiGet(`/tariff/incoterms-for-transport/${transportType}`, { transport_type: transportType, recommended_incoterms: ["FOB", "CIF"] });
}

export async function getLegalUses(substanceId: string, destination?: string): Promise<LegalUseDescription[]> {
  const params = destination ? `?destination=${destination}` : "";
  return apiGet<LegalUseDescription[]>(`/tariff/legal-use/${substanceId}${params}`, []);
}

export async function getCustomsText(substanceId: string, hsCode: string, destination: string): Promise<{ declaration_text: string }> {
  return apiGet(`/tariff/legal-use/${substanceId}/customs-text?hs_code=${hsCode}&destination=${destination}`, { declaration_text: "" });
}

// ── Batch Approve API ──

export async function batchApproveMessages(campaignId: string): Promise<BatchApproveResponse> {
  const response = await fetch(`${API_BASE_URL}/messages/outbound/batch-approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ campaign_id: campaignId }),
  });
  if (!response.ok) throw new Error("Batch approve failed");
  return response.json();
}

// ── Documents API ──

export async function listDocuments(docType?: string, campaignId?: string): Promise<GeneratedDocumentMeta[]> {
  const params = new URLSearchParams();
  if (docType) params.set("doc_type", docType);
  if (campaignId) params.set("campaign_id", campaignId);
  return apiGet<GeneratedDocumentMeta[]>(`/documents?${params}`, []);
}

export async function downloadDocument(docId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/documents/${docId}/download`);
  if (!response.ok) throw new Error("Download failed");
  return response.blob();
}

// ── Reports API ──

export async function generateReport(campaignId: string, format: string = "pdf"): Promise<GeneratedDocumentMeta> {
  const response = await fetch(`${API_BASE_URL}/reports/comparison`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ campaign_id: campaignId, format }),
  });
  if (!response.ok) throw new Error("Report generation failed");
  return response.json();
}

export async function getRanking(campaignId: string): Promise<RankingRow[]> {
  return apiGet<RankingRow[]>(`/reports/ranking/${campaignId}`, []);
}

// ── CRUD API ──

export async function createSubstance(cas: string, primaryName?: string): Promise<Substance> {
  const res = await fetch(`${API_BASE_URL}/substances`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cas, primary_name: primaryName || null }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function enrichSubstance(substanceId: string): Promise<Substance> {
  const res = await fetch(`${API_BASE_URL}/substances/${substanceId}/enrich`, { method: "POST" });
  if (!res.ok) throw new Error("Enrichment failed");
  return res.json();
}

export async function createSupplier(payload: {
  name: string;
  website?: string;
  country?: string;
  company_type?: string;
  contacts?: { channel: string; value: string; source_url: string; evidence_text: string }[];
}): Promise<Supplier> {
  const res = await fetch(`${API_BASE_URL}/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, company_type: payload.company_type || "UNKNOWN", contacts: (payload.contacts || []).map((c) => ({ ...c, consent_status: "unknown" })) }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function classifySupplier(supplierId: string): Promise<{ company_type: string; supplier_score: number; risk_score: number; risk_level: string }> {
  const res = await fetch(`${API_BASE_URL}/suppliers/${supplierId}/classify`, { method: "POST" });
  if (!res.ok) throw new Error("Classification failed");
  return res.json();
}

export async function createCampaign(payload: {
  substance_id: string;
  quantity?: string;
  destination_country?: string;
  required_grade?: string;
  intended_use?: string;
  auto_send_enabled?: boolean;
}): Promise<Campaign> {
  const res = await fetch(`${API_BASE_URL}/campaigns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generateRfq(campaignId: string, supplierId: string, contactId: string): Promise<Message> {
  const res = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/generate-rfq`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ supplier_id: supplierId, contact_id: contactId }),
  });
  if (!res.ok) throw new Error("RFQ generation failed");
  return res.json();
}

export async function runAutonomousCampaign(campaignId: string, options?: {
  supplier_ids?: string[]; dry_run?: boolean; allow_duplicates?: boolean;
}): Promise<{ campaign_id: string; generated: number; sent: number; simulated: number; requires_approval: number; blocked: number; skipped: number }> {
  const res = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/run-autonomous`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options || {}),
  });
  if (!res.ok) throw new Error("Autonomous run failed");
  return res.json();
}

export async function startDiscovery(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE_URL}/discovery/start`, { method: "POST" });
  if (!res.ok) return { message: "Discovery triggered" };
  return res.json();
}

export async function markTaskCompleted(taskId: string): Promise<ManualTask> {
  const res = await fetch(`${API_BASE_URL}/manual-tasks/${taskId}/complete`, { method: "POST" });
  if (!res.ok) throw new Error("Task completion failed");
  return res.json();
}

export async function markQuoteReviewed(quoteId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/quotes/${quoteId}/review`, { method: "POST" });
  if (!res.ok) throw new Error("Review failed");
}

export async function patchTask(taskId: string, payload: { status?: string; assigned_to?: string; title?: string }): Promise<ManualTask> {
  const res = await fetch(`${API_BASE_URL}/manual-tasks/${taskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Task update failed");
  return res.json();
}

export async function importDiscoveryUrls(urls: string[]): Promise<{ imported: number }> {
  const res = await fetch(`${API_BASE_URL}/discovery/import-urls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls }),
  });
  if (!res.ok) throw new Error("URL import failed");
  return res.json();
}
