# ParKING — implementirane funkcionalnosti

Ovaj dokument navodi samo funkcionalnosti koje su implementirane i koje se računaju u popunjenoj prijavnici.

**Konzervativna procjena: 70 bodova.**

## 1. Korisničke klase — 3 boda

Implementirane su klase `User`, `ParkingSpot` i `Reservation` kao SQLAlchemy modeli s atributima i metodama koje se koriste kroz poslovnu logiku aplikacije.

## 2. Forme i komunikacija među formama — 4 boda

Aplikacija sadrži više od tri forme/dijaloga: prijava, registracija, pretraga parkinga, dodavanje/uređivanje parkinga, detalji parkinga, rezervacija, moje rezervacije, bilješke te administratorske forme.

Na stranici **Dostupni parkinzi** korisnik odabire termin i ostale kriterije. `start_time` i `end_time` prenose se kroz **Detalji → Rezerviraj**, pa su u rezervacijskoj formi već popunjeni. Datumsko-vremenska polja koriste 24-satni Flatpickr prikaz.

## 3. Višejezično sučelje — 4 boda

Podržani su hrvatski i engleski jezik. Jezik se može mijenjati tijekom rada aplikacije preko HR/EN poveznica. Prevedeno je više od pet stranica i dijaloga.

## 4. INI postavke — 2 boda

Postavke se čitaju i zapisuju u `config.ini` pomoću `configparser`. Koriste se `default_language` i `items_per_page`, a administrator ih mijenja kroz stranicu **Postavke**.

## 5. JSON spremanje i CRUD — 4 boda

Korisničke bilješke spremaju se u `data/parking_notes.json`. Podržani su čitanje, dodavanje, uređivanje i brisanje zapisa. Logika je u `json_store.py`, a korisničko sučelje na stranici **Bilješke**.

## 6. Prilagođeni binarni format — 3 boda

Stvarne pretrage parkinga automatski se spremaju u `data/search_history.bin`. Binarni zapis se više ne dodaje ručno preko testne stranice.

Format koristi vlastito zaglavlje `PKSR`, verziju i broj zapisa. Verzija 2 sprema `user_id`, Unix vrijeme, opcionalnu maksimalnu cijenu te UTF-8 polja promjenjive duljine za lokaciju, početak termina, završetak termina i sortiranje. `binary_store.py` može čitati verziju 1 i migrirati je u verziju 2.

Stranica **Povijest pretraga** prikazuje zapise trenutno prijavljenog korisnika i omogućuje ponavljanje spremljene pretrage.

## 7. Baza podataka i CRUD — 6 bodova

Aplikacija koristi SQLite preko SQLAlchemy ORM-a. CRUD se demonstrira nad tablicama `users`, `parking_spots` i `reservations`.

## 8. Sortiranje, filtriranje, izračunato i lookup polje — 5 bodova

Parkinzi se filtriraju po lokaciji, maksimalnoj cijeni i vremenskoj dostupnosti te sortiraju po cijeni i nazivu.

Kod vremenske dostupnosti parking se isključuje samo ako postoji `ACTIVE` rezervacija koja zadovoljava:

```text
Reservation.start_time < traženi_završetak
AND
Reservation.end_time > traženi_početak
```

`CANCELLED` rezervacije ne blokiraju parking.

Izračunato polje je ukupna cijena rezervacije preko `Reservation.total_price()`. Lookup podaci dohvaćaju se ORM relacijama poput `Reservation.parking` i `ParkingSpot.owner`.

## 9. BLOB polje u bazi — 3 boda

Fotografija parkinga sprema se izravno u SQLite BLOB polje `photo`, uz MIME tip `photo_mime`. Slika se može učitati, prikazati, zamijeniti i ukloniti. Podržani su JPEG, PNG i WebP.

## 10. PDF izvještaj — 5 bodova

ReportLab generira PDF potvrdu rezervacije s podacima iz tablica `reservations`, `users` i `parking_spots`. PDF sadrži termin, trajanje, status, korisnika, parking, vlasnika, cijenu po satu i ukupnu cijenu.

## 11. Paralelno izvršavanje dretvama — 5 bodova

Open-Meteo dohvat sada se koristi i u glavnom toku aplikacije. Na stranici **Dostupni parkinzi** vremenski podaci za različite gradove prikazanih parkinga dohvaćaju se paralelno pomoću `ThreadPoolExecutor`. Podržane lokacije su Zagreb, Samobor i Velika Gorica, a više parkinga u istom gradu koristi isti rezultat jednog HTTP poziva.

