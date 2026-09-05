# ParKING — plan obrane

Cilj obrane je u kratkom vremenu pokazati funkcionalnosti koje nose bodove, bez nepotrebnog lutanja kroz aplikaciju.

## Priprema prije obrane

```bash
git pull
docker compose up -d --build
docker compose ps
```

### Učitavanje standardnog demo skupa

Za obranu se preporučuje koristiti referentni skup podataka iz repozitorija:

```text
demo/parking-demo.json
```

Postupak:

1. Prijaviti se kao `admin / admin123`.
2. Otvoriti **Test → Demo podaci**.
3. U odjeljku **Import** odabrati `demo/parking-demo.json`.
4. Potvrditi import.
5. Provjeriti da su učitani očekivani korisnici, parkinzi, rezervacije, bilješke, fotografije i binarna povijest.

Referentni JSON ne sadrži password hashove ni API tokene. Nakon importa aplikacija korisnicima postavlja demonstracijske lozinke prema ulozi.

Ako referentni dataset još nije finaliziran, može se privremeno koristiti `seed.py`:

```bash
docker compose exec parking python seed.py
```

Demo korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

> `seed.py` briše postojeću razvojnu bazu. Pokretati ga samo ako je potrebno vratiti osnovno demo stanje. Za samu obranu prednost ima `demo/parking-demo.json`, jer može sadržavati potpuniji i unaprijed provjeren demonstracijski skup.

## Brza provjera odvojenog REST servisa

ParKING u istom Docker containeru pokreće dvije zasebne Flask aplikacije kao dva odvojena procesa:

```text
run.py      → glavna web aplikacija → port 5000
api_app.py  → REST API              → port 5001
```

Nakon pokretanja provjeriti logove:

```bash
docker compose logs --tail=50
```

U logovima se trebaju vidjeti dvije Flask aplikacije, jedna na portu `5000`, a druga na `5001`.

Provjera REST health endpointa:

```bash
curl http://localhost:5001/api/health
```

Očekivani rezultat:

```json
{"port":5001,"service":"ParKING REST API","status":"ok"}
```

Provjera autentifikacije na REST aplikaciji:

```bash
curl -i http://localhost:5001/api/parkings
```

Očekuje se HTTP `401 UNAUTHORIZED` i poruka:

```json
{"error":"Nedostaje Bearer token."}
```

Provjera da REST više nije dio glavne web aplikacije:

```bash
curl -i http://localhost:5000/api/parkings
```

Očekuje se HTTP `404 NOT FOUND`. Time se jasno pokazuje da glavna aplikacija na portu `5000` nema REST rutu, nego REST servis radi kao zasebna aplikacija/proces na portu `5001`.

## Preporučeni redoslijed demonstracije

### 1. Osnovna aplikacija

1. Prijava kao `gost`.
2. Prikaz popisa parkinga.
3. Filtriranje po lokaciji i sortiranje po cijeni.
4. Otvaranje parkinga i rezervacija termina.
5. Prikaz `Moje rezervacije` i izračunate ukupne cijene.
6. Preuzimanje PDF potvrde rezervacije.

Pokazuje: forme/dijalozi, SQLite, povezane tablice, filtriranje, sortiranje, izračunato polje, lookup relacije i PDF master-detail izvještaj.

### 2. HR / EN

Prebaciti aplikaciju s HR na EN i otvoriti nekoliko stranica, uključujući tehničke stranice iz izbornika **Test**.

Pokazuje: promjena jezika tijekom rada i više od pet prevedenih stranica.

### 3. Administratorski CRUD i INI

Prijava kao `admin`.

1. `Users` — dodavanje ili uređivanje korisnika.
2. `Admin reservations` — pregled/uređivanje rezervacija.
3. `Settings` — promjena `default_language` ili `items_per_page`.

Pokazuje: CRUD nad tri SQL tablice i čitanje/pisanje INI postavki.

### 4. JSON CRUD

Otvoriti `Bilješke / Notes`.

1. Dodati bilješku.
2. Urediti je.
3. Obrisati je.

Datoteka: `data/parking_notes.json`.

### 5. BLOB

