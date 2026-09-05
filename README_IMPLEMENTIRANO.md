# ParKING — implementirane funkcionalnosti

Ovaj dokument izdvaja samo funkcionalnosti koje su implementirane i navedene u popunjenoj prijavnici. Neimplementirani kriteriji namjerno nisu navedeni.

**Procijenjeni zbroj: 70 bodova.**

## 1. Korisničke klase — 3 boda

Implementirane su tri korisničke klase: User, ParkingSpot i Reservation.

User: atributi id, username, password_hash, role; metode set_password(), check_password(), is_admin().
ParkingSpot: atributi id, owner_id, name, location, price_per_hour, description; metode display_price(), is_owned_by().
Reservation: atributi id, parking_id, user_id, start_time, end_time, status; metode duration_hours(), total_price(), overlaps().
Klase se koriste kroz SQLAlchemy modele i poslovnu logiku aplikacije.

## 2. Forme i komunikacija među formama — 4 boda

Aplikacija sadrži više od tri web forme/dijaloga: prijava, registracija, popis parkinga, dodavanje/uređivanje parkinga, detalji parkinga, rezervacija, moje rezervacije te administratorske forme za korisnike i rezervacije.

Komunikacija među formama demonstrira se npr. odabirom parkinga na popisu ili detaljima, čime se njegov parking_id prenosi na formu za rezervaciju; nakon spremanja korisnik se preusmjerava na pregled svojih rezervacija.

## 3. Višejezično sučelje — 4 boda

Aplikacija podržava hrvatsko i englesko korisničko sučelje. Jezik se može promijeniti tijekom rada aplikacije pomoću HR/EN poveznica u navigaciji bez izlaska iz aplikacije.

Prevedeno je više od 5 dijaloga/stranica: prijava, registracija, popis parkinga, moji parkinzi, forma za dodavanje/uređivanje parkinga, detalji parkinga, forma rezervacije, moje rezervacije, JSON bilješke i INI postavke.

## 4. INI postavke — 2 boda

Postavke aplikacije spremaju se i učitavaju iz INI datoteke config.ini pomoću Python modula configparser.

Spremaju se najmanje dvije postavke: default_language (zadani jezik HR/EN) i items_per_page (broj parkinga prikazanih po stranici). Administrator ih može mijenjati kroz stranicu Postavke, a promjene se zapisuju natrag u config.ini.

## 5. JSON spremanje i CRUD — 4 boda

Aplikacija koristi JSON datoteku data/parking_notes.json za niz korisničkih bilješki. Svaki zapis sadrži id, user_id, title i text.

Podržane su sve CRUD operacije: čitanje popisa i pojedine bilješke, dodavanje nove bilješke, uređivanje naslova/teksta te brisanje bilješke. Operacije su implementirane u modulu json_store.py i dostupne kroz web sučelje Bilješke.

## 6. Prilagođeni binarni format — 3 boda

Aplikacija koristi vlastiti binarni format datoteke data/search_history.bin za pohranu niza zapisa povijesti pretraga. Datoteka ima vlastito zaglavlje PKSR, verziju formata i broj zapisa. Svaki binarni zapis sadrži user_id, vrijeme zapisa, maksimalnu cijenu i lokaciju promjenjive duljine. Implementirane su funkcije za zapis cijelog niza u binarnu datoteku i ponovno čitanje zapisa iz tog formata. Binarni sadržaj demonstriran je alatom xxd, pri čemu se vidi zaglavlje PKSR i strukturirani binarni podaci, a ne tekstualni zapis.

## 7. Baza podataka i CRUD — 6 bodova

Aplikacija koristi SQLite bazu podataka preko SQLAlchemy ORM-a. Baza služi za trajnu pohranu korisnika, parkirnih mjesta i rezervacija.

Tablice: users, parking_spots i reservations. Nad sve tri tablice demonstriraju se operacije čitanja, dodavanja, uređivanja i brisanja. Korisnik upravlja vlastitim parkirnim mjestima i rezervacijama, a administrator kroz administratorsko sučelje upravlja korisnicima i rezervacijama.

## 8. Sortiranje, filtriranje, izračunato i lookup polje — 5 bodova

Sortiranje i filtriranje provodi se nad zapisima tablice parking_spots. Parkirna mjesta mogu se filtrirati po lokaciji te sortirati po cijeni uzlazno/silazno i po nazivu.

Izračunato polje: ukupna cijena rezervacije računa se metodom Reservation.total_price() iz trajanja rezervacije i cijene parkinga po satu.
Lookup/povezana polja ostvarena su SQLAlchemy relacijama, npr. Reservation.parking za dohvat naziva i lokacije parkinga te ParkingSpot.owner za dohvat vlasnika.

## 9. BLOB polje u bazi — 3 boda

Tablica parking_spots sadrži BLOB polje photo u koje se sprema fotografija parkirnog mjesta kao binarni sadržaj. Uz njega se sprema i MIME tip slike (photo_mime). Fotografija se učitava kroz obrazac za dodavanje/uređivanje parkinga, sprema izravno u SQLite bazu, može se zamijeniti ili ukloniti te se čita iz baze i prikazuje na stranici detalja parkinga. Podržani su JPEG, PNG i WebP formati uz ograničenje veličine datoteke.

## 10. PDF izvještaj — 5 bodova

Aplikacija automatski generira PDF potvrdu rezervacije. Izvještaj sadrži podatke o rezervaciji: identifikator, početak i završetak, trajanje, status i izračunatu ukupnu cijenu. U PDF se uključuju i povezani podaci iz tablice users (korisničko ime korisnika) te iz tablice parking_spots (naziv parkinga, lokacija, vlasnik i cijena po satu), čime se demonstrira master-detail izvještaj nad više tablica. PDF se generira pomoću biblioteke ReportLab i korisnik ga može preuzeti iz popisa svojih rezervacija.

