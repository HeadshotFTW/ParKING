# ParKING

ParKING je web aplikacija razvijena u Python Flask frameworku koja korisnicima omogućuje oglašavanje i rezervaciju privatnih parkirnih mjesta.

Projekt je namjerno zadržan malim i preglednim kako bi svaka implementirana funkcionalnost bila jednostavna za demonstraciju i obranu.

## Faza 1

Osnovna verzija podržava registraciju korisnika, prijavu i odjavu, pregled i filtriranje parkinga, CRUD nad parking mjestima, rezervacije, provjeru preklapanja termina, izračun cijene i SQLite bazu.

## Faza 2

Dodana je administratorska funkcionalnost za jasno demonstriranje CRUD operacija nad tri tablice baze: `users`, `parking_spots` i `reservations`.

## Faza 3

Dodani su HR/EN sučelje, INI postavke (`config.ini`) te JSON CRUD za korisničke bilješke u `data/parking_notes.json`.

## Faza 4

Dodani su BLOB spremanje slike parkinga u SQLite i PDF potvrda rezervacije s master-detail podacima iz `reservations`, `users` i `parking_spots`.

## Faza 5

Dodana je demonstracija paralelnog izvršavanja tri mrežna REST zadatka pomoću `ThreadPoolExecutor(max_workers=3)`, usporedba sekvencijalnog i paralelnog vremena te zaštita zajedničkog zapisnika pomoću `threading.Lock`. Koristi se udaljeni Open-Meteo REST servis.

## Faza 6

Dodana je demonstracija komunikacije između dva procesa:

- proces A je Flask aplikacija (`run.py`)
- proces A pokreće proces B pomoću `subprocess.run`
- proces B je zasebna skripta `reservation_worker.py`
- worker provjerava konzistentnost rezervacija u SQLite bazi
- povratni kod `0` znači uspješnu provjeru
- povratni kod `1` znači da su pronađeni problemi u rezervacijama
- povratni kod `2` znači tehničku grešku
- administratorska stranica **Procesi** prikazuje povratni kod, `stdout`, `stderr` i odgovarajuću poruku korisniku
- dostupan je i gumb za kontroliranu simulaciju tehničke greške kako bi se na obrani jasno demonstrirala obrada nenultog povratnog koda

## Faza 7

Dodani su vlastiti REST servis i klijent s Bearer token autentifikacijom i autorizacijom nad resursima `parkings` i `reservations`.

## Faza 8

Dodana je datoteka prilagođenog binarnog formata `data/search_history.bin` za niz zapisa povijesti pretraga. Format ima vlastito `PKSR` zaglavlje, verziju, broj zapisa i binarno zapisane podatke.

## Faza 9

Dodano je simetrično šifriranje i dešifriranje korisničkih bilješki pomoću AES-GCM algoritma:

- stranica **AES** izrađuje šifriranu sigurnosnu kopiju bilješki
- sadržaj se sprema u `exports/notes_user_<id>.aes`
- za svaki izvoz generira se novi slučajni 12-bajtni nonce
- AES ključ se izvodi iz aplikacijske tajne i ID-a korisnika
- ista stranica može dešifrirati datoteku i prikazati izvorne bilješke
- ne šifriraju se korisničke lozinke

## Faza 10

Dodana je demonstracija SHA-256 sažimanja sa soli i paprom:

- stranica **SHA-256** sažima proizvoljni tekst algoritmom SHA-256
- koristi se promjenjiva 16-bajtna sol izvedena po pravilu iz `user_id` i korisničkog imena
- sol se ne pohranjuje u bazu ili datoteku nego se svaki put ponovno izvodi istim pravilom
- koristi se demonstracijski papar iz raspona `0-255` (zadano 137, moguće promijeniti varijablom `HASH_DEMO_PEPPER`)
- provjera namjerno prolazi kroz svih 256 mogućih vrijednosti papra i prikazuje broj pokušaja te pronađenu vrijednost
- demo nije povezan s pohranom korisničkih lozinki

## Struktura projekta

```text
ParKING/
├── app.py
├── run.py
├── api_routes.py
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
├── templates/
├── static/
├── data/
└── exports/
```

## Pokretanje pomoću Dockera

```bash
docker compose up -d --build
```

Aplikacija je dostupna na:

```text
http://localhost:5000
```

## Ažuriranje nakon promjena na GitHubu

```bash
git pull
docker compose up -d --build
```

## Demo korisnici

Ako treba ponovno kreirati razvojne podatke:

```bash
docker compose exec parking python seed.py
```

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

> `seed.py` briše postojeće podatke baze i služi samo za razvoj i demonstraciju.

## Brzi test Faze 5

1. Prijavite se kao `admin / admin123`.
2. Otvorite **Dretve**.
3. Pokažite tri paralelna mrežna zadatka, nazive `parking-weather_*`, vremena izvođenja i `ThreadPoolExecutor(max_workers=3)`.
4. Pokažite `threading.Lock` koji štiti zajednički zapisnik.

## Brzi test Faze 6

1. Prijavite se kao `admin / admin123`.
2. Otvorite **Procesi**.
3. Kliknite **Provjeri rezervacije**.
4. Pokažite da Flask proces A pokreće `reservation_worker.py` kao zaseban proces B i dobiva povratni kod `0` ako je sve ispravno.
5. Kliknite **Simuliraj grešku procesa B**.
6. Pokažite povratni kod `2`, sadržaj `stderr` i poruku koju proces A prikazuje korisniku.
7. U `run.py` pokažite `subprocess.run(...)`, a u `reservation_worker.py` povratne vrijednosti `0`, `1` i `2`.

## Brzi test Faze 9

1. Prijavite se kao korisnik koji ima barem jednu bilješku.
2. Otvorite **AES**.
3. Kliknite **Šifriraj moje bilješke** i provjerite da nastane `exports/notes_user_<id>.aes`.
4. Po želji pokrenite `xxd exports/notes_user_<id>.aes | head` i pokažite da sadržaj nije čitljivi JSON.
5. Kliknite **Dešifriraj sigurnosnu kopiju** i pokažite da se izvorne bilješke ponovno prikažu.
6. U `crypto_store.py` pokažite `AESGCM(...).encrypt(...)` i `AESGCM(...).decrypt(...)`.

## Brzi test Faze 10

1. Prijavite se kao bilo koji korisnik.
2. Otvorite **SHA-256**.
3. Upišite proizvoljni tekst i kliknite **Izračunaj i provjeri**.
4. Pokažite SHA-256 sažetak i promjenjivu sol.
5. Naglasite da se sol ne sprema nego se izvodi iz `user_id` i korisničkog imena.
6. Pokažite da je provjeren cijeli raspon papra `0-255`, odnosno ukupno 256 pokušaja.
7. U `hash_demo.py` pokažite `hashlib.sha256(...)`, `derive_variable_salt(...)` i petlju kroz sve moguće vrijednosti papra.

## Lokalno pokretanje bez Dockera

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Napomena o sigurnosti

Razvojna vrijednost `SECRET_KEY` može se promijeniti varijablom okruženja `SECRET_KEY`. Za javno/produkcijsko postavljanje potrebno je koristiti snažnu tajnu vrijednost i ne spremati je u Git.