Otvoriti vlastiti parking i demonstrirati fotografiju spremljenu izravno u SQLite BLOB polje. Po potrebi pokazati zamjenu ili uklanjanje fotografije.

### 6. Test → Dretve

Kao administrator otvoriti **Test → Dretve**.

Pokazati:

- tri HTTP poziva Open-Meteo servisu,
- `ThreadPoolExecutor(max_workers=3)`,
- sekvencijalno i paralelno vrijeme,
- faktor ubrzanja,
- nazive radnih dretvi,
- `threading.Lock` za zajednički zapisnik.

Pokazuje: thread pool, sinkronizaciju i udaljeni REST servis.

### 7. Test → Procesi

1. Kliknuti **Provjeri rezervacije** — očekuje se povratni kod `0` ako su podaci ispravni.
2. Kliknuti **Simuliraj grešku procesa B** — očekuje se kod `2` i poruka o tehničkoj grešci.

U kodu pokazati `subprocess.run(...)` u `run.py` i izlazne kodove u `reservation_worker.py`.

### 8. Test → REST

Pokazati da ugrađeni REST klijent iz glavne aplikacije na portu `5000` preko HTTP-a poziva zasebnu REST aplikaciju na portu `5001` i dobiva HTTP `200` za:

```text
GET /api/parkings
GET /api/reservations
```

Za autentifikaciju bez tokena koristiti:

```bash
curl -i http://localhost:5001/api/parkings
```

Očekuje se HTTP `401`.

Za dokaz da REST nije registriran u glavnoj aplikaciji:

```bash
curl -i http://localhost:5000/api/parkings
```

Očekuje se HTTP `404`.

Za autorizaciju objasniti:

- korisnik vidi svoje rezervacije,
- samo vlasnik parkinga ili admin može mijenjati parking,
- admin ima širi pristup rezervacijama.

### 9. Test → Binarno

Dodati nekoliko zapisa pretrage, zatim pokazati da se ponovno čitaju iz `data/search_history.bin`.

Dokaz formata:

```bash
xxd data/search_history.bin | head
```

Na početku mora biti zaglavlje `PKSR`, a datoteka mora sadržavati više binarnih zapisa.

### 10. Test → AES

1. **Šifriraj moje bilješke**.
2. **Dešifriraj sigurnosnu kopiju**.
3. Pokazati da su vraćene izvorne bilješke.

Dokaz šifriranog sadržaja:

```bash
xxd exports/notes_user_3.aes | head
```

Na početku se vidi `PKAE`, a ostatak sadržaja nije čitljiv tekst.

### 11. Test → SHA-256

Unijeti primjer teksta i kliknuti **Izračunaj i provjeri**.

Pokazati:

- SHA-256,
- promjenjivu sol izvedenu pravilom iz `user_id` i `username`, bez spremanja soli,
- papar iz raspona `0–255`,
- provjeru svih `256` mogućih vrijednosti,
- pronađenu vrijednost papra.

## Bodovna procjena

Trenutna konzervativna procjena je oko **70 bodova**.

Za vlastiti REST servis računa se 4 boda jer nije posebno postavljen na IIS/Apache poslužitelj; autentifikacija i autorizacija računaju se zasebno.

## Datoteke koje je korisno znati pokazati

```text
models.py                 SQLAlchemy modeli
app.py                    osnovne rute glavne web aplikacije
run.py                    tehničke demonstracije, REST klijent i proces A
api_app.py                zasebna REST Flask aplikacija na portu 5001
start.sh                  pokretanje web i REST procesa u containeru
parallel_tasks.py         ThreadPoolExecutor + Lock + Open-Meteo
reservation_worker.py     proces B i izlazni kodovi
binary_store.py           prilagođeni binarni format
crypto_store.py           AES-GCM
hash_demo.py              SHA-256, promjenjiva sol i papar
json_store.py             JSON CRUD
config.ini                INI postavke
demo/parking-demo.json    referentni skup podataka za obranu
```

## Pravilo za samu obranu

Za svaki kriterij prvo pokazati rezultat u aplikaciji, a tek zatim 10–20 sekundi relevantnog koda. Ne otvarati cijele datoteke ako nije potrebno; pokazati samo funkciju ili dio koji izravno dokazuje kriterij.
