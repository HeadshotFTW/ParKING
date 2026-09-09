# ParKING — vodič za obranu po kriterijima

Ovaj dokument je namijenjen obrani projekta na grani **`obrana-minimal`**. Za svaki kriterij koji je trenutačno uračunat u procjenu projekta navedeno je:

- što funkcionalnost radi
- koje datoteke otvoriti
- koji dio koda istaknuti
- što pokazati u aplikaciji
- kratka rečenica koju je dovoljno reći na obrani

Trenutačna konzervativna procjena prema `README_IMPLEMENTIRANO.md` je **71 bod**.

## Brzi pregled

| Kriterij | Bodovi | Glavni dokaz |
|---|---:|---|
| 1 | 3 | SQLAlchemy korisničke klase u `models.py` |
| 2 | 4 | više formi + prijenos termina u rezervaciju |
| 3 | 4 | HR/EN sučelje i promjena jezika tijekom rada |
| 4 | 2 | `config.ini` + administratorske postavke |
| 5 | 4 | JSON CRUD vozila |
| 6 | 3 | vlastiti binarni format `PKSR` |
| 7 | 6 | SQLite + SQLAlchemy CRUD |
| 8 | 5 | sortiranje, filtriranje, calculated i lookup polja |
| 9 | 3 | BLOB fotografija parkinga |
| 10 | 5 | PDF potvrda rezervacije |
| 11 | 5 | `ThreadPoolExecutor`, 1 vs 3 dretve |
| 13 | 2 | `threading.Lock` i kritična sekcija |
| 20 | 3 | udaljeni Open-Meteo REST servis |
| 21 | 4 | vlastiti REST servis 5001 + klijent 5000 |
| 22 | 4 | Bearer autentifikacija + autorizacija |
| 23 | 2 | AES-GCM privatne pristupne upute |
| 25 | 7 | SHA-256 + promjenjiva sol + demonstracijski papar |
| 28 | 5 | vlastita C++ dinamička biblioteka `.so` |

---

# Kriterij 1 — korisničke klase — 3 boda

## Funkcionalnost

Aplikacija koristi vlastite klase koje predstavljaju stvarne poslovne objekte sustava:

- `User`
- `ParkingSpot`
- `Reservation`
- `PromoCode`

Sve su definirane kao SQLAlchemy modeli i sadrže podatke i metode vezane uz vlastitu odgovornost.

## Datoteke koje treba pokazati

1. **`models.py`** — glavni dokaz.

## Što istaknuti u kodu

U `models.py` pokaži definicije:

```python
class User(db.Model):
class ParkingSpot(db.Model):
class PromoCode(db.Model):
class Reservation(db.Model):
```

Kod `Reservation` pokaži i metode:

```python
def duration_hours(self):
def base_price(self):
def discount_amount(self):
def total_price(self):
def overlaps(self, start_time, end_time):
```

Time se vidi da klase nisu samo prazni spremnici podataka nego sadrže i logiku.

## Što pokazati u aplikaciji

Dovoljno je pokazati korisnika, parking i rezervaciju u normalnom radu aplikacije.

## Rečenica za obranu

> Glavne poslovne objekte modelirao sam vlastitim klasama `User`, `ParkingSpot`, `Reservation` i `PromoCode`. To su SQLAlchemy modeli, a dio poslovne logike, primjerice izračun cijene rezervacije, nalazi se kao metoda klase.

---

# Kriterij 2 — forme i komunikacija među formama — 4 boda

## Funkcionalnost

Aplikacija ima više od tri forme: prijava, registracija, parking CRUD, rezervacija, vozila, admin korisnici, postavke i promo kodovi.

Najvažniji dokaz komunikacije među formama je prijenos termina iz pretrage parkinga prema detaljima i zatim prema formi rezervacije.

## Datoteke koje treba pokazati

1. **`parking_availability.py`** — čitanje i prosljeđivanje parametara pretrage.
2. **`promo_web.py`** — konačna obrada forme rezervacije.
3. **`app.py`** — ostale forme i CRUD rute.
4. **`templates/parkings.html`**
5. **`templates/reservation_form.html`**

## Što istaknuti u kodu

U `parking_availability.py` pokaži čitanje parametara:

```python
location = request.args.get("location", "").strip()
start_raw = request.args.get("start_time", "").strip()
end_raw = request.args.get("end_time", "").strip()
max_price_raw = request.args.get("max_price", "").strip()
```

Zatim pokaži da se te vrijednosti šalju u template i prenose dalje prema rezervaciji.

U `promo_web.py` pokaži obradu `POST` zahtjeva rezervacije:

```python
if request.method == "POST":
```

te čitanje vremena, vozila i promo koda iz `request.form`.

## Što pokazati u aplikaciji

