# ParKING

ParKING je web aplikacija razvijena u Python Flask frameworku koja korisnicima omogućuje oglašavanje i rezervaciju privatnih parkirnih mjesta.

Projekt je zadržan malim i preglednim, ali su glavne funkcionalnosti međusobno povezane tako da aplikacija prati stvarni tok rezervacije parkinga: korisnik traži parking za određeni termin, provjerava dostupnost, rezervira ga, prati svoje rezervacije i po potrebi preuzima PDF potvrdu ili provjerava integritet podataka rezervacije.

## Faza 1

Osnovna verzija podržava registraciju korisnika, prijavu i odjavu, pregled parkinga, filtriranje i sortiranje, CRUD nad parking mjestima, rezervacije, provjeru preklapanja termina, izračun cijene i SQLite bazu.

## Faza 2

Dodana je administratorska funkcionalnost za CRUD operacije nad tri tablice baze: `users`, `parking_spots` i `reservations`.

## Faza 3

Dodani su HR/EN sučelje, INI postavke (`config.ini`) te JSON CRUD za korisničke bilješke u `data/parking_notes.json`.

## Faza 4

Dodani su BLOB spremanje slike parkinga u SQLite i PDF potvrda rezervacije s master-detail podacima iz `reservations`, `users` i `parking_spots`.

## Faza 5

Dodano je paralelno izvršavanje tri mrežna REST zadatka pomoću `ThreadPoolExecutor(max_workers=3)`, usporedba sekvencijalnog i paralelnog vremena te zaštita zajedničkog zapisnika pomoću `threading.Lock`. Koristi se udaljeni Open-Meteo REST servis.

## Faza 6

Dodana je komunikacija između dva procesa:

- proces A je Flask aplikacija (`run.py`)
- proces A pokreće proces B pomoću `subprocess.run`
- proces B je zasebna skripta `reservation_worker.py`
- worker provjerava konzistentnost rezervacija u SQLite bazi
- povratni kod `0` znači uspješnu provjeru
- povratni kod `1` znači da su pronađeni problemi u rezervacijama
- povratni kod `2` znači tehničku grešku
- administratorska stranica **Procesi** prikazuje povratni kod, `stdout`, `stderr` i odgovarajuću poruku korisniku
- dostupan je i gumb za kontroliranu simulaciju tehničke greške

## Faza 7

Dodani su vlastiti REST servis i klijent s Bearer token autentifikacijom i autorizacijom nad resursima `parkings` i `reservations`.

REST servis je izdvojen u zasebnu Flask aplikaciju `api_app.py` na portu `5001`, dok glavna web aplikacija radi na portu `5000`. Obje aplikacije rade kao zasebni procesi unutar istog containera, a REST klijent iz glavne aplikacije komunicira s API servisom preko HTTP-a.

## Faza 8

Povijest stvarnih pretraga parkinga sprema se u prilagođenu binarnu datoteku `data/search_history.bin`.

Kada prijavljeni korisnik na stranici **Dostupni parkinzi** pokrene valjanu pretragu, kriteriji se automatski spremaju u binarni zapis. Posebna stranica **Povijest pretraga** prikazuje korisnikove prethodne pretrage i omogućuje njihovo ponavljanje; više nema ručnog unosa testnih binarnih zapisa.

Aktualni format je verzija 2 i sadrži:

- zaglavlje `PKSR`
- verziju formata
- broj zapisa
- `user_id`
- Unix vrijeme zapisa
- opcionalnu maksimalnu cijenu
- UTF-8 polja promjenjive duljine za lokaciju, početak termina, završetak termina i sortiranje

`binary_store.py` i dalje može čitati postojeće zapise verzije 1. Pri sljedećem stvarnom zapisu stari sadržaj se automatski prepisuje u verziju 2.

## Faza 9

Dodano je simetrično šifriranje i dešifriranje korisničkih bilješki pomoću AES-GCM algoritma:

- stranica **AES** izrađuje šifriranu sigurnosnu kopiju bilješki
- sadržaj se sprema u `exports/notes_user_<id>.aes`
- za svaki izvoz generira se novi slučajni 12-bajtni nonce
- AES ključ se izvodi iz aplikacijske tajne i ID-a korisnika
- ista stranica može dešifrirati datoteku i prikazati izvorne bilješke
- korisničke lozinke nisu reverzibilno šifrirane

## Faza 10

SHA-256 je povezan s rezervacijama kao provjera integriteta podataka:

- u **Moje rezervacije** svaka rezervacija ima akciju **SHA-256**
- kontrolni otisak nastaje iz stvarnih podataka rezervacije: korisnika, parkinga, lokacije, termina, statusa, cijene po satu i ukupne cijene
- promjena bilo kojeg od tih podataka mijenja kontrolni otisak
- koristi se promjenjiva 16-bajtna sol izvedena po pravilu iz `user_id` i korisničkog imena
- sol se ne pohranjuje u bazu ili datoteku nego se svaki put ponovno izvodi istim pravilom
- koristi se papar iz raspona `0-255` (zadano 137, moguće promijeniti varijablom `HASH_DEMO_PEPPER`)
- provjera prolazi kroz svih 256 mogućih vrijednosti papra i potvrđuje odgovara li zadani kontrolni otisak trenutačnim podacima rezervacije

