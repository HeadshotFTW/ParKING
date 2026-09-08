# ParKING — implementirane funkcionalnosti

Ovaj dokument navodi funkcionalnosti koje su implementirane i trenutačno se računaju u procjeni projekta.

**Konzervativna procjena: 71 bod.** Kriterij 11 je praktično testiran s jednom i tri dretve; na zadnjem mjerenju jedna dretva trajala je 0.516 s, tri dretve 0.168 s, odnosno ubrzanje je bilo 3.07×.

## 1. Korisničke klase — 3 boda

Implementirane su klase `User`, `ParkingSpot` i `Reservation` kao SQLAlchemy modeli s atributima i metodama koje se koriste kroz poslovnu logiku aplikacije.

## 2. Forme i komunikacija među formama — 4 boda

Aplikacija sadrži više od tri forme/dijaloga: prijava, registracija, pretraga parkinga, dodavanje/uređivanje parkinga, detalji parkinga, rezervacija, moje rezervacije, bilješke te administratorske forme. Termin odabran na pretrazi prenosi se kroz **Detalji → Rezerviraj**.

## 3. Višejezično sučelje — 4 boda

Podržani su hrvatski i engleski jezik. Jezik se može mijenjati tijekom rada aplikacije preko HR/EN poveznica.

## 4. INI postavke — 2 boda

Postavke se čitaju i zapisuju u `config.ini` pomoću `configparser`. Koriste se `default_language` i `items_per_page`.

## 5. JSON spremanje i CRUD — 4 boda

Korisničke bilješke spremaju se u `data/parking_notes.json`. Podržani su čitanje, dodavanje, uređivanje i brisanje zapisa.

## 6. Prilagođeni binarni format — 3 boda

Stvarne pretrage parkinga automatski se spremaju u `data/search_history.bin`. Format koristi vlastito zaglavlje `PKSR`, verziju i broj zapisa. Stranica **Povijest pretraga** prikazuje zapise korisnika i omogućuje ponavljanje spremljene pretrage.

## 7. Baza podataka i CRUD — 6 bodova

Aplikacija koristi SQLite preko SQLAlchemy ORM-a. CRUD se demonstrira nad tablicama `users`, `parking_spots` i `reservations`.

## 8. Sortiranje, filtriranje, izračunato i lookup polje — 5 bodova

Parkinzi se filtriraju po lokaciji, maksimalnoj cijeni i vremenskoj dostupnosti te sortiraju po cijeni i nazivu. Izračunato polje je ukupna cijena rezervacije preko `Reservation.total_price()`. Lookup podaci dohvaćaju se ORM relacijama poput `Reservation.parking` i `ParkingSpot.owner`.

## 9. BLOB polje u bazi — 3 boda

Fotografija parkinga sprema se izravno u SQLite BLOB polje `photo`, uz MIME tip `photo_mime`. Slika se može učitati, prikazati, zamijeniti i ukloniti.

## 10. PDF izvještaj — 5 bodova

ReportLab generira PDF potvrdu rezervacije s podacima iz tablica `reservations`, `users` i `parking_spots`.

## 11. Paralelno izvršavanje dretvama — 5 bodova

Open-Meteo dohvat koristi se u glavnom toku aplikacije. Ako je prikazano više različitih gradova, vremenski podaci dohvaćaju se paralelno pomoću `ThreadPoolExecutor`.

Administratorska stranica **Test → Dretve** uspoređuje isti skup Open-Meteo forecast zahtjeva kroz isti `ThreadPoolExecutor` u dvije varijante:

```text
max_workers = 1
max_workers = 3
```

Koordinate se razriješe prije mjerenja, pa oba mjerenja obuhvaćaju isti posao. `seed.py` daje Zagreb, Zadar i Split kao tri neovisna mrežna zadatka. Zadnji praktični test dao je:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

Time se demonstrira zahtjev nastavnika da višedretveni pristup bude brži od izvođenja istih operacija jednom dretvom.

## 13. Sinkronizacija dretvi — 2 boda

`fetch_weather()` nakon svakog Open-Meteo poziva zapisuje rezultat u zajednički `_request_log`. Taj zapis je kritična sekcija i zaštićen je pomoću `threading.Lock`.

