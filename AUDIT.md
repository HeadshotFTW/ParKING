# ParKING — završni audit kriterija

Ovaj dokument je interna kontrolna lista trenutnog stanja projekta.

## Procijenjeni rezultat

Konzervativna procjena: **71 bod**.

| Rb. | Kriterij | Bodovi | Procjena | Dokaz / napomena |
|---:|---|---:|---|---|
| 1 | Korisničke klase | 3 | sigurno | `User`, `ParkingSpot`, `Reservation`. |
| 2 | Dijalozi / forme | 4 | sigurno | Više od tri forme; termin s pretrage prenosi se kroz detalje u rezervaciju. |
| 3 | HR / EN | 4 | sigurno | Dva jezika, više od pet prevedenih stranica. |
| 4 | INI / Registry | 2 | sigurno | `config.ini`: `default_language`, `items_per_page`. |
| 5 | XML / JSON CRUD | 4 | sigurno | JSON CRUD bilješki u `data/parking_notes.json`. |
| 6 | Vlastiti binarni format | 3 | sigurno | Stvarne pretrage u `data/search_history.bin`, `PKSR` v2. |
| 7 | Baza i CRUD | 6 | sigurno | SQLite + SQLAlchemy, CRUD nad tri tablice. |
| 8 | Sort / filter / calculated / lookup | 5 | sigurno | Lokacija, maksimalna cijena, vremenska dostupnost, sortiranje, ukupna cijena i ORM relacije. |
| 9 | BLOB | 3 | sigurno | Fotografija parkinga u BLOB polju. |
| 10 | PDF / master-detail | 5 | sigurno | PDF potvrda rezervacije iz tri povezane tablice. |
| 11 | Dretve / thread pool | 5 | praktično potvrđeno | **Test → Dretve** uspoređuje isti posao kroz `ThreadPoolExecutor(max_workers=1)` i `ThreadPoolExecutor(max_workers=3)`. Zadnje mjerenje: 0.516 s prema 0.168 s, ubrzanje 3.07×. |
| 12 | Sigurno UI ažuriranje iz dretve | 0 | ne računamo | Web izvedba ne pokriva desktop kriterij dovoljno jasno. |
| 13 | Sinkronizacija | 2 | sigurno | `threading.Lock` štiti kritičnu sekciju koja mijenja zajednički `_request_log`. |
| 14 | Proces A → B | 0 | uklonjeno | Nastavnik očekuje A i B kao izvršne EXE aplikacije. Ranija Python `subprocess` demonstracija i `reservation_worker.py` uklonjeni su. |
| 15 | TCP | 0 | nije implementirano | — |
| 16 | UDP | 0 | nije implementirano | — |
| 17 | HTTP downloader | 0 | nije implementirano | — |
| 18 | Udaljeni SOAP | 0 | nije implementirano | — |
| 19 | Vlastiti SOAP | 0 | nije implementirano | — |
| 20 | Udaljeni REST | 3 | sigurno | Open-Meteo Geocoding + Forecast API; podaci se prikazuju uz stvarne parkinge. |
| 21 | Vlastiti REST servis + klijent | 4 | vrlo vjerojatno | Web app 5000, zasebni REST app/proces 5001, dva resursa. |
| 22 | REST auth/authz | 4 | vjerojatno | Bearer token, 401 bez tokena, 403 za nedopuštene akcije. |
| 23 | AES-GCM | 2 | sigurno | **Bilješke** imaju stvarnu šifriranu sigurnosnu kopiju u `PKAE` datoteci. |
| 24 | Asimetrična kriptografija | 0 | nije implementirano | — |
| 25 | SHA-256 + promjenjiva sol + papar | 7 | vrlo vjerojatno | Integritet rezervacije koristi obični SHA-256 bez soli/papra. Zasebni sigurnosni kod za AES kopiju koristi promjenjivu sol izvedenu iz user_id, slučajni papar 0–255 i provjeru cijelog raspona od 256 vrijednosti. |
| 26 | Digitalni potpis | 0 | nije implementirano | — |
| 27 | Statička biblioteka | 0 | nije implementirano | — |
| 28 | Dinamička biblioteka | 5 | sigurno nakon Docker builda | `native/service_fee.cpp` sadrži C++ klasu `ServiceFeeCalculator` i dvije računske funkcionalnosti; Docker stvara `libservice_fee.so`, a `service_fee.py` je učitava preko `ctypes`. |
| 29 | DLL dijalozi | 0 | nije implementirano | — |
| 30 | Resurs u dinamičkoj biblioteci | 0 | nije implementirano | — |

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 3 + 4 + 4 + 2 + 7 + 5 = 71
```

## Kriterij 11 — praktična potvrda

`parallel_tasks.py` radi usporedbu na način da najprije razriješi koordinate, a zatim potpuno iste forecast HTTP zahtjeve izvršava kroz isti `ThreadPoolExecutor` jednom s jednom, a drugi put s tri radne dretve.

Zadnji test:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

Brojke mogu varirati zbog mrežne latencije, ali na obrani se mora ponovno pokazati da je višedretvena varijanta brža.

## Kriterij 14 — uklonjen

Iz projekta su uklonjeni `reservation_worker.py`, `subprocess` provjera, povezane rute, gumb i prikaz povratnih kodova. Administratorska stranica služi CRUD-u rezervacija i service fee prikazu.

## Kriterij 25 — konačni dizajn

### Provjera integriteta

`hash_demo.py` iz stabilnog tekstualnog prikaza rezervacije računa obični SHA-256. Sol i papar se ovdje namjerno ne koriste. Time isti sadržaj daje isti kontrolni otisak, a promjena podataka mijenja sažetak.

### Sigurnosni kod

`security_code_store.py` služi za sigurnosni kod kojim korisnik otključava prikaz AES-GCM sigurnosne kopije bilješki.

- izvorni sigurnosni kod se ne sprema
- promjenjiva sol izvodi se pravilom `SHA256("ParKING-security-code-salt:<user_id>")[0:16]`
- sol se ne sprema
- kod stvaranja sažetka slučajno se bira jedan papar iz `0–255`
- papar se ne sprema uz sažetak
- sprema se samo SHA-256 sažetak u `data/security_codes.json`
- kod provjere prolazi se svih 256 vrijednosti papra i uspoređuje kandidat pomoću `hmac.compare_digest`
- promjena sigurnosnog koda zahtijeva prethodnu provjeru trenutačnog koda

Na stranici **Bilješke** korisnik najprije postavi kod, zatim može izraditi AES-GCM kopiju, a pri otvaranju mora ponovno unijeti kod. Nakon uspješne provjere UI prikazuje da je pregledano svih 256 vrijednosti papra.

## Dinamička C++ biblioteka za service fee

`native/service_fee.cpp` sadrži klasu `ServiceFeeCalculator` s metodama `calculateFee()` i `calculateTotalFees()`. `service_fee.py` ih poziva preko `ctypes`, a Dockerfile prevodi kod u `/app/native/libservice_fee.so`.

Na stranici **Admin rezervacije** prva funkcionalnost računa 5% service fee za svaku `ACTIVE` rezervaciju, a druga ukupan service fee svih aktivnih rezervacija.

Provjera nakon builda:

```bash
docker compose exec parking python -c "import service_fee; print(service_fee.native_library_loaded(), service_fee.LIBRARY_PATH)"
```

## REST — obavezna provjera prije obrane

```bash
docker compose logs --tail=50
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano:

```text
5001 /api/health    → 200
5001 /api/parkings  → 401 bez tokena
5000 /api/parkings  → 404
```

Za kriterij 22 treba pokazati i stvarni `403`.

## Zaključak

Projekt je trenutačno konzervativno procijenjen na **71 bod**. Kriterij 14 je namjerno uklonjen, kriterij 11 je praktično potvrdio ubrzanje, a kriterij 25 sada odvaja integritet od zasebne primjene soli i papra na sigurnosni kod.
