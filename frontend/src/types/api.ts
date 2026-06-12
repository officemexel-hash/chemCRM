export type Substance = {
  id: string;
  cas: string;
  primary_name?: string | null;
  pubchem_cid?: string | null;
  molecular_formula?: string | null;
  regulatory_status?: string | null;
  requires_manual_review: boolean;
  synonyms?: { id: string; synonym: string }[];
  regulatory_flags?: { id: string; flag_type?: string | null; severity?: string | null }[];
};

export type Supplier = {
  id: string;
  name: string;
  website?: string | null;
  country?: string | null;
  company_type?: string | null;
  supplier_score: string | number;
  risk_score: string | number;
  risk_level?: string | null;
  contacts?: SupplierContact[];
};

export type SupplierContact = {
  id: string;
  company_id: string;
  channel: string;
  value: string;
  source_url?: string | null;
  evidence_text?: string | null;
};

export type Campaign = {
  id: string;
  substance_id: string;
  quantity?: string | null;
  destination_country?: string | null;
  required_grade?: string | null;
  intended_use?: string | null;
  status?: string | null;
  auto_send_enabled: boolean;
};

export type Message = {
  id: string;
  campaign_id: string;
  company_id: string;
  channel?: string | null;
  subject?: string | null;
  status?: string | null;
  policy_decision?: string | null;
  policy_reasons?: string[];
};

export type QuoteComparisonRow = {
  quote_id: string;
  supplier: string;
  country?: string | null;
  price?: number | null;
  currency?: string | null;
  unit?: string | null;
  moq?: string | null;
  incoterms?: string | null;
  lead_time?: string | null;
  payment_terms?: string | null;
  coa_available?: boolean | null;
  sds_available?: boolean | null;
  reach_status?: string | null;
  adr_class?: string | null;
  risk_level?: string | null;
  confidence?: number | null;
  best_quote: boolean;
};

export type ManualTask = {
  id: string;
  task_type?: string | null;
  title?: string | null;
  status?: string | null;
  related_object_type?: string | null;
};

export type ControlledQuestion = {
  key: string;
  text: string;
  required: boolean;
  category: string;
  risk_weight?: number;
};

export type ResponsePlaybookRule = {
  name: string;
  trigger_terms: string[];
  supplier_intent: string;
  recommended_action: string;
  response_template: string;
  creates_manual_task: boolean;
  block_if_matched: boolean;
};

export type AppSettings = {
  company: {
    legal_name: string;
    trading_name?: string | null;
    registration_number?: string | null;
    vat_number?: string | null;
    eori_number?: string | null;
    website?: string | null;
    address?: string | null;
    country?: string | null;
  };
  sender: {
    name: string;
    title?: string | null;
    email?: string | null;
    phone?: string | null;
    department?: string | null;
    signature?: string | null;
  };
  default_destination_country?: string | null;
  default_intended_use?: string | null;
  default_incoterms: string[];
  controlled_questions: ControlledQuestion[];
  response_playbook: ResponsePlaybookRule[];
  training_scenarios: Array<{
    name: string;
    supplier_message: string;
    expected_action: string;
    notes?: string | null;
  }>;
  require_human_approval_for_simulated_responses: boolean;
  updated_at?: string | null;
};

export type ConversationSimulation = {
  detected_intent: string;
  recommended_action: string;
  response_subject: string;
  response_body: string;
  matched_rules: string[];
  missing_controlled_questions: string[];
  red_flags: string[];
  creates_manual_task: boolean;
  block: boolean;
  approval_required: boolean;
  training_notes: string[];
};

export type SafetyOverrideState = {
  enabled: boolean;
  active: boolean;
  mode: string;
  reason?: string | null;
  enabled_by?: string | null;
  expires_at?: string | null;
  allowed_overrides: string[];
  hard_blocks: string[];
  production_locked: boolean;
};

export type SourcingTask = {
  id: string;
  task_type: string;
  title: string;
  channel?: string | null;
};

export type SourcingQuery = {
  query: string;
  priority: number;
  source_reason: string;
};

