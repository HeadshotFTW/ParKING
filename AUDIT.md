# ParKING — završni audit kriterija

Ovaj dokument sažima trenutno stanje projekta prema prijavnici i služi kao interna kontrolna lista prije obrane.

## Procijenjeni rezultat

Konzervativna procjena: **70 bodova**.

| Rb. | Kriterij | Bodovi | Procjena | Dokaz / napomena |
|---:|---|---:|---|---|
| 1 | Korisničke klase | 3 | sigurno | `User`, `ParkingSpot`, `Reservation`, svaka s atributima i metodama. |
| 2 | Dijalozi / forme | 4 | sigurno | Više od tri forme i međusobna komunikacija kroz Flask rute, bazu i sesiju. |
| 3 | HR / EN sučelje | 4 | sigurno | HR i EN, prevedeno više od pet stranica/dijaloga. |
| 4 | INI / Registry | 2 | sigurno | `config.ini`: `default_language`, `items_per_page`. Registry se ne koristi. |
| 5 | XML / JSON CRUD | 4 | sigurno | JSON CRUD nad nizom bilješki u `data/parking_notes.json`. XML se ne koristi. |
| 6 | Vlastiti binarni format | 3 | sigurno | `data/search_history.bin`, zaglavlje `PKSR`, verzija i niz binarnih zapisa. |
| 7 | Baza i CRUD | 6 | sigurno | SQLite + SQLAlchemy, CRUD nad `users`, `parking_spots`, `reservations`. |
| 8 | Sort / filter / calculated / lookup | 5 | sigurno | Sortiranje i filtriranje parkinga, ukupna cijena rezervacije, ORM relacije. |
| 9 | BLOB | 3 | sigurno | Fotografija parkinga u BLOB polju `photo`, upload/prikaz/zamjena/uklanjanje. |
| 10 | Izvještaj / PDF / master-detail | 5 | sigurno | PDF potvrda rezervacije s podacima iz tri povezane tablice. |
| 11 | Dretve / thread pool | 5 | sigurno | `ThreadPoolExecutor(max_workers=3)`, tri Open-Meteo HTTP poziva, prikaz ubrzanja. |
| 12 | Sigurno UI ažuriranje iz dretve | 0 | ne računamo | Web/Flask izvedba ne dokazuje desktop `Synchronize/Queue` kriterij dovoljno jasno. |
| 13 | Sinkronizacija | 2 | sigurno | `threading.Lock` štiti zajednički zapisnik. Drugi mehanizam se ne koristi. |
| 14 | Proces A → B | 4 | sigurno | `run.py` pokreće `reservation_worker.py`, prenosi argumente, čita stdout/stderr i return code. |
| 15 | TCP | 0 | nije implementirano | — |
| 16 | UDP | 0 | nije implementirano | — |
| 17 | HTTP download komponenta | 0 | nije implementirano | Open-Meteo se računa pod udaljeni REST, ne pod ovaj kriterij. |
| 18 | Udaljeni SOAP | 0 | nije implementirano | — |
| 19 | Vlastiti SOAP | 0 | nije implementirano | — |
| 20 | Udaljeni REST | 3 | sigurno | Open-Meteo, tri lokacije. |
| 21 | Vlastiti REST servis + klijent | 4 | vrlo vjerojatno | Glavna aplikacija `run.py` radi na 5000, zasebna Flask aplikacija `api_app.py` kao zaseban proces na 5001. Klijent preko HTTP-a koristi `parkings` i `reservations`. Ne računamo 7 bodova jer nije IIS/Apache. |
| 22 | REST autentifikacija i autorizacija | 4 | vjerojatno / demonstrirati pažljivo | Bearer token; 401 bez tokena; 403 za izmjenu tuđeg parkinga i pristup tuđoj rezervaciji; admin ima šire ovlasti. Na obrani eksplicitno pokazati dva korisnika i dva resursa. |
| 23 | Simetrična kriptografija | 2 | sigurno | AES-GCM šifriranje/dešifriranje bilješki, datoteka `PKAE`. |
| 24 | Asimetrična kriptografija | 0 | nije implementirano | — |
| 25 | SHA-256 + sol + papar | 7 | vrlo vjerojatno | SHA-256, promjenjiva sol izvedena pravilom i ne sprema se, papar 0–255, provjera svih 256 vrijednosti. |
| 26 | Digitalni potpis | 0 | nije implementirano | — |
| 27–30 | Biblioteke / DLL | 0 | nije implementirano | Nisu potrebne za ciljanu ocjenu. |

## Zbroj

```text
3 + 4 + 4 + 2 + 4 + 3 + 6 + 5 + 3 + 5 + 5 + 2 + 4 + 3 + 4 + 4 + 2 + 7 = 70
```

Kriterij 12 i neimplementirani kriteriji nisu uključeni u zbroj.

## Najvažnije točke za obranu

### REST — dokaz odvojene aplikacije

```bash
docker compose logs --tail=50
curl http://localhost:5001/api/health
curl -i http://localhost:5001/api/parkings
curl -i http://localhost:5000/api/parkings
```

Očekivano:

- dva Flask procesa, portovi `5000` i `5001`,
- health na `5001` → `200`,
- `/api/parkings` na `5001` bez tokena → `401`,
- ista ruta na `5000` → `404`.

### REST autorizacija — kriterij 22

Na obrani ne stati samo na 401 bez tokena. Potrebno je pokazati i **autorizaciju**:

1. token korisnika `gost`,
2. pokušaj `PUT` ili `DELETE` nad parkingom korisnika `vlasnik` → `403`,
3. token vlasnika ili administratora nad istim parkingom → dopušteno,
4. na `reservations` pokazati da obični korisnik vidi/dohvaća samo vlastite rezervacije, a administrator ima širi pristup.

Time se izravno pokrivaju dva korisnika i dva resursa iz teksta kriterija.

### SHA-256 — kriterij 25

Naglasiti tri odvojene stvari:

- SHA-256 sažetak,
- promjenjiva sol se **ne sprema**, nego se ponovno izvodi pravilom iz `user_id` i `username`,
- provjera papra prolazi kroz cijeli raspon `0–255`, svih 256 vrijednosti.

## Demo stanje

Referentni dataset nalazi se u:

```text
demo/parking-demo.json
```

Prije obrane ga je moguće učitati preko **Test → Demo podaci → Import**. Dataset se može kasnije zamijeniti kvalitetnije pripremljenim exportom bez promjene dokumentacije.

## Zaključak

Projekt je dosegao ciljanu razinu bez potrebe za dodavanjem novih rizičnih funkcionalnosti. Najviše pažnje na obrani treba posvetiti kriterijima **21 i 22**, jer se oni najviše oslanjaju na način demonstracije i formulaciju da REST servis radi kao zasebna aplikacija/proces.