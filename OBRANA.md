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

## 3. JSON CRUD + AES-GCM

Na stranici **Bilješke** pokazati dodavanje, uređivanje i brisanje JSON bilješke, zatim izradu i otvaranje AES-GCM šifrirane sigurnosne kopije.

Dokaz datoteke:

```bash
xxd exports/notes_user_<id>.aes | head
```

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

Ovo je važan dio zbog komentara nastavnika za kriterij 11.

Kao administrator otvoriti **Test → Dretve**. `run.py` čita lokacije stvarnih parkinga iz baze, a `parallel_tasks.py` izdvaja jedinstvene gradove. Nakon seeda trebali bi se pojaviti Zagreb, Zadar i Split.

U kodu objasniti da se koordinate prvo razriješe **prije mjerenja**, kako geokodiranje ne bi dalo prednost jednom prolazu. Zatim se potpuno isti Open-Meteo forecast zahtjevi izvršavaju kroz isti `ThreadPoolExecutor`:

```text
1. max_workers = 1
2. max_workers = 3
```

Na stranici pokazati:

- vrijeme **1 dretva**
- vrijeme **3 dretve**
- faktor ubrzanja
- da je vrijeme s tri dretve manje od vremena s jednom dretvom
- nazive radnih dretvi u rezultatima

Prema komentaru nastavnika, kriterij 11 računamo samo ako se na obrani stvarno vidi da je višedretvena varijanta brža.

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

## 9. SHA-256

Trenutačna SHA-256 funkcionalnost postoji, ali dio sa soli i paprom nije konačan. Nastavnik je pojasnio da se za provjeru integriteta ne koriste sol ni papar. Prije obrane ovaj dio treba proći zaseban redizajn; do tada ne učiti trenutačno rješenje kao konačan odgovor za kriterij 25.

## Kriterij 14 — ne demonstrirati

Ranija Python procesna demonstracija je uklonjena. Nastavnik očekuje procese A i B kao izvršne EXE aplikacije, pa kriterij 14 trenutačno ne prijavljujemo i ne pokazujemo.

## Datoteke koje je korisno znati

```text
models.py                    SQLAlchemy modeli
app.py                       osnovni CRUD i web rute
run.py                       REST klijent, AES backup, SHA-256 ruta, thread test, service fee Jinja funkcije
parking_availability.py      dostupnost + binarna povijest + vrijeme uz parkinge
binary_store.py              PKSR binarni format
crypto_store.py              AES-GCM
hash_demo.py                 SHA-256 dio koji treba redizajn soli/papra
parallel_tasks.py            Open-Meteo + ThreadPoolExecutor + Lock
service_fee.py               ctypes wrapper za dinamičku biblioteku
native/service_fee.cpp       C++ ServiceFeeCalculator
api_app.py                   vlastiti REST servis na 5001
json_store.py                JSON CRUD
config.ini                   INI postavke
```

## Bodovna procjena

Trenutačna konzervativna procjena je oko **66 bodova**, uz uvjet da kriterij 11 na obrani stvarno pokaže ubrzanje. Kriterij 25 ponovno procijeniti nakon redizajna soli i papra.
