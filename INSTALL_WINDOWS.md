# ParKING — instalacija na Windows 11

Ove upute opisuju instalaciju i pokretanje ParKING aplikacije na Windows 11 pomoću Docker Desktopa i WSL2.

## 1. Uključivanje WSL2

Otvoriti PowerShell kao administrator:

```powershell
wsl --install
```

Ako sustav zatraži restart, ponovno pokrenuti računalo. Provjera:

```powershell
wsl --status
wsl -l -v
```

## 2. Instalacija Docker Desktopa

```powershell
winget install -e --id Docker.DockerDesktop
```

Pokrenuti Docker Desktop i pričekati da Docker Engine bude spreman. Provjera:

```powershell
docker --version
docker compose version
```

## 3. Instalacija Gita i SSH pristup GitHubu

```powershell
winget install -e --id Git.Git
```

Ako računalo još nema SSH ključ:

```bash
ssh-keygen -t ed25519 -C "<vas-email>"
cat ~/.ssh/id_ed25519.pub
```

Javni ključ dodati u GitHub pod **Settings → SSH and GPG keys → New SSH key**, zatim provjeriti:

```bash
ssh -T git@github.com
```

## 4. Kloniranje repozitorija

```powershell
git clone git@github.com:HeadshotFTW/ParKING.git
cd ParKING
```

Ako je repozitorij već kloniran:

```powershell
git pull --ff-only origin main
```

Ako povlačenje blokira lokalna izmjena datoteke koju namjerno želite odbaciti, npr. `Dockerfile`:

```powershell
git restore Dockerfile
git pull --ff-only origin main
```

## 5. Build i pokretanje

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail=50
```

U istom Docker containeru rade dva zasebna Flask procesa:

```text
ParKING web aplikacija   → port 5000
ParKING REST API         → port 5001
```

Glavna aplikacija:

```text
http://localhost:5000
```

REST health provjera:

```powershell
curl.exe http://localhost:5001/api/health
```

Očekivani odgovor:

```json
{"port":5001,"service":"ParKING REST API","status":"ok"}
```

### CRLF/LF završeci redaka

Windows tekstualne datoteke često koriste CRLF, dok Linux shell skripte očekuju LF. Projekt zato u `Dockerfile` tijekom builda normalizira `start.sh`:

```dockerfile
RUN mkdir -p /app/data /app/exports \
    && sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh
```

Zbog toga se projekt može graditi i iz Windows checkouta bez ručnog pretvaranja `start.sh`.

## 6. Provjera razdvojenog REST servisa

Bez autentifikacije REST ruta na portu 5001 mora vratiti HTTP 401:

```powershell
curl.exe -i http://localhost:5001/api/parkings
```

Ista ruta na glavnoj web aplikaciji mora vratiti HTTP 404:

```powershell
curl.exe -i http://localhost:5000/api/parkings
```

Time se potvrđuje da REST servis nije registriran u web aplikaciji na portu 5000.

## 7. Demo korisnici i početno stanje

Početno stanje kreira se naredbom:

```powershell
docker compose exec parking python seed.py
```

Demo korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

`seed.py` briše postojeću razvojnu bazu i ponovno kreira početne korisnike, parkinge i rezervaciju. Posebna stranica za uvoz/izvoz demo podataka više se ne koristi.

## 8. Provjera glavnog korisničkog toka

Prijaviti se kao `gost / parking123` i otvoriti **Dostupni parkinzi**.

Provjeriti da:

1. postoje kriteriji lokacije, **Dostupno od**, **Dostupno do** i sortiranja,
2. vrijeme se bira u 24-satnom formatu, npr. `08.09.2026. 08:00` do `08.09.2026. 21:00`,
3. prikazuju se samo parking mjesta bez preklapajuće `ACTIVE` rezervacije,
4. `CANCELLED` rezervacije ne blokiraju dostupnost,
5. odabrani termin prelazi kroz **Detalji → Rezerviraj** i ostaje unaprijed popunjen,
6. nakon rezervacije na **Moje rezervacije** postoje PDF potvrda i SHA-256 provjera integriteta.

24-satni unos koristi Flatpickr iz jsDelivr CDN-a. Bootstrap se također učitava s CDN-a, a stranica **Dretve** koristi Open-Meteo, pa je za potpuno sučelje i mrežne funkcionalnosti preporučena internetska veza.

## 9. Ažuriranje aplikacije

```powershell
git pull --ff-only origin main
docker compose up -d --build
```

Nakon ažuriranja:

```powershell
docker compose ps
docker compose logs --tail=50
curl.exe http://localhost:5001/api/health
```

## 10. Zaustavljanje i ponovno pokretanje

```powershell
docker compose down
docker compose up -d
```

Potpuni rebuild:

```powershell
docker compose up -d --build
```

Direktoriji `./data` i `./exports` vezani su na host računalo i ne brišu se naredbom `docker compose down`.

## 11. Brzi postupak na čistom Windows 11 računalu

```powershell
wsl --install
winget install -e --id Git.Git
winget install -e --id Docker.DockerDesktop
```

Nakon restarta i pokretanja Docker Desktopa:

```powershell
git clone git@github.com:HeadshotFTW/ParKING.git
cd ParKING
docker compose up -d --build
docker compose exec parking python seed.py
docker compose ps
curl.exe http://localhost:5001/api/health
```

## 12. Napomena za Windows

Docker Desktop već uključuje `docker compose`, pa nije potrebno zasebno instalirati `docker-compose-v2`. Ako se Docker CLI koristi iz Ubuntu WSL distribucije, u Docker Desktopu po potrebi uključiti **Settings → Resources → WSL Integration** za tu distribuciju.
