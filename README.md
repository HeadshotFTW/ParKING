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

REST servis je izdvojen u zasebnu Flask aplikaciju `api_app.py` na portu `5001`, dok glavna web aplikacija radi na portu `5000`. Obje aplikacije rade kao zasebni procesi unutar istog containera, a REST klijent iz glavne aplikacije komunicira s API servisom preko HTTP-a.

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

## Faza 11

Dodani su administratorski export i import demonstracijskih podataka pod **Test → Demo podaci**. Jedan JSON dataset može sadržavati korisnike, parkinge, rezervacije, JSON bilješke, BLOB fotografije i binarnu povijest pretraga. Password hash i postojeći API tokeni ne izvoze se. Dataset je namijenjen brzom vraćanju poznatog stanja prije demonstracije.

## Struktura projekta

```text
ParKING/
├── app.py
├── run.py
├── api_app.py
├── start.sh
├── demo_data.py
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
├── OBRANA.md
├── templates/
├── static/
├── data/
└── exports/
```

## Pokretanje pomoću Dockera

Detaljne upute za čistu instalaciju na Ubuntu 26.04 nalaze se u `INSTALL_UBUNTU.md`.

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

## Ažuriranje nakon promjena na GitHubu

```bash
git pull
docker compose up -d --build
```

## Demo korisnici

Ako treba ponovno kreirati osnovne razvojne podatke:

```bash
docker compose exec parking python seed.py
```

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

> `seed.py` briše postojeće podatke baze i služi samo za razvoj i demonstraciju.

Za potpuno demonstracijsko stanje preporučuje se koristiti **Test → Demo podaci → Import** i učitati spremljeni JSON dataset.

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