Administratorska stranica **Test → Dretve** zadržana je kao detaljan pregled iste implementacije i koristi `ThreadPoolExecutor(max_workers=3)` za sva tri grada. Prikazuje nazive radnih dretvi, sekvencijalno i paralelno vrijeme te faktor ubrzanja.

## 13. Sinkronizacija dretvi — 2 boda

`fetch_weather()` nakon svakog Open-Meteo poziva zapisuje rezultat u zajednički `_request_log`. Taj zapis je kritična sekcija i zaštićen je pomoću `threading.Lock`, tako da više dretvi ne mijenja zajednički zapisnik istodobno. Isti Lock koristi se i kod resetiranja zapisnika i izrade njegove kopije.

## 14. Komunikacija između procesa — 4 boda

Provjera između procesa integrirana je u stvarni administratorski tok. Na stranici **Admin rezervacije** gumb **Provjeri rezervacije** pokreće zasebni proces B `reservation_worker.py` pomoću `subprocess.run` iz glavne Flask aplikacije, procesa A.

Worker čita SQLite bazu i provjerava neispravne vremenske intervale i preklapanja `ACTIVE` rezervacija. Vraća:

```text
0 = podaci su ispravni
1 = pronađen je problem u rezervacijama
2 = tehnička greška
```

Proces A čita `returncode`, `stdout` i `stderr` te rezultat prikazuje izravno iznad tablice rezervacija. Zasebna stranica **Procesi** više se ne koristi.

## 20. Udaljeni REST servis — 3 boda

Aplikacija HTTP zahtjevima dohvaća trenutačne vremenske podatke s udaljenog Open-Meteo REST servisa. Podaci nisu samo tehnički prikaz: temperatura i brzina vjetra prikazuju se uz stvarne parkinge na **Dostupni parkinzi** i na **Detalji parkinga** za podržane gradove. Isti REST pozivi koriste se i u paralelnoj implementaciji dretvi.

Ako je Open-Meteo privremeno nedostupan, parking stranice ostaju funkcionalne i samo izostavljaju vremenski podatak.

## 21. Vlastiti REST servis i klijent — 4 boda

Glavna Flask aplikacija `run.py` radi na portu `5000`, a zasebna Flask aplikacija `api_app.py` kao zaseban proces na portu `5001`. Glavna aplikacija kao REST klijent preko HTTP-a koristi vlastiti API.

Resursi su:

```text
/api/parkings
/api/reservations
```

Za `parkings` postoje GET/POST i GET/PUT/DELETE nad pojedinim parkingom. Za `reservations` postoje GET/POST i GET/DELETE nad pojedinom rezervacijom.

## 22. REST autentifikacija i autorizacija — 4 boda

REST API koristi Bearer token u zaglavlju `Authorization`. Nedostajući ili pogrešan token vraća `401`.

Obični korisnik ne može mijenjati tuđi parking niti dohvatiti tuđu rezervaciju, što vraća `403`. Vlasnik parkinga i administrator imaju šire ovlasti, a administrator može pristupati svim rezervacijama.

## 23. Simetrično šifriranje AES-GCM — 2 boda

AES-GCM više nije izdvojena testna stranica. Funkcionalnost je integrirana u **Bilješke** kao sigurnosna kopija stvarnih korisničkih podataka.

Na stranici **Bilješke** korisnik može:

- izraditi šifriranu sigurnosnu kopiju svojih trenutačnih JSON bilješki
- otvoriti i dešifrirati postojeću kopiju
- pregledati dešifrirani sadržaj unutar iste stranice

Datoteka se sprema kao `exports/notes_user_<id>.aes`, koristi vlastito `PKAE` zaglavlje, AES-GCM i novi slučajni nonce za svaki izvoz. Korisničke lozinke nisu reverzibilno šifrirane.

## 25. SHA-256, sol i papar — 7 bodova

SHA-256 je integriran u rezervacije kao kontrolni otisak integriteta. Korisnik otvara provjeru preko **Moje rezervacije → SHA-256**.

Ulaz čine stvarni podaci rezervacije: ID, korisnik, parking, lokacija, početak, završetak, status, cijena po satu i ukupna cijena.

Promjenjiva sol se ne sprema nego se deterministički izvodi pravilom:

```text
SHA256("ParKING-SHA256-salt:<user_id>:<username>")[0:16]
```

Koristi se papar iz raspona `0-255`, a provjera prolazi kroz svih 256 mogućih vrijednosti i koristi `hmac.compare_digest`.

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 4 + 3 + 4 + 4 + 2 + 7 = 70
```

Ne računaju se kriterij 12 niti neimplementirani kriteriji 15–19, 24, 26 i 27–30.
