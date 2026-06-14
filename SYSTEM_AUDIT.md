# Chemical Sourcing RFQ CRM — System Audit

**Data audytu:** 2026-06-14
**Wersja systemu:** 0.1.0 (MVP)
**Ostatni commit:** `360c644`

---

## 1. Przegląd systemu

Chemical Sourcing RFQ CRM to webowy system B2B do legalnego sourcingu substancji chemicznych po numerze CAS. System przeprowadza użytkownika od listy substancji przez discovery dostawców, kampanie RFQ, zbieranie ofert, porównanie, aż po dokumenty handlowe (LOI/PO).

**Stack technologiczny:**
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- **Baza danych:** PostgreSQL 16 (produkcja) / SQLite (development)
- **Cache/Kolejki:** Redis 7, Celery 5.x
- **Frontend:** Next.js 16, React 18, TypeScript 5, Tailwind CSS 3
- **LLM:** Anthropic Claude SDK, OpenAI SDK, Mock provider
- **Infrastruktura:** Docker Compose (6 kontenerów)

---

## 2. Stan testów

| Metryka | Wartość |
|---------|---------|
| Testy backend | **44/44 przechodzą** (pytest) |
| Build frontend | ✅ (Next.js 16.2.9, Turbopack) |
| Smoke test Playwright | **0 failures** (16 widoków + dialogi) |
| Pokrycie endpointów testami | ~55% (44 testy, ~80 endpointów) |

---

## 3. Baza danych — 27 tabel

| # | Tabela | Kluczowe kolumny | Relacje |
|---|--------|------------------|---------|
| 1 | `users` | id, email, password_hash, role | → campaigns |
| 2 | `substances` | id, cas (unique), primary_name, pubchem_cid, molecular_formula, regulatory_status | → synonyms, flags, campaigns, quotes |
| 3 | `substance_synonyms` | id, substance_id, synonym, source | → substances |
| 4 | `regulatory_flags` | id, substance_id, flag_type, severity | → substances |
| 5 | `supplier_companies` | id, name, country, company_type, supplier_score, risk_score, risk_level | → contacts, quotes, messages |
| 6 | `supplier_contacts` | id, company_id, channel, value, source_url, evidence_text | → companies |
| 7 | `consent_evidence` | id, company_id, contact_channel, evidence_type, source_url | → companies |
| 8 | `product_offers` | id, company_id, substance_id, listed_name, listed_cas, grade, moq, price_text | → companies, substances |
| 9 | `rfq_campaigns` | id, substance_id, quantity, destination_country, status, auto_send_enabled | → substances, messages, quotes |
| 10 | `outbound_messages` | id, campaign_id, company_id, contact_id, subject, body, status, policy_decision | → campaigns, companies, contacts |
| 11 | `inbound_messages` | id, company_id, campaign_id, from_address, subject, body, parsed | → companies, campaigns |
| 12 | `quotes` | id, company_id, substance_id, campaign_id, price, currency, unit, incoterms, moq, confidence | → companies, substances, campaigns |
| 13 | `manual_tasks` | id, task_type, title, status, assigned_to, completed_at | — |
| 14 | `audit_log` | id, action (indexed), object_type, object_id, details (JSON), created_at | — |
| 15 | `settings` | key (PK), value (JSON), updated_at | — |
| 16 | `document_templates` | id, doc_type, name, html_template, css_template, is_default | → generated_documents |
| 17 | `generated_documents` | id, doc_type, template_id, campaign_id, quote_id, file_path, status | → templates, campaigns, quotes |
| 18 | `raw_snapshots` | id, source_url, content_hash, fetched_at, fetch_status | — |
| 19 | `bulk_import_jobs` | id, filename, total_rows, valid_rows, invalid_rows, status | → bulk_import_items |
| 20 | `bulk_import_items` | id, job_id, row_number, cas_raw, cas_valid, substance_id, status | → jobs, substances |
| 21 | `substance_manufacturing_analyses` | id, substance_id, route_type, required_equipment (JSON), input_materials (JSON), cost_model (JSON) | → substances |
| 22 | `hs_code_entries` | id, hs_code (indexed), substance_id, description, source_database, confidence | → substances, tariff_rates |
| 23 | `tariff_rates` | id, hs_code_id, origin_country, destination_country, duty_rate_percent, duty_type | → hs_code_entries |
| 24 | `legal_use_descriptions` | id, substance_id, hs_code_id, description, category, destination_country | → substances, hs_code_entries |
| 25 | `substance_research` | id, substance_id (unique), status, total_suppliers_contacted, best_price | → substances, interactions, production_analyses |
| 26 | `supplier_interactions` | id, research_id, supplier_name, contact_channel, response_date, price_per_unit | → substance_research |
| 27 | `production_analyses` | id, research_id, method_name, equipment_needed (JSON), sub_products (JSON), total_production_cost_per_kg | → substance_research |

---

