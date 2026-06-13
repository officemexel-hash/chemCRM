# Chemical Sourcing RFQ CRM - dokument mozliwosci systemu

Data aktualizacji: 2026-06-13  
Status: produkcyjnie zorientowany MVP, gotowy do uruchomienia lokalnie i przez Docker Compose

## 1. Cel programu

Chemical Sourcing RFQ CRM to webowy system B2B procurement/CRM do legalnego sourcingu substancji chemicznych po numerze CAS. Program ma pomagac w przejsciu od listy substancji do uporzadkowanej kampanii RFQ, bazy dostawcow, draftow zapytan, porownania ofert, dokumentow handlowych i zadan manualnych.

System nie jest narzedziem do obchodzenia regulaminow portali, CAPTCHA, logowania, limitow, przepisow chemicznych ani odprawy celnej. Automatyzacja jest projektowana jako workflow biznesowy z audit logiem, zatwierdzaniem czlowieka i testowymi/mockowymi integracjami tam, gdzie realna wysylka wymaga konta, API lub zgody dostawcy.

## 2. Glowny workflow

1. Uzytkownik wpisuje lub importuje numer CAS.
2. System waliduje CAS i odrzuca niepoprawne numery.
3. System tworzy lub wzbogaca rekord substancji.
4. System generuje zapytania sourcingowe dla dostawcow, producentow i katalogow B2B.
5. System pozwala dodawac dostawcow recznie, z URL-em zrodla i dowodem kontaktu.
6. System klasyfikuje dostawce i liczy supplier score oraz risk score.
7. Uzytkownik tworzy kampanie RFQ.
8. System generuje profesjonalny draft RFQ.
9. Policy engine ocenia, czy wiadomosc jest draftem, wymaga approval, moze isc mockowo/automatycznie w niskim ryzyku, czy jest blokowana.
10. System zapisuje inbound message albo symulowana odpowiedz.
11. Quote extractor wyciaga cene, MOQ, Incoterms, lead time, dokumenty i red flagi.
12. Quote comparison pokazuje porownanie ofert.
13. System generuje dokumenty handlowe: papier firmowy, Letter of Intent i Purchase Order.
14. System tworzy audit log oraz manual tasks dla decyzji wymagajacych czlowieka.

## 3. Panel webowy

Frontend jest zbudowany w Next.js/React i ma nastepujace widoki:

- Dashboard: podsumowanie substancji, dostawcow, kampanii, odpowiedzi, ofert i alertow ryzyka.
- Import CAS: upload CSV/TSV/XLSX, walidacja i przetwarzanie listy numerow CAS.
- Sourcing: batch CAS, generowanie kampanii, zapytan i planu kanalow.
- Docs: generator LOI/PO, screening celny, legal-use drafts i analogi substancji.
- Substances: lista substancji i status manual review.
- Discovery: leady i dostawcy wykryci lub dodani do systemu.
- Suppliers: baza firm, kontakty, score i risk level.
- RFQ Campaigns: kampanie, wiadomosci, status policy decision.
- Inbox: inbound/outbound messages.
- Quotes: porownywarka ofert.
- Tariff: HS code, duty rate, legal-use text i Incoterms screening.
- Reports: ranking ofert i generowanie raportu kampanii.
- Manual Tasks: zadania dla czlowieka.
- Settings: dane firmy, osoby wysylajacej, pytania kontrolne, playbook odpowiedzi i test-only safety override.

## 4. Substancje chemiczne

System obsluguje:

- normalizacje numeru CAS,
- walidacje formatu CAS i cyfry kontrolnej,
- tworzenie substancji w bazie,
- wzbogacanie danych przez provider PubChem lub mock provider,
- nazwe podstawowa, IUPAC, wzor, mase molowa, PubChem CID, synonimy i EC number, jezeli sa dostepne,
- regulatory screening na poziomie MVP,
- status `requires_manual_review` dla substancji nieznanych, regulowanych albo niejednoznacznych,
- generowanie query sourcingowych dla CAS, nazwy i synonimow.

Przyklady poprawnych CAS w testach:

- `64-17-5`
- `7732-18-5`
- `50-00-0`

## 5. Masowy import CAS