## 11. Paralelno izvršavanje dretvama — 5 bodova

Aplikacija demonstrira paralelno izvršavanje tri neovisna mrežna zadatka pomoću bazena dretvi (concurrent.futures.ThreadPoolExecutor). Paralelno se dohvaćaju vremenski podaci za Zagreb, Samobor i Veliku Goricu s udaljenog REST servisa Open-Meteo. Administratorska stranica Dretve prikazuje naziv dretve koja je izvršila svaki zadatak te uspoređuje ukupno vrijeme sekvencijalnog i paralelnog izvršavanja i izračunava faktor ubrzanja. Korištenje više dretvi smanjuje ukupno čekanje jer se mrežni I/O zahtjevi izvršavaju istodobno.

## 13. Sinkronizacija dretvi — 2 boda

Za zaštitu zajedničkog zapisnika zahtjeva koji istodobno koriste radne dretve koristi se threading.Lock. Svaka dretva prije upisa rezultata u zajedničku strukturu ulazi u kritični odsječak zaštićen Lock objektom, čime se sprječava istodobno nekontrolirano mijenjanje zajedničkih podataka.

## 14. Komunikacija između procesa — 4 boda

Aplikacija demonstrira komunikaciju između dva zasebna procesa. Proces A je Flask aplikacija (run.py) koja pomoću subprocess.run pokreće proces B, zasebnu Python skriptu reservation_worker.py. Proces B čita SQLite bazu i provjerava konzistentnost rezervacija, uključujući neispravne vremenske intervale i preklapanja aktivnih rezervacija. Proces B vraća cjelobrojni izlazni kod: 0 kada je provjera uspješna, 1 kada su pronađeni problemi u podacima, a 2 kod tehničke greške. Proces A čita returncode, stdout i stderr te korisniku prikazuje odgovarajuću poruku. Administratorska stranica Procesi omogućuje i kontroliranu simulaciju greške radi demonstracije nenultog izlaznog koda.

## 20. Udaljeni REST servis — 3 boda

Aplikacija se spaja na udaljeni REST web servis Open-Meteo (https://open-meteo.com/). HTTP zahtjevima dohvaća aktualne vremenske podatke za tri lokacije: Zagreb, Samobor i Veliku Goricu. Podaci se koriste na administratorskoj demonstracijskoj stranici Dretve kako bi se prikazali rezultati udaljenog servisa i usporedile performanse sekvencijalnih i paralelnih mrežnih poziva.

## 21. Vlastiti REST servis i klijent — 4 boda

Aplikacija sadrži REST klijent komponentu u glavnoj Flask aplikaciji (run.py, port 5000) koja se preko HTTP-a spaja na vlastiti ParKING REST servis implementiran kao zasebna Flask aplikacija (api_app.py, port 5001) i zaseban proces. Obje aplikacije rade u istom Docker containeru, ali imaju odvojene Flask instance i procese. Servis izlaže resurse /api/parkings i /api/reservations. Za parkings podržani su GET/POST te GET/PUT/DELETE nad pojedinim parkingom; za reservations GET/POST te GET/DELETE nad pojedinom rezervacijom. REST klijent demonstrira HTTP GET za oba resursa. Odvojenost se može dokazati tako da /api/parkings na portu 5001 vraća 401 bez Bearer tokena, dok ista ruta na portu 5000 vraća 404.

## 22. REST autentifikacija i autorizacija — 4 boda

Vlastiti REST servis koristi Bearer API token u HTTP zaglavlju Authorization. Zahtjev bez tokena ili s neispravnim tokenom vraća HTTP 401. Autorizacija se provodi po korisniku i ulozi. Na resursu /api/parkings obični korisnik može čitati parkinge, ali PUT/DELETE nad tuđim parkingom vraća HTTP 403; vlasnik parkinga i administrator imaju pravo izmjene. Na resursu /api/reservations obični korisnik vidi i dohvaća samo vlastite rezervacije, dok pokušaj pristupa tuđoj rezervaciji vraća HTTP 403; administrator ima pristup svim rezervacijama. Time se mogu demonstrirati dva korisnika (npr. gost i vlasnik/admin) i dva resursa (parkings i reservations) s različitim ovlastima.

## 23. Simetrično šifriranje AES-GCM — 2 boda

Aplikacija demonstrira simetrično šifriranje i dešifriranje korisničkih bilješki pomoću algoritma AES-GCM. Za korisnika se generira šifrirana datoteka u direktoriju exports, s vlastitim zaglavljem PKAE i slučajnim nonceom. Šifrirani sadržaj nije čitljiv kao tekst, a aplikacija ga može dešifrirati i ponovno prikazati izvorne bilješke. Lozinke korisnika ne pohranjuju se reverzibilno šifrirane.

## 25. SHA-256, sol i papar — 7 bodova

Aplikacija demonstrira SHA-256 funkciju sažimanja nad proizvoljnim tekstom. Koristi se promjenjiva sol koja se ne sprema u bazu ni datoteku, nego se deterministički izvodi po pravilu SHA256('ParKING-SHA256-salt:<user_id>:<username>')[0:16], pa različiti korisnici dobivaju različitu sol. Uz sol se koristi i papar iz raspona 0-255. Provjera ispravnosti papra demonstrira se prolaskom kroz cijeli raspon svih 256 mogućih vrijednosti; za testni sažetak pronađena je vrijednost papra 137 i potvrđena ispravnost sažetka.