## 14. Komunikacija između procesa — 0 bodova / uklonjeno

Nastavnik je pojasnio da se za ovaj kriterij očekuju procesi A i B kao izvršne EXE aplikacije. Ranija Python `subprocess` demonstracija zato je uklonjena iz projekta zajedno s `reservation_worker.py`, rutama i gumbom za provjeru rezervacija.

## 20. Udaljeni REST servis — 3 boda

Aplikacija koristi Open-Meteo Geocoding API i Forecast API. Podaci se prikazuju uz stvarne parkinge na **Dostupni parkinzi** i **Detalji parkinga**.

## 21. Vlastiti REST servis i klijent — 4 boda

Glavna Flask aplikacija `run.py` radi na portu `5000`, a zasebna Flask aplikacija `api_app.py` kao zaseban proces na portu `5001`. Glavna aplikacija kao REST klijent preko HTTP-a koristi vlastiti API.

## 22. REST autentifikacija i autorizacija — 4 boda

REST API koristi Bearer token. Nedostajući ili pogrešan token vraća `401`, a nedopuštene akcije vraćaju `403`.

## 23. Simetrično šifriranje AES-GCM — 2 boda

AES-GCM je integriran u **Bilješke** kao sigurnosna kopija stvarnih korisničkih JSON podataka.

## 25. SHA-256, promjenjiva sol i papar — 7 bodova

Kriterij je razdvojen na dvije različite namjene kako se sol i papar ne bi pogrešno koristili za provjeru integriteta.

### Integritet rezervacije

`hash_demo.py` radi obični SHA-256 nad stabilnim tekstualnim prikazom stvarnih podataka rezervacije. Za ovu provjeru **ne koriste se sol ni papar**. Korisnik može usporediti trenutačni sažetak s ranije spremljenim sažetkom; promjena relevantnih podataka rezervacije mijenja SHA-256 otisak.

### Sigurnosni kod za šifriranu kopiju bilješki

Na stranici **Bilješke** korisnik postavlja sigurnosni kod prije izrade ili otvaranja AES-GCM kopije. Kod se ne sprema u izvornom obliku. `security_code_store.py` sprema samo njegov SHA-256 sažetak u `data/security_codes.json`.

Promjenjiva sol izvodi se deterministički iz korisničkog ID-a:

```text
SHA256("ParKING-security-code-salt:<user_id>")[0:16]
```

Sol se ne sprema u bazu ni datoteku. Pri stvaranju sažetka koristi se jedan papar iz raspona `0–255`. Papar se također ne sprema uz sažetak. Kod provjere `verify_security_code()` namjerno prolazi **svih 256 mogućih vrijednosti papra**, računa kandidat za svaku vrijednost i uspoređuje ga sa spremljenim sažetkom pomoću `hmac.compare_digest`.

Ako je kod ispravan, aplikacija tek tada otvara AES-GCM sigurnosnu kopiju. Stranica prikazuje da je provjereno svih 256 mogućih vrijednosti papra. Promjena već postavljenog koda zahtijeva provjeru trenutačnog koda.

## 28. Dinamička biblioteka — 5 bodova

Aplikacija koristi vlastitu C++ dinamičku biblioteku za izračun naknade platforme. Izvorni kod je u `native/service_fee.cpp`, a Docker build ga prevodi u Linux shared object `native/libservice_fee.so` pomoću `g++ -shared -fPIC`.

Biblioteka sadrži klasu `ServiceFeeCalculator` s dvije metode:

```text
calculateFee(...)        → service fee jedne rezervacije
calculateTotalFees(...)  → zbroj service feeova više rezervacija
```

Python modul `service_fee.py` učitava `.so` tijekom rada aplikacije pomoću `ctypes`. Na stranici **Admin rezervacije** za svaku `ACTIVE` rezervaciju prikazuje se pojedinačni service fee, dok se iznad tablice prikazuje ukupan service fee svih aktivnih rezervacija.

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 3 + 4 + 4 + 2 + 7 + 5 = 71
```

Ne računaju se kriteriji 12, 14–19, 24, 26, 27, 29 i 30.