Program ma widok i API do importu listy numerow CAS z pliku.

Mozliwosci:

- upload CSV/TSV/XLSX,
- parsowanie wierszy,
- walidacja CAS,
- zliczanie valid/invalid,
- tworzenie rekordow substancji,
- enrichment utworzonych substancji,
- tabela wynikow w UI.

Dodatkowy batch sourcing workflow pozwala z tekstu CSV utworzyc plan kampanii, queries i manual tasks dla wielu CAS naraz.

## 6. Substance Intelligence

System ma zakladke `Intelligence` i endpoint:

- `GET /substances/{substance_id}/intelligence`

Dla kazdej substancji system buduje karte wiedzy z istniejacych danych CRM:

- summary substancji,
- liczba dostawcow,
- liczba kontaktow,
- liczba ofert,
- liczba publicznych product offers,
- kraje dostawcow,
- najlepsza znaleziona cena,
- lista dostawcow zwiazanych z dana substancja,
- kontakty dostawcy z `source_url` i `evidence_text`,
- historia kontaktu outbound/inbound,
- statusy wiadomosci i decyzje policy engine,
- warunki ofert: cena, MOQ, Incoterms, lead time, payment terms, packaging, COA/SDS, REACH, ADR, UN number, HS code,
- brakujace pytania, np. brak HS code, brak packaging, brak Incoterms.

Karta pokazuje rowniez Incoterms per transport:

- drogowy,
- kolejowy,
- morski,
- lotniczy,
- kurierski,
- multimodalny.

## 7. Analiza produkcyjno-kosztowa

System ma bezpieczna analize feasibility dla substancji:

- `POST /substances/{substance_id}/manufacturing-analysis`
- `GET /substances/{substance_id}/manufacturing-analyses`

Analiza moze zapisac w CRM:

- target quantity,
- target grade,
- intended lawful use,
- destination country,
- route type na poziomie biznesowym,
- wysokopoziomowy process overview,
- klasy wymaganego sprzetu,
- kategorie surowcow lub polproduktow,
- cost drivers,
- cost model,
- zapytania sourcingowe dla surowcow/polproduktow,
- compliance notes,
- safety notes,
- blocked reasons,
- confidence.

Wazne ograniczenia:

- system nie generuje receptur syntezy,
- system nie podaje parametrow procesu, temperatur, cisnien, katalizatorow, wydajnosci ani instrukcji produkcyjnych,
- substancje wymagajace manual review, regulowane, restricted albo z krytycznymi flagami nie dostaja listy surowcow do dzialania,
- raw-material sourcing tworzy manual tasks, a nie automatyczne zamowienia.

Ta funkcja sluzy do decyzji procurementowej: czy bardziej oplaca sie kupic gotowy produkt, szukac toll manufacturer/contract manufacturer, czy zebrac oferty na polprodukty i opakowania.

## 8. Dostawcy

System ma model dostawcy z informacjami:

- nazwa firmy,
- strona WWW,
- kraj,
- adres,
- typ firmy,
- numery rejestrowe, VAT i EORI,
- supplier score,
- risk score,
- risk level,
- notatki,
- kontakty.

Kazdy kontakt powinien miec:

- kanal kontaktu,
- wartosc kontaktu,
- `source_url`,
- `evidence_text`,
- status zgody,
- opcjonalne `consent_evidence`.

## 9. Klasyfikacja dostawcow

Supplier classifier klasyfikuje firmy jako:

- manufacturer,
- authorized distributor,
- trader/broker,
- marketplace store,
- lab supplier,
- export agent,
- unknown,
- high risk.

Scoring uwzglednia m.in.:

- wlasna domene firmowa,
- status audited/verified,
- adres, rejestracje i telefon,
- SDS/COA/spec sheet,
- MOQ, lead time i Incoterms,
- odpowiedz z firmowego emaila,
- darmowy email jako jedyny kontakt,
- brak danych firmy,
- nacisk tylko na komunikator,
- odmowe SDS/COA/faktury,
- sugestie falszywych deklaracji albo obejscia prawa.

## 10. Discovery i search providers

System generuje uporzadkowane zapytania wyszukiwawcze, np.:

