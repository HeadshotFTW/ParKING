# ParKING

ParKING je web aplikacija razvijena u Python Flask frameworku koja korisnicima omogućuje oglašavanje i rezervaciju privatnih parkirnih mjesta.

Projekt je namjerno zadržan malim i preglednim kako bi svaka implementirana funkcionalnost bila jednostavna za demonstraciju i obranu.

## Faza 1

Trenutačna verzija podržava:

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

## Struktura projekta

```text
ParKING/
├── app.py
├── models.py
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

SQLite baza ostaje u lokalnom direktoriju `data/` i preživljava ponovno kreiranje containera.

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

> `seed.py` je namijenjen isključivo razvoju i demonstraciji jer briše postojeće podatke.

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

## Brzi test

1. Prijavite se kao `vlasnik` i provjerite njegove parkinge.
2. Odjavite se i prijavite kao `gost`.
3. Rezervirajte parking.
4. Otvorite `Moje rezervacije`.
5. Pokušajte napraviti drugu rezervaciju koja se vremenski preklapa s postojećom.
6. Aplikacija treba odbiti preklapajuću rezervaciju.

## Napomena o sigurnosti

Razvojna vrijednost `SECRET_KEY` može se promijeniti varijablom okruženja `SECRET_KEY`. Za javno/produkcijsko postavljanje potrebno je koristiti snažnu tajnu vrijednost i ne spremati je u Git.
