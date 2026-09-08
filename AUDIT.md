# ParKING — završni audit kriterija

Ovaj dokument je interna kontrolna lista trenutnog stanja projekta.

## Procijenjeni rezultat

Konzervativna procjena: **71 bod**.

| Rb. | Kriterij | Bodovi | Procjena | Dokaz / napomena |
|---:|---|---:|---|---|
| 1 | Korisničke klase | 3 | sigurno | `User`, `ParkingSpot`, `Reservation`, dodatno `PromoCode`. |
| 2 | Dijalozi / forme | 4 | sigurno | Više od tri forme; termin se prenosi iz pretrage u rezervaciju. |
| 3 | HR / EN | 4 | sigurno | Dva jezika i promjena jezika tijekom rada. |
| 4 | INI / Registry | 2 | sigurno | `config.ini`: `default_language`, `items_per_page`. |
| 5 | XML / JSON CRUD | 4 | sigurno | **Moja vozila** koristi `data/vehicles.json` i puni CRUD kroz `vehicle_store.py`. |
| 6 | Vlastiti binarni format | 3 | sigurno | Stvarne pretrage u `data/search_history.bin`, `PKSR` v2. |
| 7 | Baza i CRUD | 6 | sigurno | SQLite + SQLAlchemy, CRUD nad tri glavne tablice; dodatno `promo_codes`. |
| 8 | Sort / filter / calculated / lookup | 5 | sigurno | Lokacija, cijena, dostupnost, sortiranje, `total_price()` i ORM relacije. |
| 9 | BLOB | 3 | sigurno | Fotografija parkinga u BLOB polju. |
| 10 | PDF / master-detail | 5 | sigurno | PDF potvrda rezervacije iz povezanih tablica. |
| 11 | Dretve / thread pool | 5 | praktično potvrđeno | `ThreadPoolExecutor(max_workers=1)` vs `max_workers=3`; zadnje mjerenje 0.516 s vs 0.168 s, ubrzanje 3.07×. |
| 12 | Sigurno UI ažuriranje iz dretve | 0 | ne računamo | Web izvedba ne pokriva kriterij dovoljno jasno. |
| 13 | Sinkronizacija | 2 | sigurno | `threading.Lock` štiti zajednički `_request_log`. |
| 14 | Proces A → B | 0 | uklonjeno | Nastavnik očekuje A i B kao izvršne EXE aplikacije. |
| 15 | TCP | 0 | nije implementirano | — |
| 16 | UDP | 0 | nije implementirano | — |
| 17 | HTTP downloader | 0 | nije implementirano | — |
| 18 | Udaljeni SOAP | 0 | nije implementirano | — |
| 19 | Vlastiti SOAP | 0 | nije implementirano | — |
| 20 | Udaljeni REST | 3 | sigurno | Open-Meteo Geocoding + Forecast API. |
| 21 | Vlastiti REST servis + klijent | 4 | vrlo vjerojatno | Web app 5000, zasebni REST app 5001, dva resursa. |
| 22 | REST auth/authz | 4 | vjerojatno | Bearer token, `401`, `403`. |
| 23 | AES-GCM | 2 | sigurno | Privatne pristupne upute parkinga šifriraju se u `parking_spots.access_instructions` i dešifriraju samo za `ACTIVE` rezervacije korisnika. |
| 24 | Asimetrična kriptografija | 0 | nije implementirano | — |
| 25 | SHA-256 + promjenjiva sol + papar | 7 | vrlo vjerojatno | Integritet rezervacije koristi obični SHA-256 bez soli/papra. `POPUST` koristi sol po `user_id`, sistemski papar i puni scan 0–255. |
| 26 | Digitalni potpis | 0 | nije implementirano | — |
| 27 | Statička biblioteka | 0 | namjerno ne implementiramo | — |
| 28 | Dinamička biblioteka | 5 | sigurno nakon Docker builda | `ServiceFeeCalculator`, `.so`, `ctypes`, stvarni service fee prikaz. |
| 29 | DLL dijalozi | 0 | nije implementirano | — |
| 30 | Resurs u dinamičkoj biblioteci | 0 | nije implementirano | — |

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 3 + 4 + 4 + 2 + 7 + 5 = 71
```

## Kriterij 5 — JSON CRUD vozila

`vehicle_store.py` sprema vozila prijavljenih korisnika u `data/vehicles.json`. Podržani su create, read, update i delete. Podaci nisu duplicirani u SQL bazi. Pri rezervaciji korisnik može odabrati jedno od vlastitih vozila, a rezervacija čuva snapshot vozila.

## Kriterij 11 — praktična potvrda

Isti Open-Meteo forecast zahtjevi izvršavaju se kroz isti `ThreadPoolExecutor` jednom s jednom i jednom s tri dretve. Koordinate se razriješe prije mjerenja.

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

Na obrani ponovno pokazati da je višedretvena varijanta brža preko **Tools → Test Dretve**.

## Kriterij 14 — uklonjen

`reservation_worker.py`, `subprocess` provjera, povezane rute i UI uklonjeni su iz projekta.

## Kriterij 23 — AES-GCM pristupne upute

`ParkingSpot` ima `access_instructions` kao BLOB. `parking_access_crypto.py` koristi AES-GCM i novi nonce pri svakom spremanju. Javni parking ne otkriva te podatke. Server ih dešifrira na **Moje rezervacije** samo kada je rezervacija prijavljenog korisnika `ACTIVE`.

## Kriterij 25 — SHA-256, sol i papar

### Integritet rezervacije

`hash_demo.py` računa SHA-256 nad stabilnim prikazom podataka rezervacije. Sol i papar se ovdje namjerno ne koriste, jer je cilj provjera integriteta.

### Promo kod POPUST po korisniku

`promo_code_hash.py` i `promo_web.py` implementiraju zasebnu poslovnu primjenu soli i papra:

- jedini promo kod je `POPUST`
- svaki korisnik dobiva vlastitu reproducibilnu sol izvedenu pravilom `SHA256("ParKING-user-promo-salt:<user_id>")[0:16]`
- sol se ne sprema u bazu ni datoteku
- papar je definiran na razini sustava preko `PROMO_SYSTEM_PEPPER`
- papar se ne sprema uz korisnički hash
- administrator vidi checkbox listu svih korisnika i svakome može zadati drugi postotak popusta
- za svakog označenog korisnika računa se zaseban SHA-256 hash iz njegove soli + `POPUST` + sistemskog papra
- isti kod zato daje različit hash za različite korisnike
- kod provjere za prijavljenog korisnika prolazi se svih 256 vrijednosti papra od 0 do 255
- tek nakon cijelog raspona prihvaća se podudaranje koje odgovara sistemskom papru
- rezervacija sprema `promo_code_id` i korisnikov `discount_percent`, a `total_price()` vraća konačnu cijenu

## Dinamička C++ biblioteka

`native/service_fee.cpp` sadrži `ServiceFeeCalculator` s metodama `calculateFee()` i `calculateTotalFees()`. `service_fee.py` učitava `.so` pomoću `ctypes`.

Provjera:

```bash
docker compose exec parking python -c "import service_fee; print(service_fee.native_library_loaded(), service_fee.LIBRARY_PATH)"
```

## REST — provjera prije obrane

```bash
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano: `200`, `401`, `404`; za kriterij 22 pokazati i stvarni `403`. UI demonstracija je pod **Tools → Test REST**.

## Zaključak

Projekt je konzervativno procijenjen na **71 bod**. Kriterij 25 koristi promjenjivu korisničku sol i sistemski papar na poslovno smislenom promo kodu `POPUST`, dok provjera integriteta rezervacije ostaje čisti SHA-256 bez soli i papra.