1. Na **Dostupni parkinzi** unesi termin.
2. Pokreni pretragu.
3. Otvori detalje parkinga.
4. Klikni **Rezerviraj**.
5. Pokaži da je termin prenesen u formu rezervacije.

## Rečenica za obranu

> Aplikacija ima više formi, a komunikaciju među njima demonstriram tako da se termin odabran na pretrazi prenosi kroz detalje parkinga u formu rezervacije, bez ponovnog ručnog unosa.

---

# Kriterij 3 — višejezično sučelje — 4 boda

## Funkcionalnost

Aplikacija podržava hrvatski i engleski jezik, a jezik se može promijeniti tijekom rada.

## Datoteke koje treba pokazati

1. **`translations.py`** — prijevodi.
2. **`app.py`** — `current_language()`, `tr()` i ruta za promjenu jezika.
3. **`templates/base.html`** — HR/EN kontrole u navigaciji.

## Što istaknuti u kodu

U `app.py` pokaži:

```python
def current_language():
```

```python
def tr(key):
```

```python
@app.route("/language/<language>")
def set_language(language):
```

U `translations.py` pokaži da postoji struktura za oba jezika.

## Što pokazati u aplikaciji

1. Otvori neku glavnu stranicu na HR.
2. Klikni **EN**.
3. Pokaži promijenjene oznake bez ponovnog pokretanja aplikacije.
4. Vrati na **HR**.

## Rečenica za obranu

> Jezik čuvam u Flask sessionu, a tekstove dohvaćam preko funkcije `tr()`. Korisnik može tijekom rada prebacivati hrvatski i engleski jezik.

---

# Kriterij 4 — INI postavke — 2 boda

## Funkcionalnost

Aplikacija koristi `config.ini` za postavke:

- zadani jezik
- broj elemenata po stranici

Administrator ih može promijeniti kroz web sučelje.

## Datoteke koje treba pokazati

1. **`config.ini`**
2. **`app.py`**
3. **`templates/admin_settings.html`**

## Što istaknuti u kodu

U `app.py` pokaži:

```python
def load_settings():
```

```python
def save_settings(default_language, items_per_page):
```

te administratorsku rutu:

```python
@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
```

## Što pokazati u aplikaciji

1. Prijavi se kao admin.
2. Otvori **Postavke**.
3. Promijeni `items_per_page` ili zadani jezik.
4. Spremi.
5. Po želji pokaži promjenu i u `config.ini`.

## Rečenica za obranu

> Postavke koje trebaju preživjeti ponovno pokretanje aplikacije čuvam u `config.ini`. Administrator ih mijenja kroz web formu, a aplikacija ih čita pomoću `configparser` modula.

---

# Kriterij 5 — JSON spremanje i CRUD — 4 boda

## Funkcionalnost

**Moja vozila** koriste JSON datoteku umjesto SQL baze. Za svakog korisnika podržani su create, read, update i delete.

Podaci se nalaze u:

```text
data/vehicles.json
```

Vozilo se zatim može odabrati pri rezervaciji parkinga.

## Datoteke koje treba pokazati

1. **`vehicle_store.py`** — glavni dokaz JSON CRUD-a.
2. **`app.py`** — web rute za vozila.
3. **`promo_web.py`** — korištenje vozila pri rezervaciji.
4. **`templates/vehicles.html`**
5. **`templates/vehicle_form.html`**
6. **`data/vehicles.json`** — nakon što kroz UI dodaš barem jedno vozilo.

## Što istaknuti u kodu

U `vehicle_store.py` pokaži:

```python
def _read_all():
def _write_all(vehicles):
def list_vehicles(user_id):
def add_vehicle(user_id, name, registration):
def update_vehicle(user_id, vehicle_id, name, registration):
def delete_vehicle(user_id, vehicle_id):
```

Posebno istakni provjeru `user_id`, jer korisnik smije dohvatiti samo vlastito vozilo.

## Što pokazati u aplikaciji

1. Otvori **Moja vozila**.
2. Dodaj vozilo.
3. Uredi ga.
4. Pokaži `data/vehicles.json`.
5. Otvori rezervaciju i pokaži da je vozilo dostupno u padajućem izborniku.
6. Nakon demonstracije ga po želji obriši.

## Rečenica za obranu

> Vozila namjerno ne spremam u bazu nego u `vehicles.json`. `vehicle_store.py` implementira puni CRUD, a svaki zapis ima `user_id`, pa aplikacija prikazuje samo vozila prijavljenog korisnika.

---

# Kriterij 6 — vlastiti binarni format — 3 boda

## Funkcionalnost

Valjane pretrage parkinga zapisuju se u vlastitu binarnu datoteku:

```text
data/search_history.bin
```

Format ima vlastito zaglavlje `PKSR`, verziju i strukturirane zapise.

## Datoteke koje treba pokazati

