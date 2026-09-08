# ParKING — plan obrane

Cilj je pokazati samo funkcionalnosti koje možemo jasno objasniti i demonstrirati.

## Priprema

```bash
git pull --ff-only origin main
docker compose up -d --build
docker compose ps
docker compose exec parking python seed.py
```

Korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

`seed.py` briše postojeću razvojnu bazu. Početno stanje sadrži parkinge u Zagrebu, Zadru i Splitu.

## 1. Dostupni parkinzi, vrijeme, rezervacija i povijest pretraga

Prijava kao `gost`.

1. Otvoriti **Dostupni parkinzi**.
2. Zadati lokaciju, termin i po želji maksimalnu cijenu.
3. Pokazati 24-satni unos vremena.
4. Pokrenuti pretragu.
5. Objasniti provjeru preklapanja `ACTIVE` rezervacija.
6. Pokazati Open-Meteo temperaturu i vjetar uz parkinge.
7. Sortirati rezultate.
8. Otvoriti **Povijest pretraga** i pokazati `data/search_history.bin`.
9. Kliknuti **Ponovi**.
10. Otvoriti parking preko **Detalji**.
11. Kliknuti **Rezerviraj** i pokazati preneseni termin.
12. Spremiti rezervaciju.
13. Otvoriti **Moje rezervacije**, pokazati trajanje i ukupnu cijenu.
14. Preuzeti PDF potvrdu.

Pravilo preklapanja:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

`CANCELLED` rezervacije ne blokiraju parking.

## 2. HR / EN

Prebaciti HR → EN i otvoriti nekoliko stranica.

## 3. JSON CRUD + AES-GCM + sigurnosni kod

Na stranici **Bilješke**:

1. pokazati dodavanje, uređivanje i brisanje JSON bilješke
2. postaviti sigurnosni kod od barem 4 znaka
3. izraditi AES-GCM šifriranu sigurnosnu kopiju
4. unijeti sigurnosni kod i otvoriti kopiju
5. pokazati poruku da je kod provjere pregledano svih 256 mogućih vrijednosti papra

Kod sigurnosnog koda objasniti:

```text
sigurnosni kod + promjenjiva sol + slučajni papar 0–255
                         ↓
                      SHA-256
                         ↓
                 sprema se samo sažetak
```

Promjenjiva sol izvodi se pravilom:

```text
SHA256("ParKING-security-code-salt:<user_id>")[0:16]
```

Sol se ne sprema. Papar se kod postavljanja slučajno bira iz raspona `0–255` i također se ne sprema. Kod provjere `verify_security_code()` prolazi svih 256 vrijednosti i traži onu koja zajedno s unesenim kodom daje spremljeni SHA-256 sažetak.

Dokaz datoteka:

```bash
cat data/security_codes.json
xxd exports/notes_user_<id>.aes | head
```

U `security_codes.json` vidi se samo SHA-256 sažetak, ne izvorni kod, sol ili papar. AES datoteka počinje s `PKAE`.

## 4. BLOB fotografija

Kao `vlasnik` otvoriti **Moji parkinzi**, urediti parking i učitati fotografiju. Pokazati prikaz, zamjenu i uklanjanje slike.

## 5. Admin CRUD + dinamička biblioteka

Prijava kao `admin`.

Na **Korisnici** pokazati CRUD. Na **Admin rezervacije** pokazati:

1. CRUD nad rezervacijama
2. stupac **Service fee (5%)** uz svaku `ACTIVE` rezervaciju
3. karticu **Ukupan service fee (5%)**
4. da pojedinačni i ukupni izračun dolaze iz vlastite C++ dinamičke biblioteke

Biblioteka:

```text
native/service_fee.cpp          C++ klasa ServiceFeeCalculator
/app/native/libservice_fee.so   rezultat Docker builda
service_fee.py                  ctypes wrapper
```

