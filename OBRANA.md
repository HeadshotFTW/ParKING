# ParKING — plan obrane

Cilj je u kratkom vremenu pokazati stvarni tok aplikacije i pritom pokriti implementirane kriterije.

## Priprema

```bash
git pull --ff-only origin main
docker compose up -d --build
docker compose ps
docker compose exec parking python seed.py
```

Demo korisnici:

```text
vlasnik / parking123
gost     / parking123
admin    / admin123
```

`seed.py` briše postojeću razvojnu bazu, zato ga koristiti samo kada se namjerno želi resetirati stanje. Seed sada kreira četiri parkinga u tri različita grada: Zagreb, Zadar i Split.

## 1. Dostupni parkinzi, vrijeme, rezervacija i povijest pretraga

Prijava kao `gost`.

1. Otvoriti **Dostupni parkinzi**.
2. Zadati lokaciju, termin i po želji maksimalnu cijenu.
3. Pokazati 24-satni unos vremena.
4. Pokrenuti pretragu.
5. Objasniti da se parking skriva samo ako ima preklapajuću `ACTIVE` rezervaciju.
6. Pokazati da kartice parkinga prikazuju trenutačnu temperaturu i vjetar iz Open-Meteo servisa.
7. Pokazati da parkingi u Zagrebu, Zadru i Splitu dobivaju vremenske podatke prema stvarnoj lokaciji.
8. Sortirati rezultate.
9. Otvoriti **Povijest pretraga** i pokazati da je stvarna pretraga automatski spremljena u `data/search_history.bin`.
10. Kliknuti **Ponovi**.
11. Otvoriti parking preko **Detalji** i pokazati da se vremenski podatak prikazuje i na detaljima.
12. Kliknuti **Rezerviraj** i pokazati da je termin već prenesen.
13. Spremiti rezervaciju.
14. Otvoriti **Moje rezervacije**, pokazati trajanje i ukupnu cijenu.
15. Preuzeti PDF potvrdu.

Pravilo preklapanja:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

`CANCELLED` rezervacije ne blokiraju parking.

Za vremenske podatke aplikacija iz tekstualne lokacije izdvaja grad. Zagreb, Samobor i Velika Gorica imaju unaprijed poznate koordinate, a ostali hrvatski gradovi, primjerice Zadar ili Split, automatski se pretvaraju u koordinate preko Open-Meteo Geocoding API-ja (`countryCode=HR`). Ako je na istoj stranici više različitih gradova, vremenski zahtjevi dohvaćaju se paralelno. Više parkinga u istom gradu dijeli jedan rezultat.

### Dokaz vlastitog binarnog formata

```bash
xxd data/search_history.bin | head
```

Na početku se vidi `PKSR`. Aktualna verzija 2 sprema stvarne kriterije pretrage, a `binary_store.py` može čitati i stariju verziju 1.

## 2. HR / EN

Prebaciti HR → EN i otvoriti nekoliko stranica: Dostupni parkinzi, Povijest pretraga, Bilješke, Moje rezervacije i administratorske stranice.

## 3. JSON CRUD + AES-GCM na istoj stranici

Otvoriti **Bilješke**.

Najprije pokazati JSON CRUD:

1. dodati bilješku
2. urediti bilješku
3. obrisati bilješku

Zatim na istoj stranici pokazati AES-GCM:

1. dodati jednu bilješku koja će ostati spremljena
2. kliknuti **Izradi šifriranu kopiju**
3. kliknuti **Otvori šifriranu kopiju**
4. pokazati dešifrirani sadržaj na istoj stranici

Dokaz šifrirane datoteke:

```bash
xxd exports/notes_user_2.aes | head
```

Ako je prijavljen drugi korisnik, broj u nazivu datoteke prilagoditi njegovu `id`-u. Na početku se vidi `PKAE`, a ostatak nije čitljiv tekst.

## 4. BLOB fotografija

Kao `vlasnik` otvoriti **Moji parkinzi**, urediti parking i učitati fotografiju. Pokazati da se fotografija prikazuje na detaljima parkinga te da se može zamijeniti ili ukloniti.

## 5. Admin CRUD + provjera rezervacija kao proces B

Prijava kao `admin`.

Na **Korisnici** pokazati dodavanje ili uređivanje korisnika.

Na **Admin rezervacije**:

1. pokazati CRUD nad rezervacijama
2. kliknuti **Provjeri rezervacije**
3. očekivati poruku da su sve rezervacije ispravne i povratni kod procesa `0`

