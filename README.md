# ParKING

ParKING je web aplikacija razvijena u Python Flask frameworku koja korisnicima omogućuje oglašavanje i rezervaciju privatnih parkirnih mjesta.

Projekt je namjerno zadržan malim i preglednim kako bi svaka implementirana funkcionalnost bila jednostavna za demonstraciju i obranu.

## Faza 1

Osnovna verzija podržava:

- registraciju korisnika
- prijavu i odjavu
- pregled dostupnih parkinga
- filtriranje po lokaciji
- sortiranje po cijeni i nazivu
- dodavanje, uređivanje i brisanje vlastitih parkinga
- rezervaciju tuđeg parkinga
- provjeru preklapanja termina rezervacija
- pregled i otkazivanje vlastitih rezervacija
- automatski izračun cijene rezervacije
- SQLite bazu podataka
- Docker pokretanje na Windows 11 i Linuxu

## Faza 2

Dodana je administratorska funkcionalnost za jasno demonstriranje CRUD operacija nad tri tablice baze:

- `users` — pregled, dodavanje, uređivanje i brisanje korisnika
- `parking_spots` — pregled, dodavanje, uređivanje i brisanje parkinga
- `reservations` — pregled, dodavanje, uređivanje i brisanje rezervacija

Administrator ima dodatne izbornike **Korisnici** i **Admin rezervacije**.

Na popisu rezervacija prikazuju se i povezana lookup polja (`user.username`, `parking.name`) te izračunata ukupna cijena rezervacije.

## Faza 3

Dodane su tri funkcionalnosti za kriterije projekta:

- **HR/EN sučelje** — jezik se mijenja tijekom rada aplikacije preko HR/EN poveznica; prevedeno je više od 5 stranica/formi.
- **INI postavke** — `config.ini` s postavkama `default_language` i `items_per_page`. Administrator ih mijenja kroz **Postavke**; postavka broja stavki stvarno određuje veličinu stranice popisa parkinga.
- **JSON CRUD** — korisničke bilješke pohranjuju se kao niz zapisa u `data/parking_notes.json`. Podržano je čitanje, dodavanje, uređivanje i brisanje.

## Struktura projekta

```text
ParKING/
├── app.py
├── models.py
├── json_store.py
├── translations.py
├── config.ini
├── seed.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── templates/
├── static/
├── data/
└── exports/
```

## Pokretanje pomoću Dockera

Preduvjet je instaliran Docker i Docker Compose.

```bash
docker compose up -d --build
```

Aplikacija je zatim dostupna na:

```text
http://localhost:5000
```

Za pregled logova:

```bash
docker compose logs -f
```

Za gašenje:

```bash
docker compose down
```

SQLite baza i JSON bilješke ostaju u lokalnom direktoriju `data/`. `config.ini` je također montiran u container pa administratorske promjene postavki ostaju sačuvane nakon ponovnog kreiranja containera.

## Ažuriranje nakon promjena na GitHubu

Ako je projekt već kloniran lokalno:

```bash
git pull
docker compose up -d --build
```

## Demo podaci

Nakon što je container pokrenut, demo podatke možete kreirati naredbom:

```bash
docker compose exec parking python seed.py
```

Skripta briše postojeću razvojnu bazu i kreira sljedeće korisnike:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

Kreira i dva parkinga te jednu demo rezervaciju.

> `seed.py` je namijenjen isključivo razvoju i demonstraciji jer briše postojeće podatke baze.

## Brzi test Faze 2

1. Pokrenite `seed.py`.
2. Prijavite se kao `admin / admin123`.
3. Otvorite **Korisnici** i demonstrirajte dodavanje, uređivanje i brisanje korisnika.
4. Otvorite **Admin rezervacije** i demonstrirajte dodavanje, uređivanje i brisanje rezervacije.
5. Na listi rezervacija pokažite korisničko ime i naziv parkinga kao lookup vrijednosti.
6. Pokažite izračunatu ukupnu cijenu rezervacije.
7. Na glavnom popisu parkinga pokažite filtriranje po lokaciji i sortiranje po cijeni/nazivu.

## Brzi test Faze 3

1. Kliknite **HR / EN** u gornjem izborniku i pokažite promjenu jezika na više stranica bez izlaska iz aplikacije.
2. Kao administrator otvorite **Postavke**. Promijenite zadani jezik i `items_per_page`, spremite i pokažite sadržaj `config.ini`.
3. Na popisu parkinga pokažite da `items_per_page` određuje broj stavki po stranici.
4. Kao prijavljeni korisnik otvorite **Bilješke**.
5. Dodajte nekoliko bilješki, zatim jednu uredite i jednu obrišite.
6. U host direktoriju otvorite `data/parking_notes.json` i pokažite da se radi o nizu JSON zapisa s poljima `id`, `user_id`, `title` i `text`.

## Lokalno pokretanje bez Dockera

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Napomena o sigurnosti

Razvojna vrijednost `SECRET_KEY` može se promijeniti varijablom okruženja `SECRET_KEY`. Za javno/produkcijsko postavljanje potrebno je koristiti snažnu tajnu vrijednost i ne spremati je u Git.