## 4. API — 16 grup, ~83 endpointy

| Grupa | Prefix | Liczba endpointów | Auth |
|-------|--------|-------------------|------|
| Health | `/health` | 1 | Nie |
| Auth | `/auth` | 3 | Nie (register/login) |
| Substances | `/substances` | 8 | Tak |
| Suppliers | `/suppliers` | 8 | Tak |
| Discovery | `/discovery` | 4 | Tak |
| Campaigns | `/campaigns` | 8 | Tak |
| Messages | `/messages` | 8 | Tak |
| Quotes | `/quotes` | 4 | Tak |
| Manual Tasks | `/manual-tasks` | 3 | Tak |
| Sourcing | `/sourcing` | 3 | Tak |
| Documents | `/documents` | 11 | Tak |
| Bulk Import | `/bulk-import` | 5 | Tak |
| Tariff | `/tariff` | 7 | Tak |
| Reports | `/reports` | 2 | Tak |
| Research | `/research` | 4 | Tak |
| Settings | `/settings` | 4 | Tak (oprócz defaults) |
| Conversation | `/conversation-simulator` | 1 | Tak |
| Safety Override | `/safety-override` | 2 | Admin token |

---

## 5. Serwisy (30)

| Serwis | Stan | Opis |
|--------|------|------|
| `AppSettingsService` | ✅ Produkcyjny | CRUD ustawień firmowych |
| `AuditLogService` | ✅ Produkcyjny | Log wszystkich akcji |
| `BulkImportService` | ✅ Produkcyjny | Parsowanie CSV/XLSX, walidacja CAS, tworzenie substancji |
| `CampaignOrchestrator` | ✅ Produkcyjny | Autonomiczne kampanie RFQ |
| `CasValidator` | ✅ Produkcyjny | Walidacja formatu CAS i checksum |
| `ChannelRouter` | ✅ Produkcyjny | Routing wiadomości do providerów (email/telegram/whatsapp) |
| `ConversationEngine` | ✅ Produkcyjny | Auto-followupy, wieloetapowe rozmowy |
| `ConversationSimulator` | ✅ Produkcyjny | Analiza intencji, red flag, brakujących pytań |
| `CustomsService` | ⚠️ Mock | HS code, cło — mock provider |
| `DocumentGenerator` | ✅ Produkcyjny | Generowanie LOI, PO, papieru firmowego (HTML/text) |
| `DocumentRebrander` | ❌ Wyłączony | Rebranding COA/SDS — 410 Gone |
| `FollowupGenerator` | ✅ Produkcyjny | Generowanie follow-upów |
| `HsCodeService` | ⚠️ Mock | HS code lookup — mock |
| `LegalUseService` | ⚠️ Mock | Sugestie legal use — mock |
| `PolicyEngine` | ✅ Produkcyjny | Ocena polityki dla wiadomości wychodzących |
| `ProductionAnalyzer` | ⚠️ Mock | Analiza produkcji — mock |
| `QuoteExtractor` | ✅ Produkcyjny | Ekstrakcja ofert z treści email |
| `RegulatoryScreeningService` | ✅ Produkcyjny | Screening regulacyjny substancji |
| `ReportGeneratorService` | ⚠️ Mock | Raporty PDF/Excel — mock |
| `ResearchService` | ⚠️ Mock | Dossier badawcze — mock |
| `ResponseCollectorService` | ⚠️ Mock | IMAP/Telegram polling — mock |
| `RFQGenerator` | ✅ Produkcyjny | Generowanie draftów RFQ |
| `SafetyOverrideService` | ✅ Produkcyjny | Test-only safety override (admin, TTL, nie w produkcji) |
| `SearchQueryGenerator` | ✅ Produkcyjny | Generowanie query wyszukiwawczych |
| `SourcingBatchService` | ✅ Produkcyjny | Batch sourcing CAS |
| `SubstanceAnalogsService` | ⚠️ Mock | Sugestie analogów — wbudowana baza |
| `SubstanceEnrichmentService` | ✅ Produkcyjny | PubChem/Mock enrichment |
| `SubstanceIntelligenceService` | ✅ Produkcyjny | Profil sourcingowy substancji |
| `SupplierClassifier` | ✅ Produkcyjny | Klasyfikacja i scoring dostawców |

---

## 6. Providerzy

### LLM
| Provider | Status |
|----------|--------|
| `MockLLMProvider` | ✅ Domyślny |
| `AnthropicProvider` (Claude Sonnet 4.6) | ✅ Wymaga `ANTHROPIC_API_KEY` |
| `OpenAIProvider` (GPT-4.1-mini) | ✅ Wymaga `OPENAI_API_KEY` |

### Search
| Provider | Status |
|----------|--------|
| `MockSearchProvider` | ✅ Domyślny |
| `ManualImportProvider` | ✅ URL-e od użytkownika |
| `GenericSearchProvider` | ❌ Szkielet |