- `{CAS} supplier`,
- `{CAS} manufacturer`,
- `{CAS} bulk`,
- `{CAS} COA`,
- `{CAS} SDS`,
- `{primary_name} supplier`,
- `{primary_name} technical grade`,
- `{primary_name} REACH supplier Europe`,
- `{synonym} supplier`.

Dostepne providery:

- MockSearchProvider do testow,
- ManualImportProvider do recznie wklejonych URL-i,
- GenericSearchProvider jako adapter pod przyszle legalne Search API.

System celowo nie implementuje scrapingu Google bez API.

## 11. RFQ campaigns

Kampania RFQ zawiera:

- substancje,
- ilosc,
- kraj dostawy,
- wymagany grade,
- intended lawful use,
- wymagania dokumentacyjne,
- status,
- flage `auto_send_enabled`.

Generator RFQ tworzy profesjonalna wiadomosc z pytaniami o:

- tozsamosc produktu,
- CAS,
- grade i purity,
- COA,
- SDS/MSDS,
- spec sheet,
- TDS,
- producenta,
- kraj pochodzenia,
- production capacity,
- MOQ,
- cena za kg,
- price breaks,
- samples,
- lead time,
- shelf life,
- packaging,
- EXW/FOB/CIF/DAP/DDP,
- ADR/DG class,
- UN number,
- HS code,
- REACH,
- export restrictions,
- certyfikaty,
- warunki platnosci,
- fakture.

## 12. Policy engine

Policy engine jest centralnym modulem decyzyjnym dla komunikacji wychodzacej.

Mozliwe decyzje:

- `DRAFT_ONLY`,
- `REQUIRES_APPROVAL`,
- `ALLOW_AUTO_SEND`,
- `TEST_OVERRIDE_ALLOW`,
- `BLOCK`.

Reguly obejmuja:

- invalid CAS blokuje workflow,
- unknown/regulated substance wymaga approval,
- regulatory flags wymagaja review,
- restricted/blocked substance blokuje albo wymaga specjalnej manualnej decyzji,
- brak `source_url` lub `evidence_text` wymaga review,
- komunikator bez `consent_evidence` blokuje automatyzacje,
- Signal/Wickr sa manual-only w MVP,
- marketplace internal messaging wymaga review portalu i zadania manualnego,
- high risk supplier wymaga review albo blokady,
- fraud/evasion language blokuje workflow,
- free email jako jedyny kontakt wymaga weryfikacji,
- low-risk business email/form z publicznym zrodlem i `campaign.auto_send_enabled=true` moze przejsc do auto-send/mock send.

W aktualnym MVP realna sciezka wysylki w orkiestratorze uzywa mock providerow. Oznacza to, ze system testuje decyzje, statusy, audit log i workflow bez niekontrolowanej realnej wysylki zewnetrznej.

## 13. Test-only safety override

System ma mechanizm test-only safety override w Settings i API `/safety-override`.

Charakterystyka:

- wymaga konta admina,
- wymaga jawnego powodu,
- wymaga `confirm_test_only=true`,
- wygasa po czasie,
- jest zablokowany w `APP_ENV=production`,
- obejmuje tylko zdefiniowane miekkie kategorie testowe,
- nie sluzy do realnego wysylania na zewnatrz,
- nie sluzy do obchodzenia CAPTCHA, logowania, regulaminow, rejestracji kont ani twardych blokad.

Twarde blokady pozostaja jako ograniczenia systemowe:

- invalid CAS,
- fraud or evasion,
- restricted or blocked substance,
- messenger without consent,
- manual-only messenger,
- CAPTCHA or login bypass,
- portal terms bypass,
- automatic account registration,
- real external send.

## 14. Dokumenty handlowe

System generuje dokumenty na papierze firmowym na podstawie danych firmy z Settings.

### Papier firmowy

Zawiera:

- legal name,
- trading name,
- adres,
- kraj,
- numer rejestrowy,
- VAT,
- EORI,
- website,
- email,
- telefon,
- reference number,
- date.

Endpoint:

- `POST /documents/letterhead`

### Letter of Intent

LOI zawiera:

- dane kupujacego,
- dane odbiorcy,
- nazwe substancji,
- CAS,
- ilosc,
- destination country,
- intended lawful use,
- dodatkowe notatki,
- warunki due diligence,
- wymog dokumentow,
- non-binding disclaimer.

Endpoint:

- `POST /documents/letter-of-intent`

### Professional Order / Purchase Order

PO zawiera:

- numer PO,
- dostawce,
- adres dostawcy,
- kontakt,
- delivery address,
- termin dostawy,
- produkt,
- CAS,
- ilosc,
- unit price,
- currency,
- payment terms,
- transport mode,
- Incoterms,
- macierz odpowiedzialnosci,
- HS code,
- szacunkowe clo,
- legal-use description,
- special requirements.

Endpoint:

- `POST /documents/purchase-order`

Dokumenty sa zapisywane w CRM, maja ID i mozna je pobrac przez:

- `GET /documents/{document_id}/download`

Backend probuje wygenerowac PDF przez WeasyPrint, a w razie problemu zwraca HTML.

## 15. Transport i Incoterms

System podpowiada Incoterms wedlug transportu:

- sea: `FOB`, `CIF`, `CFR`, `FAS`,
- air: `FCA`, `CPT`, `CIP`, `DAP`,
- road: `FCA`, `CPT`, `DAP`, `DDP`,
- rail: `FCA`, `CPT`, `DAP`,
- courier: `DAP`, `DDP`,
- multimodal: `EXW`, `FCA`, `CPT`, `CIP`, `DAP`, `DDP`.

Macierz odpowiedzialnosci pokazuje, kto odpowiada za:

- transport,
- insurance,
- export clearance,
- import clearance,
- unloading,
- risk transfer.

Endpoint:

- `GET /documents/incoterms-guide?transport_mode=sea`

## 16. Cło, HS code i legal-use drafts

System ma dwa poziomy informacji celnej:

1. `Tariff` view i endpointy `/tariff/*` do pracy z tabela HS/duty/legal use w bazie.
2. `Docs` view i `/documents/customs-duty` do szybkiego screeningu pod dokument LOI/PO.

System moze zwrocic:

- HS code suggestion,
- opis HS,
- duty estimate,
- VAT note,
- additional taxes notes,
- legal-use suggestions,
- regulatory notes,
- official source URL,
- confidence,
- `manual_review_required`,
- assumptions.

Wazne ograniczenie:

System nie wydaje finalnej klasyfikacji celnej. HS code, duty estimate i opis zastosowania sa materialem do review. Finalna klasyfikacja powinna byc potwierdzona w oficjalnej bazie, przez brokera celnego albo kompetentna osobe.

## 17. Analogi i zamienniki substancji

Modul analogow sugeruje potencjalne zamienniki:

- strukturalne,
- funkcjonalne,
- nazwowe,
- aplikacyjne,
- potencjalnie tansze.

Dla kazdego analogu system pokazuje:

- CAS,
- nazwe,
- IUPAC,
- wzor,
- podobienstwo strukturalne,
- podobienstwo funkcjonalne,
- wskazanie cenowe,
- zalety,
- wady,
- podstawe podobienstwa,
- flage `requires_validation`.

Wazne ograniczenie:

Analogi nie sa automatyczna rekomendacja zakupu. Kazdy zamiennik wymaga walidacji jakosciowej, regulacyjnej, procesowej i bezpieczenstwa.

Endpoint:

- `POST /documents/substance-analogs`

## 18. Email, formularze, marketplace i komunikatory

Stan sprawdzony z kodem w MVP:

