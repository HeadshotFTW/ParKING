# ParKING

ParKING je Flask web aplikacija za oglašavanje i rezervaciju privatnih parkirnih mjesta. Glavne funkcionalnosti povezane su u jedan stvarni korisnički tok: korisnik traži parking za određeni termin, provjerava dostupnost, vidi trenutačne vremenske podatke za lokaciju, rezervira parking, prati rezervacije i koristi dodatne funkcije poput PDF potvrde, SHA-256 provjere integriteta, povijesti pretraga i šifriranih sigurnosnih kopija bilješki.

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
- SHA-256 kontrolni otisak integriteta rezervacije
- provjera konzistentnosti rezervacija pomoću zasebnog procesa B
- Open-Meteo vremenski podaci prikazani uz stvarne parkinge
- ThreadPoolExecutor + `threading.Lock` za paralelni dohvat vremenskih podataka
- vlastiti REST API s Bearer autentifikacijom i autorizacijom

## Dostupnost parkinga prema terminu

Na stranici **Dostupni parkinzi** korisnik zadaje:

- lokaciju
- početak termina
- završetak termina
- opcionalnu maksimalnu cijenu po satu
- sortiranje

Parking se prikazuje ako nema `ACTIVE` rezervaciju koja se preklapa s traženim intervalom. Koristi se pravilo:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

`CANCELLED` rezervacije ne blokiraju dostupnost. Odabrani termin prenosi se kroz **Detalji → Rezerviraj**, pa ga korisnik ne mora ponovno unositi.

## Vremenski podaci uz parkinge

Open-Meteo više nije vezan samo uz tehničku stranicu za dretve. Na karticama pod **Dostupni parkinzi** i na stranici **Detalji parkinga** prikazuju se trenutačna temperatura i brzina vjetra za grad parkinga.

Grad se automatski izdvaja iz tekstualne lokacije parkinga i, ako nije jedna od unaprijed poznatih lokacija, pretvara u koordinate preko Open-Meteo Geocoding API-ja. Primjeri podržanog unosa:

```text
Zadar, Obala kneza Branimira 10
Split, Vukovarska 15
23000 Zadar, Ulica 1
```

Geokodiranje je ograničeno na Hrvatsku (`countryCode=HR`), pa se vremenski podatak može prikazati za bilo koji hrvatski grad koji Open-Meteo prepoznaje, a ne samo za Zagreb, Samobor i Veliku Goricu.

Ako je na istoj stranici prikazano više različitih gradova, `parking_availability.py` poziva `fetch_weather_for_parking_locations()` iz `parallel_tasks.py`, a vremenski zahtjevi izvršavaju se paralelno kroz `ThreadPoolExecutor`. Više parkinga u istom gradu dijeli isti dohvaćeni rezultat, pa se isti grad ne dohvaća više puta za jednu stranicu.

`fetch_weather()` nakon završetka zahtjeva zapisuje podatke u zajednički `_request_log`. Taj zajednički resurs zaštićen je s `threading.Lock`, pa više dretvi ne mijenja zapisnik istodobno. Ako Open-Meteo privremeno nije dostupan ili lokacija nije prepoznata, popis i detalji parkinga i dalje se prikazuju bez vremenskog podatka.

Administratorska stranica **Test → Dretve** više ne koristi tri unaprijed zadana grada kao ulaz. Gradovi se dohvaćaju iz stvarnih lokacija objavljenih parkinga u bazi, uklanjaju se duplikati, a isti skup gradova izvršava se najprije sekvencijalno pa paralelno kroz `ThreadPoolExecutor` s najviše tri radne dretve. Na stranici se prikazuju pronađeni gradovi, vremena izvođenja, ubrzanje i naziv dretve za svaki rezultat. Tekstualni blok **Sinkronizacija** uklonjen je sa stranice, ali `threading.Lock` i dalje ostaje u kodu i štiti kritičnu sekciju zajedničkog zapisnika.

## Povijest pretraga i vlastiti binarni format

Svaka valjana pretraga prijavljenog korisnika automatski se sprema u:

```text
data/search_history.bin
```

Stranica **Povijest pretraga** prikazuje stvarne prethodne pretrage korisnika i omogućuje akciju **Ponovi**.

Aktualni binarni format je `PKSR` verzija 2. Sprema `user_id`, Unix vrijeme, opcionalnu maksimalnu cijenu te UTF-8 polja promjenjive duljine za lokaciju, početak, završetak i sortiranje. `binary_store.py` može čitati i stariju verziju 1 te je pri sljedećem zapisu migrira u verziju 2.

## Bilješke i AES-GCM sigurnosna kopija

Korisničke bilješke spremaju se kao JSON u:

```text
data/parking_notes.json
```

Na istoj stranici **Bilješke** nalaze se akcije:

- **Izradi šifriranu kopiju**
- **Otvori šifriranu kopiju**

AES-GCM sigurnosna kopija sprema se u:

```text
exports/notes_user_<id>.aes
```

Datoteka koristi vlastito `PKAE` zaglavlje i novi slučajni nonce za svaki izvoz. Nakon dešifriranja aplikacija prikazuje sadržaj sigurnosne kopije uz postojeće bilješke. Korisničke lozinke nisu reverzibilno šifrirane.

## SHA-256 integritet rezervacije

Na stranici **Moje rezervacije** svaka rezervacija ima akciju **SHA-256**. Kontrolni otisak računa se iz stvarnih podataka rezervacije: ID-a, korisnika, parkinga, lokacije, termina, statusa, cijene po satu i ukupne cijene.

Koristi se promjenjiva sol koja se deterministički izvodi iz `user_id` i korisničkog imena, ne sprema se u bazu ili datoteku, te papar iz raspona `0-255`. Provjera prolazi kroz svih 256 mogućih vrijednosti papra.

## Provjera konzistentnosti rezervacija kao zaseban proces

Na stranici **Admin rezervacije** administrator ima gumb **Provjeri rezervacije**. Glavna Flask aplikacija, kao proces A, pomoću `subprocess.run` pokreće zasebni proces B:

```text
reservation_worker.py
```

Worker provjerava neispravne vremenske intervale i preklapanja `ACTIVE` rezervacija u SQLite bazi. Vraća:

```text
0 = sve je ispravno
1 = pronađeni su problemi u podacima
2 = tehnička greška
```

Glavna aplikacija čita `returncode`, `stdout` i `stderr` te rezultat prikazuje izravno iznad tablice rezervacija. Zasebna stranica **Procesi** više se ne koristi.

## Vlastiti REST servis

Glavna web aplikacija radi na portu `5000`, a vlastiti REST servis kao zasebna Flask aplikacija/proces na portu `5001`.

```text
run.py      → web aplikacija → 5000
api_app.py  → REST API       → 5001
```

API izlaže resurse:

```text
/api/parkings
/api/reservations
```

Koristi Bearer token autentifikaciju i autorizaciju po korisniku i ulozi.

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
├── reservation_worker.py
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

Glavna aplikacija:

```text
http://localhost:5000
```

REST health:

```bash
curl http://localhost:5001/api/health
```

## Demo stanje

Početno stanje kreira se naredbom:

```bash
docker compose exec parking python seed.py
```

Demo korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

`seed.py` briše postojeću razvojnu bazu i ponovno kreira početne korisnike, četiri parkinga i jednu rezervaciju. Početni parkingi nalaze se u Zagrebu, Zadru i Splitu, pa **Test → Dretve** nakon seeda automatski dobiva najmanje tri različita grada za usporedbu sekvencijalnog i paralelnog izvođenja.

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

Autentificirani poziv:

```bash
curl -H "Authorization: Bearer <API_TOKEN>" http://localhost:5001/api/parkings
```

API token ne zapisivati u dokumentaciju niti spremati u Git.

## Napomena o sigurnosti

Razvojna vrijednost `SECRET_KEY` može se promijeniti varijablom okruženja `SECRET_KEY`. Za javno ili produkcijsko postavljanje potrebno je koristiti snažnu tajnu vrijednost i ne spremati je u Git.