### Marketplace
| Provider | Status |
|----------|--------|
| Alibaba | ⚠️ Draft/manual-only |
| Made-in-China | ⚠️ Draft/manual-only |
| Molbase | ⚠️ Draft/manual-only |
| IndiaMART | ⚠️ Draft/manual-only |

### Messaging
| Provider | Status |
|----------|--------|
| Email (SMTP + IMAP) | ✅ SMTP domyślny, fallback do mock |
| Formularze WWW | ⚠️ Szkielet (manual task) |
| Telegram Bot API | ⚠️ Szkielet |
| WhatsApp Business API | ⚠️ Szkielet |
| WeChat Official Account | ⚠️ Szkielet |
| Threema Gateway | ⚠️ Szkielet |
| Signal | ❌ Manual-only |
| Wickr | ❌ Manual-only |

---

## 7. Celery Worker — 13 tasków (wszystkie stuby)

| Task | Stan |
|------|------|
| `enrich_substance_task` | Stub — loguje "queued" |
| `discovery_task` | Stub |
| `fetch_page_task` | Stub |
| `extract_supplier_task` | Stub |
| `classify_supplier_task` | Stub |
| `generate_rfq_task` | Stub |
| `evaluate_policy_task` | Stub |
| `send_email_task` | Stub |
| `submit_form_task` | Stub |
| `poll_inbox_task` | Stub |
| `parse_inbound_message_task` | Stub |
| `extract_quote_task` | Stub |
| `generate_followup_task` | Stub |

---

## 8. Frontend — 16 widoków + 8 dialogów

### Widoki (w `components/views/`)
| Widok | Stan |
|-------|------|
| DashboardView | ✅ KPI + aktywna wiadomość + best quote |
| BulkImportView | ✅ Upload CSV/XLSX, process, enrich |
| SourcingView | ✅ Batch CAS + wybór kanałów |
| SubstanceIntelligenceView | ✅ Profil substancji + analiza kosztów |
| DocumentsView | ✅ LOI/PO + customs + analogi |
| SubstancesView | ✅ Tabela substancji |
| DiscoveryView | ✅ Discovery + import URL-i |
| SuppliersView | ✅ Karty dostawców |
| CampaignsView | ✅ Kampanie RFQ + wiadomości |
| InboxView | ✅ Inbound/outbound |
| QuotesView | ✅ Porównanie ofert + CSV export |
| TariffView | ✅ HS code + duty + legal use |
| ReportsView | ✅ Ranking + generowanie PDF |
| TasksView | ✅ Manual tasks + assign + complete |
| RebrandView | ✅ Informacja o wyłączonym rebrandingu |
| SettingsView | ✅ Pełna konfiguracja |

### Dialogi (w `Dialogs.tsx`)
| Dialog | Trigger |
|--------|---------|
| AddSubstanceDialog | Przycisk "Add CAS" |
| AddSupplierDialog | Przycisk "Add Supplier" |
| CreateCampaignDialog | (dostępny, niepodpięty bezpośrednio) |
| GenerateRfqDialog | Przycisk "Generate RFQ" |
| AutonomousRunDialog | Przycisk "Autonomous Run" |
| EnrichSubstancesDialog | Przycisk "Enrich selected" |
| ClassifySuppliersDialog | Przycisk "Classify" |
| CompleteTaskDialog | Przycisk "Complete" |

---

## 9. Znane luki i ograniczenia

| Luka | Priorytet | Opis |
|------|-----------|------|
| Celery taski to stuby | Wysoki | 13 tasków tylko loguje — nie wykonują realnej pracy |
| Brak PDF | Wysoki | WeasyPrint w zależnościach, ale dokumenty tylko HTML |
| Pokrycie testów 55% | Średni | Tylko 44 testy przy ~80 endpointach |
| SMTP nieprzetestowane | Średni | Kod jest, ale brak ścieżki testowej z realną konfiguracją |
| Marketplace tylko draft | Niski | Marketplace API to szkielety — wymagają realnych kont |
| Search provider mock | Niski | Brak legalnego Search API |
| Role model podstawowy | Średni | Tylko admin/user, brak granularnych uprawnień |
| Brak szablonów per kraj/branża | Niski | Jeden szablon LOI/PO dla wszystkich |

---

## 10. Podsumowanie stanu

| Obszar | Ocena |
|--------|-------|
| Backend API | ✅ Produkcyjny MVP (83 endpointy, 27 tabel) |
| Policy/Safety Engine | ✅ Solidny (wielopoziomowa polityka, audit log) |
| Frontend UI | ✅ Wszystkie 16 widoków funkcjonalne |
| Testy | ⚠️ 44/44 ale tylko 55% pokrycia |
| Worker/Celery | ❌ Stuby — nie wykonują pracy |
| Dokumenty PDF | ❌ Tylko HTML |
| Marketplace | ⚠️ Szkielety |
| LLM/Search | ⚠️ Domyślnie mock |
