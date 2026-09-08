# ParKING

ParKING je Flask web aplikacija za oglašavanje i rezervaciju privatnih parkirnih mjesta. Korisnik može pretražiti parking za određeni termin, provjeriti dostupnost, vidjeti vremenske podatke za lokaciju, rezervirati parking i upravljati svojim rezervacijama.

## Glavne funkcionalnosti

- registracija, prijava i odjava korisnika
- CRUD nad parkirnim mjestima
- rezervacije s provjerom preklapanja termina
- pretraga dostupnih parkinga po lokaciji, vremenu i maksimalnoj cijeni
- sortiranje po cijeni i nazivu
- 24-satni unos datuma i vremena pomoću Flatpickra
- SQLite + SQLAlchemy
- administratorski CRUD nad korisnicima i rezervacijama
- administratorsko upravljanje promo kodovima
- HR/EN sučelje
- INI postavke u `config.ini`
- JSON CRUD korisničkih vozila u `data/vehicles.json`
- BLOB fotografije parkinga u bazi
- PDF potvrda rezervacije
- vlastiti binarni format povijesti pretraga (`PKSR`)
- AES-GCM šifrirane privatne pristupne upute parkinga
- SHA-256 provjera integriteta rezervacije bez soli i papra
- SHA-256 promo kodovi s promjenjivom soli i paprom 0–255
- Open-Meteo vremenski podaci uz stvarne parkinge
- `ThreadPoolExecutor` + `threading.Lock`
- vlastiti REST API s Bearer autentifikacijom i autorizacijom
- vlastita C++ dinamička biblioteka (`.so`) za izračun service fee naknade

## Dostupnost parkinga prema terminu

Parking se prikazuje ako nema `ACTIVE` rezervaciju koja se preklapa s traženim intervalom:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

`CANCELLED` rezervacije ne blokiraju dostupnost. Termin odabran na pretrazi prenosi se kroz **Detalji → Rezerviraj**.

## Moja vozila — JSON CRUD

Podstranica **Moja vozila** omogućuje prijavljenom korisniku dodavanje, prikaz, uređivanje i brisanje vozila. Podaci se spremaju u:

```text
data/vehicles.json
```

Svaki zapis sadrži `id`, `user_id`, naziv vozila i registracijsku oznaku. Funkcije za čitanje i CRUD nalaze se u `vehicle_store.py`.

## Promo kodovi — SHA-256, promjenjiva sol i papar

Administrator na **Promo kodovi** može kreirati npr. `PARK10` i odrediti postotak popusta. Izvorni promo kod se ne sprema u bazu.

`promo_code_hash.py` generira promjenjivu sol iz ID-a promo zapisa:

```text
SHA256("ParKING-promo-salt:<promo_id>")[0:16]
```

Sol se ne sprema. Pri stvaranju sažetka slučajno se bira jedan papar iz raspona `0–255`; ni papar se ne sprema. U tablici `promo_codes` ostaju samo SHA-256 sažetak, postotak popusta i status aktivnosti.

Kod rezervacije korisnik može upisati promo kod. Aplikacija za svaki kandidat prolazi **svih 256 mogućih vrijednosti papra** i tek nakon završetka cijelog raspona prihvaća podudaranje. Uspješna rezervacija sprema `promo_code_id` i `discount_percent`, a `Reservation.total_price()` vraća konačnu cijenu nakon popusta.

Ova funkcionalnost je odvojena od SHA-256 provjere integriteta rezervacije, gdje se sol i papar namjerno ne koriste.

## AES-GCM pristupne upute parkinga

Vlasnik pri dodavanju ili uređivanju parkinga može unijeti privatne pristupne upute, primjerice uputu za ulaz ili oznaku parkirnog mjesta. Upute se **ne spremaju kao čitljiv tekst**.

`parking_access_crypto.py` prije spremanja koristi AES-GCM. Ključ se deterministički izvodi iz aplikacijskog `SECRET_KEY` i ID-a parkinga, a za svako šifriranje generira se novi slučajni nonce. U tablici `parking_spots` sprema se samo binarni sadržaj u polju:

```text
access_instructions BLOB
```

Javni detalji parkinga ne prikazuju privatne upute. Na stranici **Moje rezervacije** aplikacija dohvaća samo rezervacije prijavljenog korisnika i dešifrira pristupne upute samo za `ACTIVE` rezervacije. `CANCELLED` rezervacije ih ne prikazuju.

## SHA-256 integritet rezervacije

Na **Moje rezervacije → SHA-256** računa se obični SHA-256 nad stabilnim prikazom stvarnih podataka rezervacije: ID rezervacije, korisnik, parking, lokacija, termin, status, cijena po satu, eventualni promo popust i ukupna cijena.

Za ovu provjeru integriteta namjerno se **ne koriste sol ni papar**. Isti podaci daju isti kontrolni otisak, a promjena podataka mijenja otisak.

## Vremenski podaci i dretve

Open-Meteo podaci prikazuju se uz parkinge. Grad se izdvaja iz lokacije, a po potrebi se geokodira preko Open-Meteo Geocoding API-ja.

**Test → Dretve** koristi iste Open-Meteo forecast zahtjeve kroz isti `ThreadPoolExecutor` s:

```text
max_workers = 1
max_workers = 3
```

Koordinate se razriješe prije mjerenja. Zadnji praktični test dao je:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

`threading.Lock` štiti zajednički `_request_log` i kratke pristupe geocode cacheu.

## Povijest pretraga i vlastiti binarni format

Valjane pretrage prijavljenog korisnika spremaju se u `data/search_history.bin`. Format koristi vlastito `PKSR` zaglavlje i podržava ponavljanje spremljene pretrage.

## Dinamička biblioteka za service fee

`native/service_fee.cpp` sadrži klasu `ServiceFeeCalculator` s metodama `calculateFee()` i `calculateTotalFees()`. Docker build stvara:

```text
native/libservice_fee.so
```

`service_fee.py` učitava biblioteku pomoću `ctypes`. Na **Admin rezervacije** prikazuju se pojedinačni i ukupni service fee izračuni za `ACTIVE` rezervacije.

## Vlastiti REST servis

Glavna web aplikacija radi na portu `5000`, a zasebna REST Flask aplikacija na portu `5001`:

```text
run.py      → web aplikacija → 5000
api_app.py  → REST API       → 5001
```

API izlaže `/api/parkings` i `/api/reservations` te koristi Bearer token autentifikaciju i autorizaciju.

## Struktura projekta

```text
ParKING/
├── app.py
├── run.py
├── api_app.py
├── start.sh
├── models.py
├── parking_availability.py
├── parking_access_crypto.py
├── vehicle_store.py
├── binary_store.py
├── hash_demo.py
├── promo_code_hash.py
├── promo_web.py
├── parallel_tasks.py
├── service_fee.py
├── native/
│   └── service_fee.cpp
├── translations.py
├── config.ini
├── seed.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README_IMPLEMENTIRANO.md
├── OBRANA.md
├── AUDIT.md
├── templates/
├── static/
├── data/
└── exports/
```

## Pokretanje pomoću Dockera

```bash
docker compose up -d --build
```

Glavna aplikacija: `http://localhost:5000`

REST health:

```bash
curl http://localhost:5001/api/health
```

## Početno stanje

```bash
docker compose exec parking python seed.py
```

`seed.py` resetira razvojnu bazu i kreira početne korisnike, parkinge u Zagrebu, Zadru i Splitu te jednu rezervaciju. Vozila, privatne pristupne upute i promo kodovi mogu se zatim dodati kroz normalno korisničko sučelje.

## Ažuriranje nakon promjena

```bash
git pull --ff-only origin main
docker compose up -d --build
```

## Brza REST provjera

```bash
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano:

- `5001 /api/health` → `200`
- `5001 /api/parkings` bez tokena → `401`
- `5000 /api/parkings` → `404`