1. **`binary_store.py`** — glavni dokaz.
2. **`parking_availability.py`** — mjesto gdje stvarna pretraga stvara zapis.
3. **`run.py`** — ruta za prikaz povijesti.
4. **`templates/binary_history.html`**

## Što istaknuti u kodu

U `binary_store.py` pokaži:

```python
MAGIC = b"PKSR"
VERSION = 2
HEADER = struct.Struct("<4sBI")
```

Zatim:

```python
def read_records(path):
def write_records(path, records):
def add_record(...):
```

Objasni da se tekst pretvara u UTF-8 bajtove, a duljine i numerički podaci zapisuju pomoću `struct`.

## Što pokazati u aplikaciji

1. Kao prijavljeni korisnik napravi stvarnu pretragu parkinga.
2. Kao administrator otvori **Povijest pretraga**.
3. Pokaži spremljeni zapis.
4. Ako te profesor pita format, otvori `binary_store.py` i pokaži `MAGIC`, `VERSION`, `HEADER`, `FIXED_V2`.

## Rečenica za obranu

> Ne koristim pickle ni JSON nego vlastiti binarni format. Datoteka počinje `PKSR` zaglavljem, ima verziju i broj zapisa, a sadržaj pakiram i raspakiravam pomoću modula `struct`.

---

# Kriterij 7 — baza podataka i CRUD — 6 bodova

## Funkcionalnost

Aplikacija koristi SQLite i SQLAlchemy. CRUD postoji nad više poslovnih entiteta:

- korisnici
- parking mjesta
- rezervacije

Dodatno postoji tablica promo kodova.

## Datoteke koje treba pokazati

1. **`models.py`** — tablice i relacije.
2. **`app.py`** — CRUD rute parkinga, korisnika i rezervacija.
3. **`promo_web.py`** — spremanje `PromoCode` zapisa.

## Što istaknuti u kodu

U `models.py` pokaži `db.Column`, primarne ključeve, strane ključeve i `db.relationship`.

U `app.py` pokaži primjer CRUD ruta za jednu cjelinu, primjerice korisnike:

```python
/admin/users
/admin/users/new
/admin/users/<id>/edit
/admin/users/<id>/delete
```

Nije potrebno čitati sav CRUD kod — dovoljno je pokazati obrazac.

## Što pokazati u aplikaciji

Najbrže je kroz **Admin → Korisnici**:

1. Create — dodaj korisnika.
2. Read — pokaži ga na listi.
3. Update — promijeni podatak.
4. Delete — obriši ga.

## Rečenica za obranu

> Baza je SQLite, a pristup podacima radim kroz SQLAlchemy ORM. CRUD imam nad korisnicima, parking mjestima i rezervacijama, s primarnim i stranim ključevima te ORM relacijama.

---

# Kriterij 8 — sortiranje, filtriranje, calculated i lookup polja — 5 bodova

## Funkcionalnost

Na popisu parkinga postoje:

- filter po lokaciji
- filter po maksimalnoj cijeni
- filter po dostupnosti u terminu
- sortiranje po cijeni i nazivu

`Reservation.total_price()` je izračunato polje/logika, a ORM relacije služe kao lookup povezana polja.

## Datoteke koje treba pokazati

1. **`parking_availability.py`** — filteri, dostupnost i sortiranje.
2. **`models.py`** — `total_price()` i relacije.

## Što istaknuti u kodu

U `parking_availability.py` pokaži:

```python
query = query.filter(ParkingSpot.location.ilike(...))
query = query.filter(ParkingSpot.price_per_hour <= max_price)
```

te provjeru preklapanja `ACTIVE` rezervacija:

```text
postojeći početak < traženi završetak
AND
postojeći završetak > traženi početak
```

Pokaži i grananje za sortiranje.

U `models.py` pokaži:

```python
def total_price(self):
```

te lookup relacije:

```python
Reservation.parking
Reservation.user
ParkingSpot.owner
```

## Što pokazati u aplikaciji

1. Filtriraj lokaciju.
2. Postavi maksimalnu cijenu.
3. Postavi termin.
4. Promijeni sortiranje.
5. Otvori rezervaciju s izračunatom konačnom cijenom.

## Rečenica za obranu

> SQLAlchemy query dinamički nadograđujem filterima za lokaciju, cijenu i dostupnost te `order_by` izrazima za sortiranje. Konačna cijena rezervacije računa se metodom `total_price()`, a povezane podatke dohvaćam preko ORM relacija.

---

# Kriterij 9 — BLOB polje — 3 boda

## Funkcionalnost

Fotografija parkinga sprema se direktno u SQLite bazu kao binarni sadržaj.

## Datoteke koje treba pokazati

1. **`models.py`**
2. **`app.py`**
3. **`templates/parking_form.html`**
4. **`templates/parking_detail.html`**

