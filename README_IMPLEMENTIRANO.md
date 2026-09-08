# ParKING — implementirane funkcionalnosti

Ovaj dokument navodi funkcionalnosti koje su implementirane i trenutačno se računaju u procjeni projekta.

**Konzervativna procjena: 71 bod.** Kriterij 11 je praktično testiran: `0.516 s` s jednom dretvom i `0.168 s` s tri dretve, odnosno `3.07×` ubrzanje.

## 1. Korisničke klase — 3 boda

Implementirane su klase `User`, `ParkingSpot`, `Reservation` i `PromoCode` kao SQLAlchemy modeli.

## 2. Forme i komunikacija među formama — 4 boda

Aplikacija ima više od tri forme. Termin odabran na pretrazi prenosi se kroz **Detalji → Rezerviraj**, a među formama postoje prijava, registracija, parking CRUD, rezervacije, vozila i administratorske forme. Pri rezervaciji korisnik može odabrati i jedno od svojih vozila iz JSON spremnika.

## 3. Višejezično sučelje — 4 boda

Podržani su hrvatski i engleski jezik, uz promjenu jezika tijekom rada aplikacije.

## 4. INI postavke — 2 boda

`config.ini` sadrži `default_language` i `items_per_page`, koje administrator može mijenjati kroz aplikaciju.

## 5. JSON spremanje i CRUD — 4 boda

Podstranica **Moja vozila** koristi `vehicle_store.py` i datoteku:

```text
data/vehicles.json
```

Za svakog korisnika podržani su prikaz, dodavanje, uređivanje i brisanje vozila. Zapis sadrži `id`, `user_id`, naziv vozila i registracijsku oznaku. Dodano vozilo može se odabrati pri rezervaciji parkinga.

## 6. Prilagođeni binarni format — 3 boda

Stvarne pretrage parkinga spremaju se u `data/search_history.bin` u vlastitom `PKSR` formatu. **Povijest pretraga** prikazuje zapise i omogućuje ponavljanje pretrage; pristup toj stranici ima administrator.

## 7. Baza podataka i CRUD — 6 bodova

SQLite + SQLAlchemy. CRUD se demonstrira nad `users`, `parking_spots` i `reservations`; korisnički promo popusti dodatno se spremaju u tablici `promo_codes`.

## 8. Sortiranje, filtriranje, izračunato i lookup polje — 5 bodova

Parkinzi se filtriraju po lokaciji, maksimalnoj cijeni i vremenskoj dostupnosti te sortiraju po cijeni i nazivu. `Reservation.total_price()` računa konačnu cijenu nakon eventualnog promo popusta, a ORM relacije poput `Reservation.parking` i `ParkingSpot.owner` služe kao lookup/povezana polja.

## 9. BLOB polje — 3 boda

Fotografija parkinga sprema se u BLOB polje `photo`, uz `photo_mime`.

## 10. PDF izvještaj — 5 bodova

ReportLab generira PDF potvrdu rezervacije iz povezanih podataka `reservations`, `users` i `parking_spots`.

## 11. Paralelno izvršavanje dretvama — 5 bodova

Open-Meteo dohvat koristi `ThreadPoolExecutor`. **Tools → Test Dretve** uspoređuje iste forecast zahtjeve s:

```text
max_workers = 1
max_workers = 3
```

Koordinate se razriješe prije mjerenja. Zadnji praktični rezultat:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

## 13. Sinkronizacija dretvi — 2 boda

`threading.Lock` štiti zajednički `_request_log` i kratke pristupe geocode cacheu.

## 14. Komunikacija između procesa — 0 bodova / uklonjeno

Nastavnik je pojasnio da očekuje procese A i B kao izvršne EXE aplikacije. Ranija Python demonstracija uklonjena je.

## 20. Udaljeni REST servis — 3 boda

Open-Meteo Geocoding + Forecast API koristi se u stvarnom prikazu parkinga.

## 21. Vlastiti REST servis i klijent — 4 boda

Glavna aplikacija radi na `5000`, a zasebni vlastiti REST servis na `5001`. Glavna aplikacija preko HTTP-a koristi vlastiti servis. Demonstracija je dostupna administratoru pod **Tools → Test REST**.

## 22. REST autentifikacija i autorizacija — 4 boda

Bearer token autentifikacija; `401` za neispravan/nedostajući token i `403` za nedopuštene akcije.

## 23. Simetrično šifriranje AES-GCM — 2 boda

Vlasnik parkinga može unijeti **privatne pristupne upute**. `parking_access_crypto.py` ih šifrira AES-GCM algoritmom prije spremanja. U bazi se nalazi samo binarni sadržaj u `parking_spots.access_instructions`.

Ključ se izvodi iz aplikacijskog `SECRET_KEY` i `parking_id`, a za svako šifriranje koristi se novi slučajni nonce. Javni prikaz parkinga ne prikazuje te podatke. Na **Moje rezervacije** aplikacija dešifrira upute samo za `ACTIVE` rezervacije prijavljenog korisnika.

## 25. SHA-256 + promjenjiva sol + papar — 7 bodova

Kriterij se koristi u dvije jasno odvojene svrhe.

### Integritet rezervacije

`hash_demo.py` računa obični SHA-256 nad stvarnim podacima rezervacije. Za provjeru integriteta se **ne koriste sol ni papar**, u skladu s komentarom nastavnika.

### Korisnički promo kod POPUST

Jedini promo kod je `POPUST`. Svaki korisnik ima vlastitu promjenjivu sol izvedenu iz stabilnog korisničkog ID-a pravilom:

```text
SHA256("ParKING-user-promo-salt:<user_id>")[0:16]
```

Sol se ne sprema u bazu ni datoteku; iz istog `user_id` se uvijek ponovno izvede ista vrijednost. Papar je jedna vrijednost definirana na razini sustava preko `PROMO_SYSTEM_PEPPER`. Za obranu i demonstraciju raspon papra je namjerno ograničen na `1-5`, a zadana Docker vrijednost je `3`.

Administrator na stranici **Promo kodovi** vidi sve korisnike. Za svakog korisnika može uključiti checkbox i postaviti zaseban postotak popusta. Klikom na **Primijeni** za svakog označenog korisnika računa se SHA-256 nad kombinacijom njegove soli, koda `POPUST` i sistemskog papra. Zato isti tekst `POPUST` daje različit hash za različite korisnike.

Kod rezervacije uz promo kod postoji jasno označen **DEMO** dropdown s vrijednostima `1-5`. Aplikacija pri provjeri namjerno prolazi cijeli raspon `1-5`, pronalazi papar koji odgovara spremljenom korisničkom hash-u, ali popust prihvaća samo ako je korisnik u DEMO dropdownu pogodio upravo tu vrijednost. Pogrešan papar ne primjenjuje popust.

Ovaj dropdown postoji isključivo za demonstraciju kriterija; u produkcijskoj aplikaciji tajni papar se ne bi prikazivao niti pogađao kroz korisničko sučelje.

## 28. Dinamička biblioteka — 5 bodova

`native/service_fee.cpp` sadrži C++ klasu `ServiceFeeCalculator` s metodama `calculateFee()` i `calculateTotalFees()`. Docker stvara `native/libservice_fee.so`, a `service_fee.py` je učitava pomoću `ctypes` i koristi u **Admin rezervacije**.

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 3 + 4 + 4 + 2 + 7 + 5 = 71
```

Ne računaju se kriteriji 12, 14–19, 24, 26, 27, 29 i 30.