- Email: aktywna sciezka kampanii i endpointow wysylki uzywa mock send path; `SMTPEmailSender` istnieje jako modul integracyjny, ale nie jest domyslna sciezka produkcyjna.
- IMAP: `IMAPEmailReceiver` i `ResponseCollectorService.collect_email_replies()` istnieja do inbound collection, ale worker `poll_inbox_task` jest nadal szkieletem logujacym kolejke.
- Telegram: `TelegramBotConnector` ma metody send/getUpdates i `ResponseCollectorService.collect_telegram_replies()` obsluguje inbound, ale nie jest domyslnie wpiety w kampanie/outreach.
- WhatsApp: `WhatsAppBusinessConnector` ma szkic send przez Twilio Business API, ale nie jest wpiety w aktywna sciezke kampanii/outreach.
- Threema/WeChat: klasy istnieja, ale dziedzicza po szkicu WhatsApp i wymagaja przepisania pod realne oficjalne API przed uzyciem.
- ChannelRouter: istnieje i potrafi kierowac email/Telegram/WhatsApp, ale aktywne endpointy i `CampaignOrchestrator` go obecnie nie uzywaja.
- Formularze WWW: detector i submitter sa szkieletem pod Playwright; CAPTCHA/login/terms tworza manual task albo blokade manual-review.
- Alibaba: skeleton connector, draft/manual/API-only.
- Made-in-China: skeleton connector, draft/manual/API-only.
- Molbase: skeleton connector, draft/manual/API-only.
- IndiaMART: skeleton connector/channel planning, draft/manual/API-only.
- Signal/Wickr: manual task only w MVP.

System nie rejestruje sam kont na portalach i nie obsluguje prywatnych komunikatorow jako cold outreach. Takie przypadki sa modelowane jako zadania manualne albo przyszle oficjalne/API-only integracje.

## 19. Conversation simulator i playbook

W Settings mozna skonfigurowac:

- dane firmy,
- osobe wysylajaca,
- kontrolowane pytania,
- reguly response playbook,
- scenariusze treningowe.

Conversation simulator przyjmuje wiadomosc dostawcy i zwraca:

- detected intent,
- recommended action,
- response subject,
- response body,
- matched rules,
- missing controlled questions,
- red flags,
- czy powstaje manual task,
- czy odpowiedz ma byc blokowana,
- czy wymagany jest approval.

To sluzy do trenowania reakcji operatora i budowania draftow, nie do samodzielnego prowadzenia realnych rozmow bez policy engine.

## 20. Quote extraction i quote comparison

Quote extractor waliduje JSON przez Pydantic i wyciaga z odpowiedzi:

- supplier type,
- potwierdzony CAS,
- grade,
- purity,
- MOQ,
- ceny,
- walute,
- jednostke,
- Incoterms,
- lead time,
- payment terms,
- sample availability,
- packaging,
- COA/SDS,
- REACH,
- ADR,
- UN number,
- HS code,
- shelf life,
- certificates,
- production capacity,
- red flags,
- missing questions,
- confidence.

Quote comparison pokazuje:

- supplier,
- country,
- price/kg,
- currency,
- MOQ,
- Incoterms,
- lead time,
- payment terms,
- COA/SDS,
- REACH,
- ADR,
- risk level,
- confidence,
- best quote marker.

## 21. Raporty

Widok Reports pozwala:

- wybrac kampanie,
- pobrac ranking ofert,
- wygenerowac raport,
- pobrac dokument raportu.

Ranking uwzglednia:

- price score,
- supplier quality score,
- risk score,
- document completeness,
- total score,
- rekomendacje.

## 22. Audit log i manual tasks

Audit log zapisuje kluczowe akcje:

- utworzenie kampanii,
- enrichment substancji,
- discovery leadu,
- klasyfikacje,
- utworzenie wiadomosci,
- decyzje policy engine,
- approval,
- wysylke mock/simulation,
- odbior,
- ekstrakcje quote,
- zmiane risk score,
- manual task,
- wygenerowanie dokumentu.

Manual tasks obejmuja m.in.:

- approval needed,
- CAPTCHA/login required,
- messenger contact manual,
- high risk supplier,
- regulatory review,
- policy blocked,
- missing contact evidence,
- marketplace terms review.

## 23. API

Glowne grupy endpointow:

- Auth: `/auth/register`, `/auth/login`, `/auth/me`
- Substances: `/substances`
- Substance intelligence: `/substances/{id}/intelligence`, `/substances/{id}/manufacturing-analysis`
- Suppliers: `/suppliers`
- Discovery: `/discovery/*`
- Bulk import: `/bulk-import/*`
- Sourcing: `/sourcing/batches`
- Campaigns: `/campaigns`
- Messages: `/messages/*`
- Quotes: `/quotes`
- Manual tasks: `/manual-tasks`
- Audit: `/audit-log`
- Settings: `/settings/app`
- Safety: `/safety-override`
- Conversation: `/conversation-simulator/simulate`
- Tariff: `/tariff/*`
- Documents: `/documents/*`
- Reports: `/reports/*`
- Health: `/health`