## Što istaknuti u kodu

U `models.py` pokaži:

```python
photo = db.Column(db.LargeBinary, nullable=True)
photo_mime = db.Column(db.String(100), nullable=True)
```

U `app.py` pokaži:

```python
def read_uploaded_image():
```

te rutu koja vraća sadržaj slike:

```python
@app.route("/parking/<int:parking_id>/image")
```

## Što pokazati u aplikaciji

1. Kao vlasnik otvori parking.
2. Učitaj fotografiju.
3. Spremi.
4. Pokaži fotografiju na detaljima.
5. Po želji pokaži zamjenu ili uklanjanje.

## Rečenica za obranu

> Fotografiju ne spremam kao putanju nego kao stvarne bajtove u `LargeBinary` odnosno BLOB polje, a zasebno čuvam MIME tip potreban za HTTP odgovor.

---

# Kriterij 10 — PDF izvještaj — 5 bodova

## Funkcionalnost

Aplikacija generira PDF potvrdu rezervacije koristeći stvarne povezane podatke rezervacije, korisnika i parkinga.

## Datoteke koje treba pokazati

1. **`app.py`** — funkcija `reservation_pdf()`.
2. **`models.py`** — podaci i relacije koji se koriste u PDF-u.

## Što istaknuti u kodu

U `app.py` pronađi:

```python
@app.route("/reservation/<int:reservation_id>/pdf")
```

Pokaži:

```python
buffer = io.BytesIO()
pdf = canvas.Canvas(buffer, pagesize=A4)
```

te listu `rows` u kojoj se kombiniraju podaci rezervacije, korisnika i parkinga.

## Što pokazati u aplikaciji

1. Otvori **Moje rezervacije**.
2. Klikni preuzimanje PDF potvrde.
3. Otvori PDF i pokaži podatke rezervacije.

## Rečenica za obranu

> PDF generiram u memoriji pomoću ReportLaba. Podaci dolaze iz rezervacije i povezanih tablica korisnika i parkinga, nakon čega Flask vraća generirani PDF kao datoteku.

---

# Kriterij 11 — paralelno izvršavanje dretvama — 5 bodova

## Funkcionalnost

Isti Open-Meteo forecast zahtjevi izvršavaju se prvo s jednom, a zatim s najviše tri radne dretve. Mjeri se ukupno vrijeme i računa ubrzanje.

## Datoteke koje treba pokazati

1. **`parallel_tasks.py`** — glavni dokaz multithreadinga.
2. **`run.py`** — ruta `/admin/threads`.
3. **`templates/admin_threads.html`** — prikaz rezultata.

## Što istaknuti u kodu

Najvažnija funkcija:

```python
def run_weather_with_workers(locations, max_workers):
```

Pokaži:

```python
with ThreadPoolExecutor(max_workers=workers, ...) as executor:
    results = list(executor.map(fetch_weather, locations))
```

Zatim u `run_thread_demo()` pokaži dvije izvedbe:

```python
run_weather_with_workers(locations, 1)
run_weather_with_workers(locations, 3)
```

te izračun:

```python
speedup = one_time / multi_time
```

Važno: koordinate se razrješavaju prije mjerenja kako bi obje varijante radile isti posao.

## Što pokazati u aplikaciji

1. Kao admin otvori **Tools → Test Dretve**.
2. Pokaži vrijeme za 1 dretvu.
3. Pokaži vrijeme za 3 dretve.
4. Pokaži faktor ubrzanja.
5. Ako rezultat nije uvjerljiv zbog mreže, osvježi test.

Ranije praktično mjerenje bilo je približno:

```text
1 dretva   0.516 s
3 dretve   0.168 s
ubrzanje   3.07×
```

## Rečenica za obranu

> Isti skup Open-Meteo HTTP zahtjeva izvršavam kroz isti `ThreadPoolExecutor`. Prvo koristim jednog radnika, zatim do tri radnika, mjerim oba vremena i računam faktor ubrzanja.

---

# Kriterij 13 — sinkronizacija dretvi — 2 boda

## Funkcionalnost

Više radnih dretvi zapisuje u zajednički `_request_log`. Taj zajednički resurs zaštićen je `threading.Lock` objektom.

## Datoteke koje treba pokazati

1. **`parallel_tasks.py`**

## Što istaknuti u kodu

Na vrhu:

```python
_request_log = []
_request_log_lock = threading.Lock()
```

U `fetch_weather()` pokaži kritičnu sekciju:

```python
with _request_log_lock:
    _request_log.append(...)
```

Objasni da u tom trenutku samo jedna dretva smije mijenjati zajednički zapisnik.

## Što pokazati u aplikaciji

Na **Test Dretve** pokaži zapisnik i različita imena radnih dretvi ako ih template prikazuje.

