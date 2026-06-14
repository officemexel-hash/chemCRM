# Chemical Sourcing RFQ CRM — Instrukcja obsługi

## Uruchomienie

```bash
# Docker (zalecane)
git clone https://github.com/officemexel-hash/chemCRM.git
cd chemCRM
cp .env.example .env
docker compose up --build -d
```

**Adresy:**
- Panel: `http://localhost:3000`
- API: `http://localhost:8000`
- Dokumentacja API: `http://localhost:8000/docs`

**Demo seed (opcjonalnie):**
```bash
docker exec chemcrm-backend-1 sh -c "PYTHONPATH=/app python /app/scripts/seed_demo.py"
# Login: demo@example.com / ChangeMe123!
```

---

## Przegląd panelu

Panel składa się z 16 zakładek w lewym sidebarze:

| Zakładka | Do czego służy |
|----------|----------------|
| **Dashboard** | Podsumowanie: liczba substancji, dostawców, kampanii, ofert, alertów ryzyka. Pokazuje ostatnią aktywną wiadomość RFQ i najlepszą ofertę. |
| **Import CAS** | Masowy import numerów CAS z pliku CSV/XLSX. Upload → Process → Enrich. |
| **Sourcing** | Batch sourcing: wklej tabelę CAS, wybierz kanały, system stworzy kampanie, query i manual taski. |
| **Intelligence** | Karta wiedzy o substancji: dostawcy, kontakty, oferty, historia cen, Incoterms, analiza kosztów produkcji. |
| **Docs** | Generator dokumentów: Letter of Intent (LOI) i Purchase Order (PO). Customs lookup, wyszukiwanie analogów. |
| **Substances** | Lista wszystkich substancji w bazie. Przyciski: Add CAS (dodaj nową), Enrich selected (wzbogać z PubChem). |
| **Discovery** | Wyniki discovery dostawców. Przyciski: Start Discovery, Import URLs. |
| **Suppliers** | Lista dostawców z scoringiem i poziomem ryzyka. Przyciski: Add Supplier, Classify. |
| **RFQ** | Kampanie RFQ. Przyciski: Generate RFQ (stwórz draft dla dostawcy), Autonomous Run (uruchom kampanię automatycznie). |
| **Inbox** | Skrzynka: wiadomości przychodzące i wychodzące. |
| **Quotes** | Porównywarka ofert: cena, MOQ, Incoterms, lead time, dokumenty, ryzyko. Przyciski: Export CSV, Mark reviewed. |
| **Tariff** | Screening celny: HS code, stawki celne, legal use descriptions. |
| **Reports** | Raporty: ranking dostawców, generowanie PDF. |
| **Tasks** | Zadania manualne do wykonania. Przyciski: Complete, Assign. |
| **Rebrand** | Informacja: rebranding COA/SDS dostawcy jest wyłączony (compliance). |
| **Settings** | Konfiguracja: dane firmy, osoba wysyłająca, kontrolowane pytania RFQ, playbook odpowiedzi, symulator rozmów, safety override, logo, PubChem toggle. |

---

## Typowy workflow

### 1. Dodaj substancję
1. Wejdź w **Substances**
2. Kliknij **Add CAS**
3. Wpisz numer CAS (np. `64-17-5`) i opcjonalnie nazwę
4. Kliknij **Create Substance**
5. (Opcjonalnie) Zaznacz substancję i kliknij **Enrich selected** — pobierze dane z PubChem

### 2. Dodaj dostawcę
1. Wejdź w **Suppliers**
2. Kliknij **Add Supplier**
3. Wypełnij nazwę firmy, stronę, kraj, typ
4. Dodaj kontakt (email/form/phone) z URL-em źródłowym i dowodem
5. Kliknij **Create Supplier**
6. (Opcjonalnie) Zaznacz dostawcę i kliknij **Classify** — system oceni ryzyko

