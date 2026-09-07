# ParKING — završni audit kriterija

Ovaj dokument je interna kontrolna lista trenutnog stanja projekta.

## Procijenjeni rezultat

Konzervativna procjena: **70 bodova**.

| Rb. | Kriterij | Bodovi | Procjena | Dokaz / napomena |
|---:|---|---:|---|---|
| 1 | Korisničke klase | 3 | sigurno | `User`, `ParkingSpot`, `Reservation`. |
| 2 | Dijalozi / forme | 4 | sigurno | Više od tri forme; termin s pretrage prenosi se kroz detalje u rezervaciju. |
| 3 | HR / EN | 4 | sigurno | Dva jezika, više od pet prevedenih stranica. |
| 4 | INI / Registry | 2 | sigurno | `config.ini`: `default_language`, `items_per_page`. |
| 5 | XML / JSON CRUD | 4 | sigurno | JSON CRUD bilješki u `data/parking_notes.json`. |
| 6 | Vlastiti binarni format | 3 | sigurno | Stvarne pretrage u `data/search_history.bin`, `PKSR` v2, čitanje/migracija v1. |
| 7 | Baza i CRUD | 6 | sigurno | SQLite + SQLAlchemy, CRUD nad tri tablice. |
| 8 | Sort / filter / calculated / lookup | 5 | sigurno | Lokacija, maksimalna cijena, vremenska dostupnost, sortiranje, ukupna cijena i ORM relacije. |
| 9 | BLOB | 3 | sigurno | Fotografija parkinga u BLOB polju. |
| 10 | PDF / master-detail | 5 | sigurno | PDF potvrda rezervacije iz tri povezane tablice. |
| 11 | Dretve / thread pool | 5 | sigurno | `ThreadPoolExecutor(max_workers=3)` + tri Open-Meteo poziva. |
| 12 | Sigurno UI ažuriranje iz dretve | 0 | ne računamo | Web izvedba ne pokriva desktop kriterij dovoljno jasno. |
| 13 | Sinkronizacija | 2 | sigurno | `threading.Lock` štiti zajednički zapisnik. |
| 14 | Proces A → B | 4 | sigurno | **Admin rezervacije → Provjeri rezervacije** pokreće `reservation_worker.py` preko `subprocess.run`. |
| 15 | TCP | 0 | nije implementirano | — |
| 16 | UDP | 0 | nije implementirano | — |
| 17 | HTTP downloader | 0 | nije implementirano | — |
| 18 | Udaljeni SOAP | 0 | nije implementirano | — |
| 19 | Vlastiti SOAP | 0 | nije implementirano | — |
| 20 | Udaljeni REST | 3 | sigurno | Open-Meteo. |
| 21 | Vlastiti REST servis + klijent | 4 | vrlo vjerojatno | Web app 5000, zasebni REST app/proces 5001, dva resursa. |
| 22 | REST auth/authz | 4 | vjerojatno | Bearer token, 401 bez tokena, 403 za nedopuštene akcije. |
| 23 | AES-GCM | 2 | sigurno | **Bilješke** imaju stvarnu šifriranu sigurnosnu kopiju u `PKAE` datoteci. |
| 24 | Asimetrična kriptografija | 0 | nije implementirano | — |
| 25 | SHA-256 + sol + papar | 7 | vrlo vjerojatno | Integritet stvarne rezervacije, promjenjiva sol, papar 0–255, provjera svih 256 vrijednosti. |
| 26 | Digitalni potpis | 0 | nije implementirano | — |
| 27–30 | Biblioteke / DLL | 0 | nije implementirano | — |

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 4 + 3 + 4 + 4 + 2 + 7 = 70
```

## Integracije koje više nisu samo testne stranice

### Vlastiti binarni format

Klik na **Pretraži** kod valjane pretrage prijavljenog korisnika automatski sprema stvarne kriterije u `data/search_history.bin`. **Povijest pretraga** ih ponovno čita i omogućuje akciju **Ponovi**.

Provjera:

```bash
xxd data/search_history.bin | head
```

### AES-GCM

AES nije više pod **Test**. Nalazi se na stranici **Bilješke** kao sigurnosna kopija stvarnih JSON bilješki.

Korisnik može izraditi i otvoriti šifriranu kopiju. Datoteka je:

```text
exports/notes_user_<id>.aes
```

Provjera:

```bash
xxd exports/notes_user_<id>.aes | head
```

Na početku se vidi `PKAE`.

### Proces A → B

Zasebna stranica **Procesi** više se ne koristi. Na **Admin rezervacije** postoji gumb **Provjeri rezervacije**.

`run.py` pokreće `reservation_worker.py` kao zasebni proces i čita:

```text
returncode
stdout
stderr
```

Kodovi su:

```text
0 = sve ispravno
1 = problem u rezervacijama
2 = tehnička greška
```

### SHA-256

SHA-256 ostaje integriran u **Moje rezervacije** kao provjera integriteta stvarnih podataka rezervacije.

## Dostupnost parkinga

Parking se isključuje iz rezultata samo ako postoji `ACTIVE` rezervacija koja zadovoljava:

```text
Reservation.start_time < traženi_završetak
AND
Reservation.end_time > traženi_početak
```

`CANCELLED` rezervacije ne blokiraju dostupnost. Maksimalna cijena je dodatni filter.

## 24-satni unos

Flatpickr s `time_24hr: true` koristi se na:

- pretrazi parkinga
- korisničkoj rezervaciji
- administratorskom uređivanju rezervacije

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

Za kriterij 22 treba pokazati i stvarni `403`, ne samo `401`.

## Demo stanje

```bash
docker compose exec parking python seed.py
```

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

## Zaključak

Projekt ostaje na konzervativno procijenjenih **70 bodova**, ali su kriteriji 6, 14, 23 i 25 sada bolje povezani sa stvarnim funkcionalnostima ParKING aplikacije umjesto s izdvojenim demonstracijskim ekranima.
