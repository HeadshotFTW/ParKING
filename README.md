# ParKING

ParKING je Flask web aplikacija za oglašavanje i rezervaciju privatnih parkirnih mjesta. Glavne funkcionalnosti povezane su u jedan stvarni korisnički tok: korisnik traži parking za određeni termin, provjerava dostupnost, vidi trenutačne vremenske podatke za lokaciju, rezervira parking, prati rezervacije i koristi dodatne funkcije poput PDF potvrde, SHA-256 provjere, povijesti pretraga i šifriranih sigurnosnih kopija bilješki.

## Glavne funkcionalnosti

- registracija, prijava i odjava korisnika
- CRUD nad parkirnim mjestima
- rezervacije s provjerom preklapanja termina
- pretraga dostupnih parkinga po lokaciji, vremenu i maksimalnoj cijeni
- sortiranje po cijeni i nazivu
- 24-satni unos datuma i vremena pomoću Flatpickra
- SQLite + SQLAlchemy
- administratorski CRUD nad korisnicima i rezervacijama
- HR/EN sučelje
- INI postavke u `config.ini`
- JSON CRUD korisničkih bilješki
- BLOB fotografije parkinga u bazi
- PDF potvrda rezervacije
- stvarna binarna povijest pretraga u vlastitom `PKSR` formatu
- AES-GCM sigurnosna kopija bilješki integrirana u stranicu **Bilješke**
- SHA-256 funkcionalnost nad podacima rezervacije
- Open-Meteo vremenski podaci prikazani uz stvarne parkinge
- ThreadPoolExecutor + `threading.Lock` za paralelni dohvat vremenskih podataka
- vlastiti REST API s Bearer autentifikacijom i autorizacijom
- vlastita C++ dinamička biblioteka (`.so`) za izračun service fee naknade

## Dostupnost parkinga prema terminu

Na stranici **Dostupni parkinzi** korisnik zadaje lokaciju, početak i završetak termina, opcionalnu maksimalnu cijenu po satu i sortiranje.

Parking se prikazuje ako nema `ACTIVE` rezervaciju koja se preklapa s traženim intervalom. Koristi se pravilo:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

`CANCELLED` rezervacije ne blokiraju dostupnost. Odabrani termin prenosi se kroz **Detalji → Rezerviraj**, pa ga korisnik ne mora ponovno unositi.

## Vremenski podaci uz parkinge

Na karticama pod **Dostupni parkinzi** i na stranici **Detalji parkinga** prikazuju se trenutačna temperatura i brzina vjetra za grad parkinga.

Grad se automatski izdvaja iz tekstualne lokacije parkinga i, ako nije jedna od unaprijed poznatih lokacija, pretvara u koordinate preko Open-Meteo Geocoding API-ja. Geokodiranje je ograničeno na Hrvatsku (`countryCode=HR`).

Ako je na istoj stranici prikazano više različitih gradova, `parking_availability.py` poziva `fetch_weather_for_parking_locations()` iz `parallel_tasks.py`, a vremenski zahtjevi izvršavaju se paralelno kroz `ThreadPoolExecutor`. Više parkinga u istom gradu dijeli isti dohvaćeni rezultat.

`fetch_weather()` nakon završetka zahtjeva zapisuje podatke u zajednički `_request_log`. Taj zajednički resurs zaštićen je s `threading.Lock`, pa više dretvi ne mijenja zapisnik istodobno.

### Test → Dretve

Administratorska stranica **Test → Dretve** koristi gradove iz stvarnih lokacija parkinga u bazi. Za poštenu usporedbu koordinate se razriješe prije mjerenja, a zatim se isti Open-Meteo forecast zahtjevi izvršavaju dvaput kroz isti `ThreadPoolExecutor`:

```text
max_workers = 1
max_workers = 3   (ili manje ako nema tri grada)
```

Stranica prikazuje vrijeme za **1 dretvu**, vrijeme za **više dretvi** i faktor ubrzanja. Početno stanje sadrži parkinge u Zagrebu, Zadru i Splitu kako bi se mogla demonstrirati usporedba jedne i tri radne dretve.

## Povijest pretraga i vlastiti binarni format

Svaka valjana pretraga prijavljenog korisnika automatski se sprema u `data/search_history.bin`. Stranica **Povijest pretraga** prikazuje prethodne pretrage korisnika i omogućuje akciju **Ponovi**.

Aktualni binarni format je `PKSR` verzija 2. Sprema `user_id`, Unix vrijeme, opcionalnu maksimalnu cijenu te UTF-8 polja promjenjive duljine za lokaciju, početak, završetak i sortiranje.

## Bilješke i AES-GCM sigurnosna kopija

Korisničke bilješke spremaju se kao JSON u `data/parking_notes.json`. Na istoj stranici **Bilješke** mogu se izraditi i otvoriti AES-GCM šifrirane sigurnosne kopije u `exports/notes_user_<id>.aes`.

## SHA-256

Na stranici **Moje rezervacije** postoji SHA-256 funkcionalnost nad stvarnim podacima rezervacije. Dio vezan uz sol i papar trenutačno je predviđen za redizajn prema povratnoj informaciji nastavnika; ne treba ga smatrati konačnim rješenjem za provjeru integriteta.

## Dinamička biblioteka za service fee

`native/service_fee.cpp` sadrži C++ klasu `ServiceFeeCalculator`. Biblioteka ima dvije računske funkcionalnosti: izračun service fee naknade jedne rezervacije i zbroj service fee naknada više rezervacija.

Docker build iz izvornog koda stvara Linux dinamičku biblioteku:

```text
native/libservice_fee.so
```

Python modul `service_fee.py` učitava biblioteku pomoću `ctypes`. Naknada je 5% ukupne cijene rezervacije. Na stranici **Admin rezervacije** svaka `ACTIVE` rezervacija prikazuje svoj service fee, a iznad tablice prikazuje se zbroj service feeova svih aktivnih rezervacija. `CANCELLED` rezervacije ne ulaze u ukupan iznos naknade.

## Vlastiti REST servis

Glavna web aplikacija radi na portu `5000`, a vlastiti REST servis kao zasebna Flask aplikacija/proces na portu `5001`.

```text
run.py      → web aplikacija → 5000
api_app.py  → REST API       → 5001
```

API izlaže resurse `/api/parkings` i `/api/reservations` te koristi Bearer token autentifikaciju i autorizaciju po korisniku i ulozi.

## Struktura projekta

```text
ParKING/
├── app.py
├── run.py
├── api_app.py
├── start.sh
├── parking_availability.py
├── binary_store.py
├── crypto_store.py
├── hash_demo.py
├── parallel_tasks.py
├── service_fee.py
├── native/
│   └── service_fee.cpp
├── models.py
├── json_store.py
├── translations.py
├── config.ini
├── seed.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README_IMPLEMENTIRANO.md
├── INSTALL_UBUNTU.md
├── INSTALL_WINDOWS.md
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

Korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

`seed.py` briše postojeću razvojnu bazu i ponovno kreira početne korisnike, četiri parkinga i jednu rezervaciju. Početni parkingi nalaze se u Zagrebu, Zadru i Splitu.

## Ažuriranje nakon promjena

```bash
git pull --ff-only origin main
docker compose up -d --build
```

## Brza provjera odvojenog REST servisa

```bash
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano:

- health na `5001` vraća `200`
- `/api/parkings` na `5001` bez tokena vraća `401`
- `/api/parkings` na `5000` vraća `404`

API token ne zapisivati u dokumentaciju niti spremati u Git.
