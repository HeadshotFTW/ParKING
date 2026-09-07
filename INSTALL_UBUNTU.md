# ParKING — instalacija na Ubuntu 26.04

Ove upute opisuju instalaciju i pokretanje ParKING aplikacije pomoću Dockera i Docker Composea.

## 1. Kreiranje SSH ključa za GitHub

Ako računalo još nema SSH ključ:

```bash
ssh-keygen -t ed25519 -C "<vas-email>"
cat ~/.ssh/id_ed25519.pub
```

Javni ključ dodati u GitHub pod **Settings → SSH and GPG keys → New SSH key**.

Provjera:

```bash
ssh -T git@github.com
```

## 2. Instalacija Dockera

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
```

Provjera:

```bash
docker --version
docker compose version
```

Dodati trenutnog korisnika u grupu `docker`:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Provjera članstva:

```bash
groups
```

## 3. Kloniranje repozitorija

```bash
git clone git@github.com:HeadshotFTW/ParKING.git
cd ParKING
```

Ako je repozitorij već kloniran:

```bash
git pull --ff-only origin main
```

## 4. Build i pokretanje

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=50
```

U istom containeru rade dva zasebna Flask procesa:

```text
ParKING web aplikacija   → port 5000
ParKING REST API         → port 5001
```

Web aplikacija:

```text
http://localhost:5000
```

REST health provjera:

```bash
curl http://localhost:5001/api/health
```

Očekivani odgovor:

```json
{"port":5001,"service":"ParKING REST API","status":"ok"}
```

## 5. Provjera razdvojenog REST servisa

Bez autentifikacije REST ruta na portu 5001 mora vratiti HTTP 401:

```bash
curl -i http://localhost:5001/api/parkings
```

Ista ruta na glavnoj aplikaciji mora vratiti HTTP 404:

```bash
curl -i http://localhost:5000/api/parkings
```

Time se potvrđuje da REST servis nije registriran u web aplikaciji na portu 5000.

## 6. Demo korisnici i početno stanje

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

`seed.py` briše postojeću razvojnu bazu i ponovno kreira početne korisnike, parkinge i rezervaciju. Posebna stranica za uvoz/izvoz demo podataka više se ne koristi.

## 7. Provjera glavnog korisničkog toka

Prijaviti se kao `gost / parking123` i otvoriti **Dostupni parkinzi**.

Provjeriti da:

1. postoje kriteriji lokacije, **Dostupno od**, **Dostupno do** i sortiranja,
2. vrijeme se bira u 24-satnom formatu, npr. `08.09.2026. 08:00` do `08.09.2026. 21:00`,
3. pretraga prikazuje samo parking mjesta bez preklapajuće `ACTIVE` rezervacije,
4. `CANCELLED` rezervacije ne blokiraju dostupnost,
5. odabrani termin prelazi kroz **Detalji → Rezerviraj** i ostaje unaprijed popunjen,
6. nakon rezervacije na **Moje rezervacije** postoje PDF potvrda i SHA-256 provjera integriteta.

24-satni unos koristi Flatpickr iz jsDelivr CDN-a. Bootstrap se također učitava s CDN-a, a stranica **Dretve** koristi udaljeni Open-Meteo servis, pa je za potpuno sučelje i mrežne funkcionalnosti preporučena internetska veza.

## 8. Ažuriranje aplikacije

```bash
git pull --ff-only origin main
docker compose up -d --build
```

Nakon ažuriranja:

```bash
docker compose ps
docker compose logs --tail=50
curl http://localhost:5001/api/health
```

## 9. Zaustavljanje i ponovno pokretanje

```bash
docker compose down
docker compose up -d
```

Potpuni rebuild:

```bash
docker compose up -d --build
```

Direktoriji `./data` i `./exports` vezani su na host računalo i ne brišu se naredbom `docker compose down`.