## Rečenica za obranu

> `_request_log` je zajednički resurs kojem pristupa više dretvi. Kritičnu sekciju štitim `threading.Lock` objektom tako da samo jedna dretva u danom trenutku mijenja listu.

---

# Kriterij 20 — udaljeni REST servis — 3 boda

## Funkcionalnost

ParKING koristi vanjski Open-Meteo servis za:

- geokodiranje grada
- vremensku prognozu / trenutačne vremenske podatke

Ti podaci nisu samo test nego se prikazuju uz stvarne parkinge.

## Datoteke koje treba pokazati

1. **`parallel_tasks.py`**
2. **`parking_availability.py`**

## Što istaknuti u kodu

U `parallel_tasks.py` pokaži URL-ove:

```text
https://geocoding-api.open-meteo.com/v1/search
https://api.open-meteo.com/v1/forecast
```

Pokaži funkcije za geokodiranje i vremenski dohvat te obradu JSON odgovora.

U `parking_availability.py` pokaži da se rezultat povezuje sa stvarnim parkingima koji se prikazuju korisniku.

## Što pokazati u aplikaciji

Otvori listu ili detalje parkinga i pokaži temperaturu/vjetar za lokaciju parkinga.

## Rečenica za obranu

> Kao udaljeni REST servis koristim Open-Meteo. Prvo po potrebi pretvorim naziv grada u koordinate, a zatim forecast endpointom dohvatim vremenske podatke koje prikazujem uz stvarne parkinge.

---

# Kriterij 21 — vlastiti REST servis i klijent — 4 boda

## Funkcionalnost

Projekt ima dvije odvojene Flask aplikacije/procesa:

```text
run.py      → glavna web aplikacija → port 5000
api_app.py  → vlastiti REST API     → port 5001
```

Glavna aplikacija pomoću biblioteke `requests` šalje HTTP zahtjeve vlastitom REST servisu.

## Datoteke koje treba pokazati

1. **`api_app.py`** — REST servis.
2. **`run.py`** — REST klijent.
3. **`start.sh`** — pokretanje dva procesa.
4. **`Dockerfile`** / **`docker-compose.yml`** — izloženi portovi i pokretanje aplikacije.
5. **`templates/rest_client.html`**

## Što istaknuti u kodu

U `api_app.py` pokaži:

```python
@api_app.route("/api/parkings", methods=["GET", "POST"])
```

```python
@api_app.route("/api/reservations", methods=["GET", "POST"])
```

U `run.py` pokaži:

```python
REST_API_BASE_URL = "http://127.0.0.1:5001"
```

te:

```python
requests.get(...)
```

Bitno je naglasiti da to nije direktan Python poziv funkcije iz `api_app.py`, nego stvarni HTTP zahtjev.

## Što pokazati u aplikaciji

Kao admin otvori **Tools → Test REST**.

Za dodatni tehnički dokaz:

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

## Rečenica za obranu

> Vlastiti REST API je zasebna Flask aplikacija na portu 5001. Glavna web aplikacija na portu 5000 ponaša se kao REST klijent i pomoću `requests` biblioteke šalje stvarne HTTP zahtjeve API procesu.

---

# Kriterij 22 — REST autentifikacija i autorizacija — 4 boda

## Funkcionalnost

REST API koristi Bearer token za autentifikaciju. Nakon autentifikacije provjerava se smije li korisnik obaviti traženu akciju.

## Datoteke koje treba pokazati

1. **`api_app.py`** — gotovo cijeli kriterij.
2. **`models.py`** — `User.api_token` i `User.is_admin()`.
3. **`run.py`** — slanje Bearer tokena iz klijenta.

## Što istaknuti u kodu

U `models.py`:

```python
api_token = db.Column(...)
```

U `api_app.py`:

```python
def api_auth_required(view_func):
```

Pokaži čitanje:

```python
Authorization: Bearer <token>
```

te ishode:

- nema tokena / krivi token → `401`
- token je valjan, ali korisnik nema pravo → `403`

Primjer autorizacije:

```python
if parking.owner_id != user.id and not user.is_admin():
    return ..., 403
```

## Što pokazati u aplikaciji / terminalu

1. Bez tokena pozovi `/api/parkings` → `401`.
2. S valjanim tokenom pokaži uspješan zahtjev.
3. Pokušaj akciju nad tuđim resursom → `403`.

## Rečenica za obranu

> Autentifikacija odgovara na pitanje tko je korisnik i radi preko Bearer tokena. Autorizacija nakon toga provjerava smije li taj korisnik pristupiti ili mijenjati konkretan resurs. Zato razlikujem `401` i `403`.

---

# Kriterij 23 — simetrično šifriranje AES-GCM — 2 boda

## Funkcionalnost

