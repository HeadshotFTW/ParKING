# ParKING — instalacija na Ubuntu 26.04

Ove upute opisuju najjednostavniji način instalacije i pokretanja ParKING aplikacije pomoću Dockera i Docker Composea.

## 1. Kreiranje SSH ključa za GitHub

Ako računalo još nema SSH ključ:

```bash
ssh-keygen -t ed25519 -C "<vas-email>"
```

Prikaz javnog ključa:

```bash
cat ~/.ssh/id_ed25519.pub
```

Javni ključ dodati u GitHub račun pod **Settings → SSH and GPG keys → New SSH key**.

Provjera GitHub SSH pristupa:

```bash
ssh -T git@github.com
```

## 2. Instalacija Dockera

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
```

Pokrenuti Docker i uključiti automatsko pokretanje nakon restarta sustava:

```bash
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

Provjera članstva u grupi:

```bash
groups
```

## 3. Kloniranje repozitorija

```bash
git clone git@github.com:HeadshotFTW/ParKING.git
cd ParKING
```

## 4. Build i pokretanje

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
curl -H "Authorization: Bearer <API_TOKEN>" \
  http://localhost:5001/api/parkings
```

API token se ne treba zapisivati u dokumentaciju niti spremati u Git.

## 6. Demo korisnici i standardni demo podaci

Ako je potrebno vratiti samo osnovne razvojne podatke:

```bash
docker compose exec parking python seed.py
```

Demo korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

> `seed.py` briše postojeću razvojnu bazu. Koristiti ga samo kada je namjerno potrebno vratiti početno demo stanje.

Za potpunu demonstraciju koristi se referentni skup podataka iz repozitorija:

```text
demo/parking-demo.json
```

Datoteka `demo/parking-demo.json` namijenjena je držanju u `main` grani kako bi svaki klon repozitorija imao isti pripremljeni demonstracijski skup. U njoj se ne spremaju password hashovi ni API tokeni.

Učitavanje referentnog skupa:

1. Prijaviti se kao `admin / admin123`.
2. Otvoriti **Test → Demo podaci**.
3. U odjeljku **Import** odabrati `demo/parking-demo.json`.
4. Potvrditi import.
5. Nakon importa ponovno se prijaviti po potrebi.

Import zamjenjuje postojeće demonstracijske podatke sadržajem iz JSON datoteke, pa ga treba koristiti namjerno, posebno prije obrane ili testiranja.

Kada se kasnije pripremi bolji demo skup, postojeća datoteka `demo/parking-demo.json` jednostavno se zamijeni novim exportom i ponovno commit-a u `main`.

## 7. Ažuriranje aplikacije

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

## 8. Zaustavljanje i ponovno pokretanje

Zaustavljanje:

```bash
docker compose down
```

Ponovno pokretanje:

```bash
docker compose up -d
```

Potpuni rebuild:

```bash
docker compose up -d --build
```