### 3. Stwórz kampanię RFQ
1. Wejdź w **RFQ**
2. Kliknij **Generate RFQ**
3. Wybierz kampanię (lub najpierw stwórz nową przez **Create Campaign**)
4. Wybierz dostawcę i kontakt
5. Kliknij **Generate RFQ Draft**
6. System wygeneruje draft, oceni polityką (policy_decision) i pokaże status

### 4. Uruchom kampanię automatycznie
1. W **RFQ** kliknij **Autonomous Run**
2. Wybierz kampanię
3. Zaznacz **Dry run** (bez wysyłki) lub odznacz (mock send)
4. Kliknij **Run Autonomous Campaign**
5. System pokaże: ile wygenerowano, ile wymaga approval, ile zablokowano

### 5. Porównaj oferty
1. Wejdź w **Quotes**
2. Zobaczysz tabelę z cenami, MOQ, Incoterms, dokumentami i ryzykiem
3. Najlepsza oferta oznaczona ✓
4. Kliknij **Export CSV** żeby pobrać dane

### 6. Wygeneruj dokumenty
1. Wejdź w **Docs**
2. Wypełnij dane zamówienia (dostawca, substancja, ilość, cena, transport, Incoterms)
3. Kliknij **Customs** żeby sprawdzić HS code i cło
4. Kliknij **LOI** — wygeneruje Letter of Intent
5. Kliknij **PO** — wygeneruje Purchase Order
6. Kliknij **Download LOI** / **Download PO** żeby pobrać

### 7. Skonfiguruj firmę
1. Wejdź w **Settings**
2. Wypełnij **Company Identity** (nazwa, adres, VAT, EORI, strona)
3. Wypełnij **Sender Persona** (imię, tytuł, email, telefon)
4. Opcjonalnie: wgraj logo firmy
5. Opcjonalnie: włącz **Use real PubChem enrichment**
6. Kliknij **Save**

---

## Konfiguracja SMTP (dla realnej wysyłki email)

W pliku `.env` ustaw:
```env
SMTP_HOST=smtp.twoja-firma.pl
SMTP_PORT=587
SMTP_USERNAME=nadawca@twoja-firma.pl
SMTP_PASSWORD=twoje-haslo
SMTP_FROM=nadawca@twoja-firma.pl
SMTP_USE_TLS=true
```

Po restarcie Dockera system będzie wysyłał emaile przez SMTP. Jeśli SMTP nie jest skonfigurowane, automatycznie używa mock send (bez realnej wysyłki).

---

## Safety Override (tryb testowy)

1. W **Settings** przewiń na dół do **Test-Only Safety Override**
2. Wpisz token admina (Bearer token z logowania)
3. Wpisz powód
4. Kliknij **Enable test override**
5. System poluzuje politykę dla testów (ALE NIGDY nie odblokowuje: invalid CAS, fraud/evasion, real external send, CAPTCHA bypass, portal login)

Override wygasa po ustawionym TTL. Niedostępny w `APP_ENV=production`.

---

## Masowy import CAS

1. Wejdź w **Import CAS**
2. Wybierz plik CSV/XLSX (pierwsza kolumna = CAS)
3. Kliknij **Upload** → **Process** → **Enrich**
4. System pokaże tabelę: które CAS są valid/invalid, status, błędy

---

## Batch Sourcing

1. Wejdź w **Sourcing**
2. Wklej tabelę CAS w formacie `CAS,quantity`
3. Ustaw ilość, kraj, grade, intended use
4. Wybierz kanały (search, form, marketplace, messengers)
5. Kliknij **Import CAS**
6. System utworzy substancje, kampanie, zapytania i manual taski

---

## Symulator rozmów

1. W **Settings** przewiń do **Conversation Simulator**
2. Wpisz przykładową wiadomość od dostawcy
3. Kliknij **Simulate response**
4. System pokaże: wykrytą intencję, rekomendowaną akcję, odpowiedź, braki, red flagi

To narzędzie treningowe — nie wysyła realnych wiadomości.
