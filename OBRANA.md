# ParKING — plan obrane

Cilj je pokazati samo funkcionalnosti koje možemo jasno objasniti i demonstrirati.

## Priprema

```bash
git pull --ff-only origin main
docker compose up -d --build
docker compose ps
docker compose exec parking python seed.py
```

`seed.py` briše postojeću razvojnu bazu i kreira parkinge u Zagrebu, Zadru i Splitu.

## 1. Dostupni parkinzi, vrijeme i rezervacija

Kao obični korisnik:

1. otvoriti **Dostupni parkinzi**
2. zadati lokaciju, termin i maksimalnu cijenu
3. pokazati 24-satni unos vremena
4. pokrenuti pretragu
5. objasniti provjeru preklapanja `ACTIVE` rezervacija
6. pokazati Open-Meteo temperaturu i vjetar
7. sortirati rezultate
8. otvoriti **Moja vozila** i imati barem jedno spremljeno vozilo
9. rezervirati parking, pokazati preneseni termin i odabrati jedno od svojih vozila
10. otvoriti **Moje rezervacije** i pokazati odabrano vozilo uz rezervaciju
11. preuzeti PDF potvrdu

Pravilo preklapanja:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

**Povijest pretraga** demonstrira se kao administrator jer je pristup toj stranici ograničen na admin korisnike.

## 2. HR / EN

Prebaciti HR → EN i otvoriti nekoliko glavnih stranica.

## 3. JSON CRUD — Moja vozila

Otvoriti **Moja vozila** i pokazati puni CRUD:

1. dodati vozilo
2. prikazati ga na listi
3. urediti naziv ili registraciju
4. po završetku demonstracije po želji obrisati vozilo

Za tehnički dokaz pokazati:

```bash
cat data/vehicles.json
```

Objasniti da `vehicle_store.py` sprema `id`, `user_id`, naziv vozila i registracijsku oznaku u JSON, bez baze podataka.

Kod normalne rezervacije padajući izbornik prikazuje samo vozila prijavljenog korisnika. Ako korisnik odabere vozilo, aplikacija provjerava vlasništvo nad tim JSON zapisom i u rezervaciju sprema snapshot ID-a, naziva i registracije. Zato stara rezervacija ostaje razumljiva čak i ako se vozilo kasnije izmijeni ili obriše iz `vehicles.json`.

## 4. AES-GCM — privatne pristupne upute parkinga

Kao vlasnik otvoriti **Moji parkinzi → Uredi** i u polje **Privatne pristupne upute** upisati primjerice:

```text
Ulaz je iz dvorišta. Parkirno mjesto je označeno brojem 12.
```

Spremiti parking. Objasniti:

- aplikacija prije spremanja poziva `encrypt_access_instructions()`
- koristi se AES-GCM
- za svako šifriranje generira se novi slučajni nonce
- u `parking_spots.access_instructions` sprema se samo binarni šifrirani sadržaj
- ključ se izvodi iz `SECRET_KEY` i `parking_id`

Javni **Detalji parkinga** ne prikazuju privatne upute.

Zatim kao korisnik s `ACTIVE` rezervacijom otvoriti **Moje rezervacije**. U stupcu **Pristupne upute** prikazuje se dešifrirani tekst. Za `CANCELLED` rezervacije prikazuje se `—`.

Za dokaz da se u bazi ne nalazi čitljiv tekst može se izvršiti:

```bash
docker compose exec parking python -c "from app import app; from models import ParkingSpot; app.app_context().push(); p=ParkingSpot.query.filter(ParkingSpot.access_instructions.isnot(None)).first(); print(p.access_instructions.hex() if p else 'nema uputa')"
```

Važno za objašnjenje: AES-GCM ovdje štiti stvaran privatni podatak parkinga.

## 5. Promo kod POPUST — SHA-256, promjenjiva sol i DEMO papar

Kao administrator otvoriti **Promo kodovi**. Na stranici postoji samo jedan promo kod:

```text
POPUST
```

U tablici su svi korisnici. Za dva različita korisnika označiti checkbox i postaviti različite popuste, primjerice:

```text
gost      10%
vlasnik   20%
```

Kliknuti **Primijeni**. Za svakog označenog korisnika sprema se različit SHA-256 sažetak, iako je tekst promo koda isti.

Objasniti da svaki korisnik ima vlastitu promjenjivu sol izvedenu pravilom iz stabilnog `user_id`:

```text
SHA256("ParKING-user-promo-salt:<user_id>")[0:16]
```

Sol se ne sprema u bazu ni datoteku. Time je svaki korisnik dobio vlastitu reproducibilnu sol čim postoji njegov `user_id`.

Papar je definiran na razini sustava preko varijable:

```text
PROMO_SYSTEM_PEPPER
```

Za demonstraciju je raspon namjerno ograničen na vrijednosti `1-5`; zadana Docker vrijednost je `3`. Papar se ne sprema uz korisnički hash.

Hash korisnika računa se nad:

```text
korisnikova sol + "POPUST" + sistemski papar
                  ↓
               SHA-256
```

Zatim se prijaviti kao korisnik kojem je admin dodijelio popust i otvoriti rezervaciju. Uz unos promo koda nalazi se jasno označen **Papar — DEMO** dropdown s vrijednostima `1-5`.

Demonstracija:

1. upisati `POPUST`
2. namjerno odabrati pogrešan papar, npr. `1` — popust se ne prihvaća
3. pokušati ponovno s drugom vrijednošću
4. kad se pogodi ispravan papar, popust se prihvaća i primjenjuje baš postotak dodijeljen tom korisniku

Backend pri svakoj provjeri prolazi cijeli demonstracijski raspon `1-5` i pronalazi vrijednost koja daje spremljeni hash, ali popust daje samo ako korisnikov odabir odgovara toj vrijednosti. Time se istodobno demonstrira provjera cijelog raspona i pogađanje papra.

**Važno za obranu:** dropdown papra postoji isključivo u demonstracijske svrhe. U stvarnoj produkcijskoj aplikaciji tajni papar se ne bi prikazivao korisniku niti bi ga korisnik pogađao.

Za drugog korisnika isti tekst `POPUST` daje drugi hash i može dati drugi postotak popusta.

Ključne datoteke:

```text
promo_code_hash.py     sol po user_id-u, sistemski papar i puni scan 1-5
promo_web.py           checkbox dodjela popusta + provjera korisničkog DEMO odabira
templates/reservation_form.html   DEMO dropdown za papar 1-5
models.py              PromoCode.user_id + discount_percent + hash po korisniku
docker-compose.yml     PROMO_SYSTEM_PEPPER na razini sustava
```

Važno: ovo je zasebno od provjere integriteta rezervacije. Kod integriteta nema soli ni papra.

## 6. BLOB fotografija

Kao vlasnik urediti parking i učitati fotografiju. Pokazati prikaz, zamjenu i uklanjanje slike.

## 7. Admin CRUD + dinamička biblioteka

Kao administrator na **Korisnici** pokazati CRUD. Na **Admin rezervacije** pokazati:

1. CRUD nad rezervacijama
2. stupac **Service fee (5%)**
3. karticu **Ukupan service fee (5%)**
4. da izračun dolazi iz vlastite C++ dinamičke biblioteke

Provjera biblioteke:

```bash
docker compose exec parking python -c "import service_fee; print(service_fee.native_library_loaded(), service_fee.LIBRARY_PATH)"
```

Očekuje se `True` i `/app/native/libservice_fee.so`.

## 8. INI postavke

Na **Postavke** promijeniti `default_language` ili `items_per_page` i pokazati `config.ini`.

## 9. Dretve, ubrzanje, kritična sekcija i Open-Meteo

Kao administrator otvoriti **Tools → Test Dretve**. Koordinate gradova razriješe se prije mjerenja, a potpuno isti Open-Meteo forecast zahtjevi izvršavaju se kroz isti `ThreadPoolExecutor`:

```text
max_workers = 1
max_workers = 3
```

Zadnji praktični test:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

Na obrani ponovno pokazati da je varijanta s tri dretve brža. Brojke mogu varirati zbog mrežne latencije.

Kritična sekcija:

```python
with _request_log_lock:
    _request_log.append(...)
```

`threading.Lock` štiti zajednički `_request_log`.

## 10. Tools → Test REST

Pokazati odvojeni web proces na `5000` i vlastiti REST servis na `5001`:

```bash
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

Za kriterij 22 treba pokazati i stvarni `403` za nedopuštenu akciju.

## 11. SHA-256 integritet rezervacije

Otvoriti **Moje rezervacije → SHA-256**.

Objasniti da se koristi **obični SHA-256 bez soli i papra**, jer je svrha provjera integriteta. U kontrolni tekst ulaze i snapshot odabranog vozila te eventualni promo popust. Pokazati trenutačni kontrolni otisak, uspješnu provjeru te po želji neuspješnu provjeru nakon promjene jednog znaka otiska.

## Kriterij 14 — ne demonstrirati

Ranija Python procesna demonstracija je uklonjena. Nastavnik očekuje procese A i B kao izvršne EXE aplikacije, pa kriterij 14 ne prijavljujemo.

## Datoteke koje je korisno znati

```text
models.py                    SQLAlchemy modeli + korisnički PromoCode zapis
app.py                       web rute, CRUD, vozila, AES pristupne upute
run.py                       instalira prošireni rezervacijski tok
vehicle_store.py             JSON CRUD vozila
parking_access_crypto.py     AES-GCM šifriranje/dešifriranje pristupnih uputa
hash_demo.py                 SHA-256 integritet rezervacije
promo_code_hash.py           sol po user_id-u + sistemski papar + provjera 1-5
promo_web.py                 POPUST po korisniku + DEMO pogađanje papra + rezervacija
parking_availability.py      dostupnost + binarna povijest + vrijeme
binary_store.py              PKSR binarni format
parallel_tasks.py            Open-Meteo + ThreadPoolExecutor + Lock
service_fee.py               ctypes wrapper za dinamičku biblioteku
native/service_fee.cpp       C++ ServiceFeeCalculator
api_app.py                   vlastiti REST servis na 5001; podržava opcionalni vehicle_id
docker-compose.yml           SECRET_KEY + PROMO_SYSTEM_PEPPER
config.ini                   INI postavke
```

## Bodovna procjena

Konzervativna procjena je oko **71 bod**. Kriterij 11 je praktično potvrdio ubrzanje. Kriterij 14 je uklonjen. Kriterij 25 ima čistu provjeru integriteta bez soli/papra te zasebnu demonstraciju promjenjive korisničke soli i sistemskog papra na promo kodu `POPUST`.