Za dokaz nenultog koda može se privremeno napraviti preklapajuća `ACTIVE` rezervacija preko administratorskog CRUD-a, ponovno kliknuti **Provjeri rezervacije** i dobiti kod `1`, zatim obrisati testnu rezervaciju.

U kodu pokazati:

```text
run.py                 → subprocess.run(...)
reservation_worker.py  → provjera baze i return code 0/1/2
```

Zasebna stranica **Test → Procesi** više ne postoji; provjera je dio stvarnog administratorskog upravljanja rezervacijama.

## 6. INI postavke

Na **Postavke** promijeniti `default_language` ili `items_per_page` i pokazati `config.ini`.

## 7. Dretve, kritična sekcija i Open-Meteo

Najprije podsjetiti da se Open-Meteo već koristi u stvarnom korisničkom toku na **Dostupni parkinzi** i **Detalji parkinga**.

Zatim kao administrator otvoriti **Test → Dretve**. Stranica više nema statički zadane Zagreb/Samobor/Velika Gorica zadatke. `run.py` čita lokacije stvarnih parkinga iz baze, a `parallel_tasks.py` iz njih izdvaja jedinstvene gradove. Nakon seeda stranica bi trebala prikazati:

```text
Zagreb, Zadar, Split
```

Pokazati:

- gradove pronađene iz stvarnih parkinga
- da se isti gradovi dohvaćaju najprije sekvencijalno pa paralelno
- `ThreadPoolExecutor` s najviše tri radne dretve
- sekvencijalno i paralelno vrijeme
- faktor ubrzanja
- nazive dretvi uz rezultate

Tekstualni blok **Sinkronizacija** namjerno je uklonjen sa stranice. Sinkronizacija i dalje postoji u kodu. Kritična sekcija je dio `fetch_weather()` koji upisuje u zajednički `_request_log`:

```python
with _request_log_lock:
    _request_log.append(...)
```

Lock osigurava da samo jedna dretva u tom trenutku mijenja zajednički zapisnik. Isti Lock koristi se i pri resetiranju i kopiranju zapisnika te za kratke pristupe cacheu geokodiranih gradova.

Time se pokrivaju dretve, sinkronizacija i udaljeni REST servis, a vremenski podaci imaju stvarnu funkciju u ParKING aplikaciji.

## 8. Test → REST

Pokazati da glavni Flask proces na portu `5000` preko HTTP-a poziva vlastiti REST servis na portu `5001`.

Provjera health endpointa:

```bash
curl http://localhost:5001/api/health
```

Bez tokena:

```bash
curl -i http://localhost:5001/api/parkings
```

Očekuje se `401`.

Dokaz da ruta nije registrirana u glavnoj web aplikaciji:

```bash
curl -i http://localhost:5000/api/parkings
```

Očekuje se `404`.

Za autorizaciju pokazati ili objasniti:

- korisnik ne može mijenjati tuđi parking → `403`
- korisnik ne može dohvatiti tuđu rezervaciju → `403`
- administrator ima šire ovlasti

## 9. SHA-256 integritet rezervacije

Kao `gost` otvoriti **Moje rezervacije → SHA-256**.

Pokazati:

- kontrolni otisak stvarnih podataka rezervacije
- promjenjivu sol izvedenu iz `user_id` i `username`
- da se sol ne sprema
- papar iz raspona `0–255`
- provjeru svih 256 mogućih vrijednosti
- uspješnu provjeru trenutačnog otiska
- po želji promijeniti jedan znak u otisku i pokazati neuspješnu provjeru

## Brza REST provjera prije obrane

```bash
docker compose logs --tail=50
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano:

```text
5001 /api/health    → 200
5001 /api/parkings  → 401 bez tokena
5000 /api/parkings  → 404
```

## Datoteke koje je korisno znati

```text
models.py                    SQLAlchemy modeli
app.py                       osnovni CRUD i web rute
run.py                       REST klijent, AES backup, procesna provjera, SHA-256 ruta, gradovi za thread test
parking_availability.py      dostupnost + binarna povijest + vrijeme uz parkinge
binary_store.py              PKSR binarni format
crypto_store.py              AES-GCM
hash_demo.py                 SHA-256 integritet, sol i papar
parallel_tasks.py            Open-Meteo geokodiranje + ThreadPoolExecutor + Lock
reservation_worker.py        zasebni proces B
api_app.py                   vlastiti REST servis na 5001
json_store.py                JSON CRUD
config.ini                   INI postavke
```

## Bodovna procjena

Konzervativna procjena ostaje oko **70 bodova**.