Klasa ima metode `calculateFee()` i `calculateTotalFees()`.

Provjera da je `.so` stvarno učitan:

```bash
docker compose exec parking python -c "import service_fee; print(service_fee.native_library_loaded(), service_fee.LIBRARY_PATH)"
```

Očekuje se `True` i `/app/native/libservice_fee.so`.

## 6. INI postavke

Na **Postavke** promijeniti `default_language` ili `items_per_page` i pokazati `config.ini`.

## 7. Dretve, ubrzanje, kritična sekcija i Open-Meteo

Kao administrator otvoriti **Test → Dretve**. `run.py` čita lokacije stvarnih parkinga iz baze, a `parallel_tasks.py` izdvaja jedinstvene gradove. Nakon seeda trebali bi se pojaviti Zagreb, Zadar i Split.

Koordinate se razriješe **prije mjerenja**, kako geokodiranje ne bi dalo prednost jednom prolazu. Zatim se potpuno isti Open-Meteo forecast zahtjevi izvršavaju kroz isti `ThreadPoolExecutor`:

```text
1. max_workers = 1
2. max_workers = 3
```

Na zadnjem praktičnom testu dobiveno je:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

Na obrani ponovno pokazati da je vrijeme s tri dretve manje od vremena s jednom dretvom. Zbog mrežne latencije konkretne brojke mogu varirati.

Kritična sekcija:

```python
with _request_log_lock:
    _request_log.append(...)
```

`threading.Lock` štiti zajednički `_request_log`.

## 8. Test → REST

Pokazati da web aplikacija na portu `5000` preko HTTP-a poziva zasebni vlastiti REST servis na `5001`.

```bash
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

Za autorizaciju pokazati stvarni `403` na nedopuštenoj akciji.

## 9. SHA-256 integritet rezervacije

Kao `gost` otvoriti **Moje rezervacije → SHA-256**.

Ovdje se namjerno koristi **obični SHA-256 bez soli i papra**. Objasniti da je cilj provjera integriteta: isti podaci daju isti kontrolni otisak, a promjena podataka rezervacije mijenja otisak.

Pokazati:

1. trenutačni SHA-256 otisak rezervacije
2. uspješnu provjeru trenutačnog otiska
3. po želji promijeniti jedan znak otiska i pokazati neuspješnu provjeru

Važno: sol i papar ne braniti na ovoj stranici. Oni su zasebno implementirani kod sigurnosnog koda na **Bilješke**.

## Kriterij 14 — ne demonstrirati

Ranija Python procesna demonstracija je uklonjena. Nastavnik očekuje procese A i B kao izvršne EXE aplikacije, pa kriterij 14 ne prijavljujemo i ne pokazujemo.

## Datoteke koje je korisno znati

```text
models.py                    SQLAlchemy modeli
app.py                       osnovni CRUD i web rute
run.py                       REST klijent, AES backup, security-code ruta, SHA-256 ruta, thread test, service fee Jinja funkcije
parking_availability.py      dostupnost + binarna povijest + vrijeme uz parkinge
binary_store.py              PKSR binarni format
crypto_store.py              AES-GCM
hash_demo.py                 obični SHA-256 integritet rezervacije
security_code_store.py       promjenjiva sol + slučajni papar + provjera 0–255
parallel_tasks.py            Open-Meteo + ThreadPoolExecutor + Lock
service_fee.py               ctypes wrapper za dinamičku biblioteku
native/service_fee.cpp       C++ ServiceFeeCalculator
api_app.py                   vlastiti REST servis na 5001
json_store.py                JSON CRUD
config.ini                   INI postavke
```

## Bodovna procjena

Konzervativna procjena je oko **71 bod**. Kriterij 14 je namjerno izbačen, kriterij 11 je praktično potvrdio ubrzanje, a kriterij 25 sada jasno razdvaja integritet rezervacije od hashiranja sigurnosnog koda sa soli i paprom.