## 24. Technologie

Backend:

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- PostgreSQL
- Redis
- Celery
- httpx
- BeautifulSoup
- Playwright skeletons
- pytest

Frontend:

- Next.js
- React
- TypeScript
- Tailwind CSS
- Lucide React

Deployment:

- Docker Compose,
- osobne serwisy backend, frontend, postgres, redis, worker, scheduler,
- konfiguracja przez `.env`,
- gotowosc pod reverse proxy Nginx/Caddy.

## 25. Jak uruchomic

Docker:

```bash
docker compose up --build
```

Backend lokalnie:

```powershell
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Frontend lokalnie:

```powershell
cd frontend
npm.cmd run dev
```

Adresy:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## 26. Jak testowac

Backend:

```powershell
cd backend
..\.venv\Scripts\python -m pytest
```

Frontend build:

```powershell
cd frontend
npm.cmd run build
```

Test manualny w UI:

1. Otworz `http://localhost:3000`.
2. Wejdz w `Docs`.
3. Kliknij `Customs`.
4. Kliknij `Analogs`.
5. Kliknij `LOI`.
6. Kliknij `PO`.
7. Pobierz `Download LOI` lub `Download PO`.
8. Wejdz w `Import CAS` i przetestuj upload CSV/XLSX.
9. Wejdz w `Intelligence`, wczytaj profil substancji i uruchom `Analyze Cost`.
10. Wejdz w `Tariff` i sprawdz HS/duty screening.
11. Wejdz w `Reports` i wygeneruj ranking/raport dla kampanii.

## 27. Rzeczy celowo niezaimplementowane

System celowo nie implementuje:

- obchodzenia CAPTCHA,
- obchodzenia logowania,
- obchodzenia rate limits,
- ukrywania automatyzacji przed portalami,
- scrapingu Google bez API,
- masowego spamu,
- cold outreach na prywatne konta komunikatorow,
- samodzielnej rejestracji kont na portalach,
- obchodzenia regulaminow marketplace,
- falszowania faktur, deklaracji celnych, opisow transportowych albo dokumentow,
- przepisywania lub rebrandingu dostawczych COA/SDS/MSDS jako wlasnych dokumentow,
- generowania instrukcji syntezy, parametrow procesu albo receptur produkcji chemicznej,
- pomocy w obchodzeniu przepisow dotyczacych substancji regulowanych,
- automatycznego zamawiania substancji,
- automatycznych platnosci,
- finalizacji transakcji.

## 28. Najblizsze sensowne rozszerzenia

0. Reconciliation statusu przed wiekszym portem albo integracja: sprawdzic kod, testy, endpointy, workery i UI zamiast wierzyc opisom README/PLAN.
1. Eksport PDF/DOCX z szablonami firmowymi i uploadem logo.
2. Oficjalna integracja TARIC/HTS albo workflow z brokerem celnym.
3. Legalne Search API zamiast mock/manual search.
4. Realne SMTP/IMAP po konfiguracji SPF/DKIM/DMARC.
5. Oficjalne API marketplace, jezeli dany portal to udostepnia.
6. Wiecej danych analogow z legalnych baz chemicznych.
7. Zaawansowany scoring dostawcow z historią odpowiedzi i jakoscia dokumentow.
8. Role i permission model dla zespolu procurement/compliance.
9. Eksport raportow dla zarzadu i dzialu zakupow.
10. Szablony LOI/PO/RFQ per firma, branza i kraj.

Uwaga po reconciliation 2026-06-13: `ChannelRouter`, SMTP, IMAP, Telegram i WhatsApp maja czesciowe moduly kodowe, ale nie sa jeszcze aktywna domyslna sciezka kampanii/outreach. Przed wlaczeniem tych modulow trzeba podjac osobna decyzje architektoniczna, dodac testy policy path i zaktualizowac README oraz ROADMAP.
