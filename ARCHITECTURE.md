# Chemical Sourcing RFQ CRM — Architektura

## Diagram przepływu danych

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  DashboardApp → 16 Views → Widgets/Dialogs → API calls          │
│  localhost:3000                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                   BACKEND API (FastAPI :8000)                     │
│                                                                   │
│  main.py                                                          │
│  ├── Middleware: CORS, TrustedHost, SecurityHeaders               │
│  ├── StaticFiles: /storage (logo)                                 │
│  └── Routers (16 grup, ~83 endpointy)                             │
│       │                                                           │
│       ├── Auth (register/login/me) ──► deps.py (JWT-like token)  │
│       ├── Substances ──► SubstanceEnrichmentService               │
│       │                   ├── MockSubstanceProvider               │
│       │                   └── PubChemPugRestProvider (jeśli       │
│       │                        pubchem_enabled=true)              │
│       ├── Suppliers ──► SupplierClassifier                        │
│       ├── Campaigns ──► CampaignOrchestrator                      │
│       │                  ├── RFQGenerator                         │
│       │                  ├── PolicyEngine (BLOCK/APPROVE/SEND)    │
│       │                  └── ChannelRouter                        │
│       ├── Messages ──► QuoteExtractor, PolicyEngine               │
│       ├── Documents ──► DocumentGenerator                         │
│       ├── Tariff ──► HsCodeService, LegalUseService               │
│       ├── Sourcing ──► SourcingBatchService                       │
│       ├── Reports ──► ReportGeneratorService                      │
│       ├── Research ──► ResearchService                            │
│       ├── Discovery ──► ManualTask (MVP)                          │
│       ├── Settings ──► AppSettingsService (DB-backed)             │
│       └── Safety ──► SafetyOverrideService                        │
│                                                                   │
└─────────────┬────────────────────────────┬────────────────────────┘
              │                            │
              ▼                            ▼
┌─────────────────────┐     ┌──────────────────────────────┐
│   PostgreSQL :5432   │     │      Redis :6379              │
│   27 tabel           │     │   Celery broker + backend     │
│   SQLAlchemy +       │     │   + result backend            │
│   Alembic            │     └──────────┬───────────────────┘
└─────────────────────┘                │
                                        ▼
                          ┌──────────────────────────────┐
                          │  Celery Worker + Scheduler    │
                          │  13 tasków (obecnie stuby)    │
                          │  celery beat (harmonogram)    │
                          └──────────────────────────────┘
```

## Struktura katalogów

```
chemCRM/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── api/
│   │   │   ├── deps.py                # Auth dependencies
│   │   │   └── routes/                # 16 plików routerów
│   │   │       ├── health.py
│   │   │       ├── auth.py
│   │   │       ├── substances.py
│   │   │       ├── suppliers.py
│   │   │       ├── discovery.py
│   │   │       ├── campaigns.py
│   │   │       ├── conversation.py
│   │   │       ├── messages.py
│   │   │       ├── quotes.py
│   │   │       ├── manual_tasks.py
│   │   │       ├── audit.py
│   │   │       ├── app_settings.py
│   │   │       ├── safety.py
│   │   │       ├── sourcing.py
│   │   │       ├── documents.py
│   │   │       ├── bulk_import.py
│   │   │       ├── tariff.py
│   │   │       ├── reports.py
│   │   │       └── research.py
│   │   ├── db/
│   │   │   ├── base.py                # SQLAlchemy Base
│   │   │   ├── session.py             # Session factory
│   │   │   ├── models/                # 27 modeli w 15 plikach
│   │   │   └── migrations/            # Alembic
│   │   ├── services/                  # 30 serwisów
│   │   ├── schemas/                   # Pydantic v2
│   │   ├── core/                      # config, security, middleware, logging
│   │   ├── llm/providers/             # mock, anthropic, openai
│   │   ├── search_providers/          # mock, generic, manual_import
│   │   ├── marketplaces/              # alibaba, made_in_china, molbase, indiamart
│   │   ├── messaging/                 # email, forms, messengers
│   │   ├── extractors/                # page_fetcher, robots, contact, supplier
│   │   ├── browser/                   # Playwright manager
│   │   ├── utils/                     # hashing, text, urls
│   │   └── workers/                   # Celery app + tasks
│   ├── scripts/
│   │   ├── seed_demo.py               # Demo data seeder
│   │   └── smoke_test_frontend.py     # Playwright smoke test
│   ├── tests/                         # 44 pytest testów
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root HTML shell
│   │   │   ├── page.tsx               # Entry → DashboardApp
│   │   │   └── globals.css            # Tailwind
│   │   ├── components/
│   │   │   ├── DashboardApp.tsx       # Main SPA (tabs + dialog state)
│   │   │   ├── Dialogs.tsx            # 8 modalnych dialogów
│   │   │   ├── Widgets.tsx            # Shared UI components
│   │   │   ├── NewViews.tsx           # RebrandView
│   │   │   └── views/                 # 15 widoków
│   │   ├── lib/
│   │   │   └── api.ts                 # API client + demo data
│   │   └── types/
│   │       └── api.ts                 # TypeScript types
│   ├── Dockerfile
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml                 # 6 kontenerów
├── .env.example
├── README.md
├── CHEMCRM_CAPABILITIES.md
├── SYSTEM_AUDIT.md
├── ARCHITECTURE.md
└── USER_GUIDE.md
```

## Kluczowe decyzje architektoniczne

### 1. Bezpieczeństwo i compliance od początku
- Policy Engine ocenia każdą wiadomość wychodzącą przed wysyłką
- 4 stany: `BLOCK` > `REQUIRES_APPROVAL` > `ALLOW_AUTO_SEND` > `TEST_OVERRIDE_ALLOW`
- Safety override tylko dla admina, z TTL, niedostępny w produkcji
- Audit log zapisuje każdą istotną akcję

### 2. Stateless auth (HMAC tokeny)
- Brak zależności od JWT — własna implementacja HMAC-SHA256
- Opcjonalna autoryzacja (flaga `AUTH_REQUIRED`)
- Pierwszy zarejestrowany użytkownik = admin

### 3. Provider abstraction
- LLM: `LLMProvider` protocol → Mock / Anthropic / OpenAI
- Search: `SearchProvider` protocol → Mock / Manual / Generic
- Marketplace: `MarketplaceConnector` protocol → Alibaba / IndiaMART / Made-in-China / Molbase
- Messenger: `MessengerConnector` protocol → Telegram / WhatsApp / WeChat / Threema

### 4. Graceful degradation
- SMTP → fallback do Mock gdy nie skonfigurowany
- PubChem → fallback do Mock (chyba że `pubchem_enabled=true`)
- WeasyPrint → fallback do HTML gdy brak
- Playwright → opcjonalny (sprawdza `HAS_PLAYWRIGHT`)

### 5. Frontend: SPA bez routera
- DashboardApp to jedna strona (Next.js App Router tylko `/`)
- Nawigacja przez `activeTab` state — błyskawiczne przełączanie
- Wszystkie dane ładowane przy starcie (można odświeżyć `refresh()`)
- Dialogi renderowane warunkowo przy `dialog !== null`

### 6. Docker: 6 kontenerów
```
postgres:16-alpine  ← dane
redis:7-alpine      ← cache + celery broker
backend             ← FastAPI (workers=1)
worker              ← Celery worker
scheduler           ← Celery beat
frontend            ← Next.js (production)
```