## Faza 11

Pretraga parkinga proširena je stvarnom provjerom dostupnosti u vremenskom intervalu.

Na stranici **Dostupni parkinzi** korisnik unosi:

- lokaciju
- početak željenog termina
- završetak željenog termina
- opcionalnu maksimalnu cijenu po satu
- način sortiranja

Aplikacija prikazuje samo parkirna mjesta koja zadovoljavaju kriterije cijene/lokacije i nemaju `ACTIVE` rezervaciju koja se preklapa s traženim intervalom. Otkazane (`CANCELLED`) rezervacije ne blokiraju dostupnost. Provjera koristi isto pravilo preklapanja kao i spremanje nove rezervacije:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

Odabrani termin i ostali kriteriji prenose se s popisa parkinga na detalje parkinga i dalje na formu za rezervaciju, pa korisnik ne mora ponovno unositi datum i vrijeme.

Unos datuma i vremena koristi Flatpickr u 24-satnom formatu. Hrvatsko sučelje prikazuje npr. `08.09.2026. 21:00`, a backend i dalje prima ISO vrijednost oblika `2026-09-08T21:00`. Isti 24-satni unos koristi se na pretrazi dostupnosti, korisničkoj rezervaciji i administratorskoj formi rezervacije.

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
├── INSTALL_UBUNTU.md
├── INSTALL_WINDOWS.md
├── OBRANA.md
├── AUDIT.md
├── README_IMPLEMENTIRANO.md
├── templates/
├── static/
├── data/
└── exports/
```

## Pokretanje pomoću Dockera

Detaljne upute za čistu instalaciju na Ubuntu 26.04 nalaze se u `INSTALL_UBUNTU.md`, a za Windows 11 u `INSTALL_WINDOWS.md`.

Za već pripremljeno računalo dovoljno je:

```bash
docker compose up -d --build
```

Glavna aplikacija je dostupna na:

```text
http://localhost:5000
```

REST API radi zasebno na:

```text
http://localhost:5001
```

Health provjera:

```bash
curl http://localhost:5001/api/health
```

## Osnovni korisnički tok

Nakon prijave otvoriti **Dostupni parkinzi**, odabrati početak i završetak željenog termina u 24-satnom formatu, po želji zadati lokaciju i maksimalnu cijenu te pokrenuti pretragu. Prikazuju se samo parking mjesta dostupna tijekom cijelog zadanog intervala. Termin se zatim prenosi kroz **Detalji → Rezerviraj**.

Svaka valjana pretraga prijavljenog korisnika automatski se zapisuje u `data/search_history.bin`. Stranica **Povijest pretraga** prikazuje te stvarne pretrage i nudi akciju **Ponovi** koja vraća spremljene kriterije na stranicu dostupnih parkinga.

Nakon rezervacije korisnik na stranici **Moje rezervacije** može vidjeti trajanje, ukupnu cijenu i status rezervacije, preuzeti PDF potvrdu te otvoriti SHA-256 provjeru integriteta rezervacije.

## Ažuriranje nakon promjena na GitHubu

```bash
git pull
docker compose up -d --build
```

## Demo korisnici i podaci

Početno demonstracijsko stanje kreira se naredbom:

```bash
docker compose exec parking python seed.py
```

Nakon izvršavanja dostupni su korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

`seed.py` briše postojeće podatke baze i ponovno kreira početno demo stanje, zato ga treba pokretati samo kada je namjerno potrebno resetirati demonstracijske podatke.

## Brza provjera odvojenog REST servisa

```bash
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano:

- port `5001` health vraća `status: ok`
- `/api/parkings` na portu `5001` bez Bearer tokena vraća `401`
- `/api/parkings` na portu `5000` vraća `404`, jer API nije dio glavne web aplikacije

Autentificirani poziv koristi stvarni API token korisnika:

```bash
curl -H "Authorization: Bearer <API_TOKEN>" http://localhost:5001/api/parkings
```

API token se ne zapisuje u dokumentaciju niti sprema u Git.

## Lokalno pokretanje bez Dockera

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x start.sh
./start.sh
```

`start.sh` pokreće zasebni REST proces na portu `5001` i glavnu web aplikaciju na portu `5000`.

### Windows

Za lokalno pokretanje bez Dockera potrebno je u dva terminala pokrenuti:

```powershell
python api_app.py
```

te:

```powershell
python run.py
```

## Napomena o sigurnosti

Razvojna vrijednost `SECRET_KEY` može se promijeniti varijablom okruženja `SECRET_KEY`. Za javno/produkcijsko postavljanje potrebno je koristiti snažnu tajnu vrijednost i ne spremati je u Git.