export type SourcingBatchItem = {
  raw_cas: string;
  cas?: string | null;
  status: string;
  substance_id?: string | null;
  campaign_id?: string | null;
  queries: SourcingQuery[];
  tasks: SourcingTask[];
  errors: string[];
};

export type SourcingBatch = {
  batch_id: string;
  name: string;
  created_at: string;
  channels: string[];
  summary: {
    total_inputs: number;
    valid: number;
    invalid: number;
    duplicates: number;
    substances_created: number;
    campaigns_created: number;
    manual_tasks_created: number;
    queries_generated: number;
  };
  items: SourcingBatchItem[];
};

export type SourcingReport = {
  batch: SourcingBatch;
  campaign_ids: string[];
  substance_ids: string[];
  manual_task_ids: string[];
  outbound_messages: number;
  inbound_messages: number;
  quotes: number;
  channel_plan: Record<string, string>;
};

export type SubstanceSourcingProfile = {
  summary: {
    id: string;
    cas: string;
    primary_name?: string | null;
    regulatory_status?: string | null;
    requires_manual_review: boolean;
    supplier_count: number;
    contact_count: number;
    quote_count: number;
    offer_count: number;
    countries: string[];
    best_price?: string | number | null;
    best_price_currency?: string | null;
    best_price_unit?: string | null;
  };
  suppliers: Array<{
    id: string;
    name: string;
    website?: string | null;
    country?: string | null;
    company_type?: string | null;
    supplier_score?: string | number | null;
    risk_score?: string | number | null;
    risk_level?: string | null;
    contacts: Array<{
      id: string;
      channel: string;
      value: string;
      contact_person?: string | null;
      source_url?: string | null;
      evidence_text?: string | null;
      consent_status?: string | null;
    }>;
    quotes: Array<{
      id: string;
      campaign_id: string;
      quantity?: string | null;
      price?: string | number | null;
      currency?: string | null;
      unit?: string | null;
      incoterms?: string | null;
      transport_mode?: string | null;
      lead_time?: string | null;
      moq?: string | null;
      payment_terms?: string | null;
      packaging?: string | null;
      coa_available?: boolean | null;
      sds_available?: boolean | null;
      reach_status?: string | null;
      adr_class?: string | null;
      un_number?: string | null;
      hs_code?: string | null;
      confidence?: string | number | null;
      status?: string | null;
    }>;
    product_offers: Array<{
      id: string;
      source_url?: string | null;
      listed_name?: string | null;
      listed_cas?: string | null;
      grade?: string | null;
      purity?: string | null;
      moq?: string | null;
      price_text?: string | null;
      currency?: string | null;
      last_seen_at?: string | null;
    }>;
    contact_history: Array<{
      id: string;
      direction: string;
      company_id: string;
      channel?: string | null;
      subject?: string | null;
      status?: string | null;
      policy_decision?: string | null;
      timestamp?: string | null;
      summary?: string | null;
    }>;
    latest_contact_at?: string | null;
    quoted_packaging: string[];
    quoted_incoterms: string[];
  }>;
  incoterms_by_transport: Array<{
    transport_mode: string;
    recommended_incoterms: string[];
    responsibility_matrix: Record<string, Record<string, string>>;
  }>;
  open_questions: string[];
};

export type ManufacturingAnalysisRequest = {
  target_quantity?: string | null;
  target_grade?: string | null;
  intended_use?: string | null;
  destination_country?: string | null;
  include_raw_material_sourcing: boolean;
  create_raw_material_tasks: boolean;
  save_to_crm: boolean;
};