Vlasnik parkinga može spremiti privatne pristupne upute. One se prije zapisa u bazu šifriraju AES-GCM algoritmom.

Primjeri privatnog sadržaja:

- uputa za ulaz
- oznaka parkirnog mjesta
- informacija o dvorištu ili rampi

## Datoteke koje treba pokazati

1. **`parking_access_crypto.py`** — glavni kriptografski dokaz.
2. **`models.py`** — `access_instructions` BLOB.
3. **`app.py`** — šifriranje pri spremanju i dešifriranje pri prikazu.
4. **`templates/parking_form.html`**
5. **`templates/reservations.html`**

## Što istaknuti u kodu

U `parking_access_crypto.py` pokaži:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
```

Novi nonce:

```python
nonce = os.urandom(12)
```

Šifriranje:

```python
AESGCM(key).encrypt(...)
```

Dešifriranje:

```python
AESGCM(key).decrypt(...)
```

Ključ se reproducibilno izvodi iz `SECRET_KEY` i `parking_id`, dok je nonce svaki put nov.

U `models.py` pokaži:

```python
access_instructions = db.Column(db.LargeBinary, nullable=True)
```

## Što pokazati u aplikaciji

1. Kao vlasnik otvori **Moji parkinzi → Uredi**.
2. Upiši privatnu uputu.
3. Spremi.
4. Pokaži da javni detalji parkinga ne prikazuju uputu.
5. Kao korisnik s `ACTIVE` rezervacijom otvori **Moje rezervacije** i pokaži dešifriranu uputu.
6. Objasni da `CANCELLED` rezervacija uputu ne prikazuje.

## Rečenica za obranu

> Privatne pristupne upute šifriram AES-GCM algoritmom prije zapisa u BLOB. Ključ izvodim iz `SECRET_KEY` i ID-a parkinga, a za svako novo šifriranje generiram novi slučajni nonce.

---

# Kriterij 25 — SHA-256, promjenjiva sol i papar — 7 bodova

Ovaj kriterij treba braniti kao **dvije odvojene funkcionalnosti**.

## A) Integritet rezervacije — obični SHA-256

### Funkcionalnost

Aplikacija radi stabilan tekstualni prikaz rezervacije i nad njim računa SHA-256. Ako se promijeni sadržaj rezervacije, mijenja se i hash.

Kod provjere integriteta **nema soli ni papra**.

### Datoteke

1. **`hash_demo.py`**
2. **`run.py`** — ruta `/hash`.
3. **`templates/hash_demo.html`**

### Što istaknuti

U `hash_demo.py`:

```python
def reservation_integrity_text(reservation):
```

Zatim:

```python
hashlib.sha256(text.encode("utf-8")).hexdigest()
```

Pokaži i:

```python
def verify_integrity_hash(...):
```

### Demonstracija

1. Otvori **Moje rezervacije → SHA-256**.
2. Pokaži kontrolni tekst i hash.
3. Napravi uspješnu provjeru.
4. Promijeni jedan znak kontrolnog hasha i pokaži neuspješnu provjeru.

### Rečenica

> Za integritet rezervacije koristim čisti SHA-256 bez soli i papra, jer želim da isti sadržaj uvijek daje isti kontrolni otisak.

## B) Promo kod POPUST — promjenjiva sol i papar

### Funkcionalnost

Jedini promo kod je:

```text
POPUST
```

Svaki korisnik ima svoju sol izvedenu pravilom iz `user_id`:

```text
SHA256("ParKING-user-promo-salt:<user_id>")[0:16]
```

Sol se ne sprema u bazu ni datoteku.

Sistemski papar dolazi iz:

```text
PROMO_SYSTEM_PEPPER
```

Za demonstraciju je namjerno ograničen na raspon `1-5`; zadana Docker vrijednost je `3`.

Admin svakom korisniku može dodijeliti drugi postotak popusta. Hash nastaje iz:

```text
korisnikova sol + "POPUST" + papar
                ↓
             SHA-256
