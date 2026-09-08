# ParKING — završni audit kriterija

Ovaj dokument je interna kontrolna lista trenutnog stanja projekta.

## Procijenjeni rezultat

Konzervativna procjena: **66 bodova**, uz uvjet da se za kriterij 11 na obrani stvarno pokaže ubrzanje višedretvenog pristupa u odnosu na jednu dretvu.

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
| 11 | Dretve / thread pool | 5 | uvjetno | **Test → Dretve** uspoređuje isti posao kroz `ThreadPoolExecutor(max_workers=1)` i `ThreadPoolExecutor(max_workers=3)`. Koordinate se razrješavaju prije mjerenja. Na obrani se mora pokazati da je višedretvena varijanta brža. |
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
| 25 | SHA-256 | 2 | privremeno | SHA-256 se koristi, ali dodatne bodove za sol i papar trenutačno ne računamo. Nastavnik je pojasnio da se kod provjere integriteta ne koriste sol ni papar. Potreban je redizajn prije konačne procjene. |
| 26 | Digitalni potpis | 0 | nije implementirano | — |
| 27 | Statička biblioteka | 0 | nije implementirano | — |
| 28 | Dinamička biblioteka | 5 | sigurno nakon Docker builda | `native/service_fee.cpp` sadrži C++ klasu `ServiceFeeCalculator` i dvije računske funkcionalnosti; Docker stvara `libservice_fee.so`, a `service_fee.py` je učitava preko `ctypes`. |
| 29 | DLL dijalozi | 0 | nije implementirano | — |
| 30 | Resurs u dinamičkoj biblioteci | 0 | nije implementirano | — |

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 3 + 4 + 4 + 2 + 2 + 5 = 66
```

## Kriterij 11 — provjera koju obavezno napraviti prije obrane

`parallel_tasks.py` sada radi pošteniju usporedbu:

1. iz stvarnih parkinga izdvoji jedinstvene gradove
2. prije mjerenja razriješi koordinate svih gradova
3. iste forecast HTTP zahtjeve izvrši s `max_workers=1`
4. iste forecast HTTP zahtjeve izvrši s `max_workers=3`
5. prikaže oba vremena i omjer `one_thread_time / multi_thread_time`

Time geokodiranje nije dio jednog mjerenja, a iz drugog izostavljeno zbog cachea. Seed sadrži Zagreb, Zadar i Split, pa druga varijanta može koristiti tri radne dretve.

Na obranu ne ići dok praktični test više puta ne pokaže da je vrijeme s tri dretve manje od vremena s jednom dretvom.

## Kriterij 14 — uklonjen

Iz projekta su uklonjeni:

```text
reservation_worker.py
run_reservation_check()
/admin/reservations/check
/admin/process
UI gumb "Provjeri rezervacije"
prikaz returncode/stdout/stderr na Admin rezervacije
```

Administratorska stranica sada ponovno služi samo stvarnom CRUD-u rezervacija i prikazu service fee naknada.

## SHA-256 / kriterij 25

Trenutačna implementacija još sadrži raniji pristup sa soli i paprom. Taj dio ne smije se braniti kao konačno rješenje za provjeru integriteta. Redizajn će se napraviti zasebno prema komentaru nastavnika.

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

Projekt je trenutačno konzervativno procijenjen na **66 bodova**. Kriterij 14 je namjerno uklonjen umjesto da se brani implementacija koja ne odgovara nastavnikovoj interpretaciji. Kriterij 25 čeka redizajn, a kriterij 11 mora prije obrane biti praktično potvrđen mjerenjem.
