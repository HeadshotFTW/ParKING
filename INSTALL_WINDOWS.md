# ParKING — instalacija na Windows 11

Ove upute opisuju najjednostavniji način instalacije i pokretanja ParKING aplikacije na Windows 11 pomoću Docker Desktopa i WSL2.

## 1. Uključivanje WSL2

Otvoriti PowerShell kao administrator i pokrenuti:

```powershell
wsl --install
```

Ako sustav zatraži restart, ponovno pokrenuti računalo.

Provjera WSL-a:

```powershell
wsl --status
```

Po potrebi provjeriti instalirane distribucije:

```powershell
wsl -l -v
```

## 2. Instalacija Docker Desktopa pomoću wingeta

Na Windows 11 najjednostavnije je instalirati Docker Desktop iz PowerShella pomoću `winget`:

```powershell
winget install -e --id Docker.DockerDesktop
```

Nakon instalacije pokrenuti **Docker Desktop** i pričekati da Docker Engine bude spreman. Docker Desktop treba koristiti WSL 2 backend.

Provjera:

```powershell
docker --version
docker compose version
```

Ako `winget` nije dostupan, Docker Desktop se može instalirati i klasičnim instalacijskim paketom za Windows.

## 3. Instalacija Gita i SSH pristup GitHubu

Ako Git nije instaliran, može se instalirati pomoću `winget`:

```powershell
winget install -e --id Git.Git
```

Nakon instalacije po potrebi ponovno otvoriti PowerShell ili Git Bash.

Ako računalo još nema SSH ključ:

```bash
ssh-keygen -t ed25519 -C "<vas-email>"
```

Prikaz javnog ključa u Git Bashu:

```bash
cat ~/.ssh/id_ed25519.pub
```

Javni ključ dodati u GitHub račun pod **Settings → SSH and GPG keys → New SSH key**.

Provjera SSH pristupa:

```bash
ssh -T git@github.com
```

## 4. Kloniranje repozitorija

U Git Bashu ili PowerShellu:

```bash
git clone git@github.com:HeadshotFTW/ParKING.git
cd ParKING
```

Ako je repozitorij već kloniran:

```bash
git pull
```

## 5. Build i pokretanje

Pokrenuti iz korijena repozitorija:

```bash
docker compose up -d --build
```

Provjera containera:

```bash
docker compose ps
```

Provjera logova:

```bash
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

```bash
curl http://localhost:5001/api/health
```

Očekivani odgovor:

```json
{"port":5001,"service":"ParKING REST API","status":"ok"}
```

## 6. Provjera razdvojenog REST servisa

REST API bez Bearer tokena mora odbiti zahtjev:

```bash
curl -i http://localhost:5001/api/parkings
```

Očekuje se:

```text
HTTP/1.1 401 UNAUTHORIZED
```

Glavna web aplikacija na portu 5000 nema `/api/parkings` rutu:

```bash
curl -i http://localhost:5000/api/parkings
```

Očekuje se:

```text
HTTP/1.1 404 NOT FOUND
```

Za autentificirani REST poziv koristiti API token stvarnog korisnika:

```bash
curl -H "Authorization: Bearer <API_TOKEN>" http://localhost:5001/api/parkings
```

API token ne zapisivati u dokumentaciju niti spremati u Git.

## 7. Demo korisnici i demo podaci

Osnovni demo korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

Ako treba vratiti osnovne razvojne podatke:

```bash
docker compose exec parking python seed.py
```

> `seed.py` briše postojeću razvojnu bazu. Koristiti ga samo kada je namjerno potrebno vratiti početno demo stanje.

Za potpuno demonstracijsko stanje preporučuje se koristiti referentni dataset:

```text
demo/parking-demo.json
```

Postupak:

1. otvoriti `http://localhost:5000`
2. prijaviti se kao `admin / admin123`
3. otvoriti **Test → Demo podaci**
4. odabrati **Import**
5. učitati `demo/parking-demo.json`

Import zamjenjuje postojeće korisnike, parkinge i rezervacije demonstracijskim podacima.

## 8. Ažuriranje aplikacije

```bash
git pull
docker compose up -d --build
```

Nakon ažuriranja provjeriti:

```bash
docker compose ps
docker compose logs --tail=50
curl http://localhost:5001/api/health
```

## 9. Zaustavljanje i ponovno pokretanje

Zaustavljanje:

```bash
docker compose down
```

Ponovno pokretanje bez rebuilda:

```bash
docker compose up -d
```

Potpuni rebuild:

```bash
docker compose up -d --build
```

## 10. Brzi postupak na čistom Windows 11 računalu

U PowerShellu kao administrator:

```powershell
wsl --install
winget install -e --id Git.Git
winget install -e --id Docker.DockerDesktop
```

Nakon eventualnog restarta i pokretanja Docker Desktopa:

```bash
git clone git@github.com:HeadshotFTW/ParKING.git
cd ParKING
docker compose up -d --build
docker compose ps
curl http://localhost:5001/api/health
```

## 11. Napomena za Windows

Za ovaj projekt nije potrebno ručno instalirati `docker-compose-v2` kao na Ubuntu sustavu. Docker Desktop već uključuje naredbu:

```bash
docker compose
```

Ako se naredba `docker` ne izvršava, prvo provjeriti je li Docker Desktop pokrenut i je li Docker Engine spreman.