```

Kod rezervacije korisnik u DEMO dropdownu pogađa papar. Backend prolazi **svih pet vrijednosti 1-5** kako bi pronašao koja odgovara spremljenom hash-u, ali popust prihvaća samo ako korisnikov odabir odgovara pronađenoj vrijednosti.

### Datoteke koje treba pokazati

1. **`promo_code_hash.py`** — sol, papar i SHA-256.
2. **`promo_web.py`** — dodjela popusta i provjera pri rezervaciji.
3. **`models.py`** — `PromoCode` i polja rezervacije.
4. **`templates/admin_promos.html`**
5. **`templates/reservation_form.html`**
6. **`docker-compose.yml`** — `PROMO_SYSTEM_PEPPER`.

### Što istaknuti u kodu

U `promo_code_hash.py` pokaži:

```python
PROMO_CODE = "POPUST"
PEPPER_MIN = 1
PEPPER_MAX = 5
```

Pokaži funkciju izvođenja soli i funkciju koja računa digest.

Najvažniji dokaz provjere papra je petlja:

```python
for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
```

Time se vidi da se provjerava cijeli demonstracijski raspon.

### Demonstracija

1. Kao admin otvori **Promo kodovi**.
2. Dodijeli npr. `gost` → 10%.
3. Drugom korisniku dodijeli drugi postotak.
4. Klikni **Primijeni** i pokaži različite hash vrijednosti.
5. Prijavi se kao korisnik kojem je dodijeljen popust.
6. Kod rezervacije upiši `POPUST`.
7. Namjerno izaberi krivi papar, npr. `1` → odbijeno.
8. Pokušaj dalje dok ne pogodiš ispravnu vrijednost; uz zadanu konfiguraciju to je `3`.
9. Pokaži da se primijenio upravo korisnikov postotak popusta.

### Rečenica za obranu

> Promo kod koristi SHA-256 s korisničkom promjenjivom soli koju ne spremam nego je ponovno izvodim iz `user_id`. Papar je sistemska vrijednost. Za demonstraciju je raspon 1-5 i backend namjerno provjerava cijeli raspon, dok se popust daje samo ako korisnik pogodi ispravnu vrijednost.

### Važno upozorenje na obrani

Obavezno reci:

> Dropdown papra postoji isključivo za demonstraciju kriterija. U stvarnom produkcijskom sustavu tajni papar se ne bi prikazivao korisniku niti bi ga korisnik pogađao.

---

# Kriterij 28 — dinamička C++ biblioteka — 5 bodova

## Funkcionalnost

Service fee rezervacije računa se u vlastitoj C++ dinamičkoj biblioteci.

Docker build iz izvornog C++ koda stvara:

```text
/app/native/libservice_fee.so
```

Python zatim biblioteku učitava pomoću `ctypes`.

## Datoteke koje treba pokazati

1. **`native/service_fee.cpp`** — vlastita C++ klasa.
2. **`service_fee.py`** — `ctypes` wrapper.
3. **`Dockerfile`** — kompajliranje `.so` biblioteke.
4. **`run.py`** — funkcije izložene Jinja templateima.
5. **`templates/admin_reservations.html`** — stvarni prikaz service fee izračuna.

## Što istaknuti u kodu

U `native/service_fee.cpp` pokaži:

```cpp
class ServiceFeeCalculator
```

metode:

```cpp
calculateFee(...)
calculateTotalFees(...)
```

te `extern "C"` funkcije koje omogućuju jednostavan poziv iz Pythona.

U `service_fee.py` pokaži:

```python
_library = ctypes.CDLL(str(LIBRARY_PATH))
```

te deklariranje argumenata i povratnih tipova.

## Što pokazati u aplikaciji

Kao admin otvori **Admin rezervacije** i pokaži:

- service fee pojedine `ACTIVE` rezervacije
- ukupan service fee

Za tehničku provjeru:

```bash
docker compose exec parking python -c "import service_fee; print(service_fee.native_library_loaded(), service_fee.LIBRARY_PATH)"
```

Očekivano:

```text
True /app/native/libservice_fee.so
```

## Rečenica za obranu

> Izračun service fee naknade implementiran je u vlastitoj C++ klasi. Docker je kompajlira u dinamičku `.so` biblioteku, a Python je učitava pomoću `ctypes` i poziva C funkcije koje delegiraju rad klasi `ServiceFeeCalculator`.

---

# Dodatna funkcionalnost — korisnički avatar preko vanjskog `wget` programa

Ova funkcionalnost je dodana nakon ranije bodovne procjene od 71 boda. Trenutačni `README_IMPLEMENTIRANO.md` je još ne računa kao zaseban kriterij, zato prije konačne prijave provjeri odgovara li to točno službenom kriteriju 17 u prijavnici.

## Funkcionalnost

ParKING container sadrži pravi izvršni program `wget`. Python ga pokreće preko `subprocess.run()` i njime dohvaća korisnički avatar s Pravatar servisa.

## Datoteke koje treba pokazati

1. **`Dockerfile`** — instalacija `wget`.
2. **`avatar_fetch.py`** — `subprocess.run()` i Pravatar URL.
3. **`avatar_web.py`** — web rute profila/avatara.
4. **`templates/profile.html`**
5. **`templates/base.html`** — prikaz avatara u navigaciji.

## Što istaknuti

U `avatar_fetch.py` pokaži da se ne koristi Python HTTP biblioteka za samo preuzimanje slike, nego vanjska izvršna aplikacija:

```python
subprocess.run([
    "wget",
    ...
])
```

Pravatar URL aplikacija sama konstruira; korisnik ne može zadati proizvoljan URL.

## Demonstracija

1. Otvori **Profil**.
2. Klikni **Dohvati novi avatar**.
3. Pokaži da se avatar promijenio.
4. U terminalu pokaži:

```bash
docker compose exec parking which wget
docker compose exec parking wget --version
```

## Rečenica za obranu

> Python ne preuzima avatar sam, nego pokreće zasebnu izvršnu aplikaciju `wget` pomoću `subprocess.run()`. `wget` je instaliran u istom Docker containeru i dohvaća sliku s Pravatar servisa.

---

# Kriteriji koje ne prijavljujemo

Prema trenutačnoj konzervativnoj procjeni ne računaju se:

```text
12, 14, 15, 16, 17, 18, 19, 24, 26, 27, 29, 30
```

Napomena za **17**: projekt sada ima `wget`/Pravatar funkcionalnost, ali ona još nije unesena u postojeći bodovni dokument. Ako službeni opis kriterija 17 odgovara toj implementaciji, ažurirati ovaj popis i ukupan broj bodova prije predaje.

Kriterij 14 se namjerno ne demonstrira jer je ranija Python procesna demonstracija uklonjena nakon pojašnjenja nastavnika da očekuje procese A i B kao izvršne aplikacije.

---

# Preporučeni redoslijed obrane

Ako želiš obranu odraditi što jednostavnije, idi ovim redom:

1. **Dostupni parkinzi** — forme, filteri, sortiranje, Open-Meteo.
2. **Moja vozila** — JSON CRUD.
3. **Rezervacija** — prijenos termina, vozilo, cijena.
4. **PDF potvrda**.
5. **Moji parkinzi** — BLOB fotografija i AES-GCM pristupne upute.
6. **HR / EN**.
7. **Admin → Postavke** — INI.
8. **Admin → Korisnici** — SQL CRUD i klase.
9. **Promo kodovi + rezervacija** — SHA-256, sol i papar.
10. **Tools → Test Dretve** — `ThreadPoolExecutor` + `Lock`.
11. **Tools → Test REST** — vlastiti REST + Bearer auth.
12. **Admin rezervacije** — dinamička C++ biblioteka.
13. **Povijest pretraga** — vlastiti binarni format.
14. **Profil** — `wget` + Pravatar, ako taj kriterij prijavljuješ.

---

# Minimalni skup datoteka koje treba znati otvoriti

Ako profesor traži kod, najvažnije je znati gdje je što:

```text
models.py                    klase, baza, relacije, calculated polja, BLOB
app.py                       osnovne Flask rute, CRUD, PDF, INI, AES korištenje
run.py                       dodatne rute: REST klijent, dretve, SHA-256
parking_availability.py      filteri, dostupnost, Open-Meteo povezivanje, binary history zapis
vehicle_store.py             JSON CRUD
binary_store.py              vlastiti PKSR binarni format
parallel_tasks.py            Open-Meteo, ThreadPoolExecutor, Lock
api_app.py                   vlastiti REST API, Bearer auth/authz
parking_access_crypto.py     AES-GCM
hash_demo.py                 SHA-256 integritet rezervacije
promo_code_hash.py           korisnička sol + papar + SHA-256
promo_web.py                 promo administracija i rezervacija
service_fee.py               ctypes učitavanje dinamičke biblioteke
native/service_fee.cpp       vlastita C++ klasa
avatar_fetch.py              subprocess + wget + Pravatar
avatar_web.py                profil i avatar rute
Dockerfile                   wget + build libservice_fee.so
start.sh                     web proces 5000 + REST proces 5001
config.ini                   INI postavke
translations.py              HR/EN prijevodi
```

# Najvažnije stvari koje ne smiješ zamijeniti na obrani

- `requests` šalje HTTP zahtjev; Flaskov `request` predstavlja zahtjev koji je stigao aplikaciji.
- Glavna aplikacija je na **5000**, vlastiti REST API na **5001**.
- `401` znači da autentifikacija nije uspjela; `403` znači da je korisnik poznat, ali nema pravo na akciju.
- Dretve se stvaraju preko `ThreadPoolExecutor`; `Lock` služi za sinkronizaciju pristupa zajedničkom resursu.
- JSON vozila nisu u SQLite bazi.
- BLOB fotografija parkinga jest u SQLite bazi.
- AES-GCM koristi se za privatne pristupne upute parkinga.
- SHA-256 integritet rezervacije ne koristi sol ni papar.
- Sol i papar koriste se zasebno za promo kod `POPUST`.
- Promo demo provjerava papar **1-5**, ne 0-255.
- Dinamička biblioteka je `.so` koju Python učitava preko `ctypes`.
- `wget` je vanjska izvršna aplikacija koju Python pokreće preko `subprocess.run()`.