export type ManufacturingAnalysis = {
  id?: string | null;
  substance_id: string;
  target_quantity?: string | null;
  target_grade?: string | null;
  intended_use?: string | null;
  destination_country?: string | null;
  status: string;
  route_type?: string | null;
  process_overview?: string | null;
  required_equipment: Array<Record<string, unknown>>;
  input_materials: Array<Record<string, unknown>>;
  cost_drivers: Array<Record<string, unknown>>;
  cost_model: Record<string, unknown>;
  sourcing_queries: Array<Record<string, unknown>>;
  compliance_notes: string[];
  safety_notes: string[];
  blocked_reasons: string[];
  confidence?: string | number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type LetterOfIntentResponse = {
  subject: string;
  html: string;
  text: string;
  pdf_ready: boolean;
  generated_document_id?: string | null;
};

export type PurchaseOrderResponse = {
  po_number: string;
  subject: string;
  html: string;
  text: string;
  incoterms_responsibility: Record<string, string>;
  transport_mode: string;
  suggested_incoterms: string[];
  pdf_ready: boolean;
  generated_document_id?: string | null;
};

export type IncotermsGuide = {
  transport_mode: string;
  available_incoterms: string[];
  responsibility_matrix: Record<string, Record<string, string>>;
};

export type CustomsDutyResponse = {
  hs_code: string;
  hs_code_description: string;
  duty_rate: string;
  vat_rate: string;
  additional_taxes: string[];
  legal_uses: string[];
  regulatory_notes: string[];
  source: string;
  source_url?: string | null;
  effective_date?: string | null;
  confidence: number;
  manual_review_required: boolean;
  assumptions: string[];
};

export type SubstanceAnalogsResponse = {
  source_cas: string;
  source_name: string;
  recommendation: string;
  analogs: Array<{
    cas: string;
    name: string;
    iupac_name?: string | null;
    molecular_formula?: string | null;
    structural_similarity: string;
    functional_similarity: string;
    price_indication: string;
    advantages: string[];
    disadvantages: string[];
    similarity_basis: string[];
    requires_validation: boolean;
  }>;
};

// ── Bulk Import ──

export type BulkImportJob = {
  id: string;
  filename: string;
  original_filename?: string | null;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  status: string;
  error_details?: Record<string, unknown> | null;
  created_at: string;
  items?: BulkImportItem[];
};

export type BulkImportItem = {
  id: string;
  job_id: string;
  row_number: number;
  cas_raw: string;
  cas_valid: boolean;
  substance_id?: string | null;
  status: string;
  error_message?: string | null;
};

// ── Tariff / HS Code ──

export type HsCodeEntry = {
  id: string;
  hs_code: string;
  chapter?: string | null;
  heading?: string | null;
  subheading?: string | null;
  description?: string | null;
  cas_pattern?: string | null;
  source_database: string;
  confidence?: number | null;
};

export type TariffRate = {
  id: string;
  hs_code_id: string;
  origin_country: string;
  destination_country: string;
  duty_rate_percent?: number | null;
  duty_type?: string | null;
  preferential_rate?: number | null;
  preferential_source?: string | null;
  anti_dumping_rate?: number | null;
  source_database: string;
};

export type LegalUseDescription = {
  id: string;
  substance_id: string;
  description: string;
  category?: string | null;
  destination_country?: string | null;
  source?: string | null;
};

export type ResponsibilityMatrixRow = {
  cost_type: string;
  responsible_party: string;
  notes?: string | null;
};

// ── Reports ──

export type RankingRow = {
  rank: number;
  quote_id: string;
  supplier_name: string;
  country?: string | null;
  total_score: number;
  price_score: number;
  supplier_quality_score: number;
  risk_score: number;
  document_completeness: number;
  recommended: boolean;
  price?: string | null;
  currency?: string | null;
  lead_time?: string | null;
  incoterms?: string | null;
};

export type GeneratedDocumentMeta = {
  id: string;
  doc_type: string;
  campaign_id?: string | null;
  quote_id?: string | null;
  company_id?: string | null;
  substance_id?: string | null;
  file_path?: string | null;
  file_size_bytes?: number | null;
  parameters?: Record<string, unknown> | null;
  status: string;
  created_at: string;
};

// ── Batch Approve ──

export type BatchApproveResponse = {
  approved: number;
  skipped: number;
  blocked: number;
  results: Array<{ message_id: string; status: string }>;
};
