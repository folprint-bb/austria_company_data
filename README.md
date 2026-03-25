# 🏢 FirmenABC Scraper

Osztrák vállalkozások adatainak automatikus gyűjtése a firmenabc.at oldalról, modern webes felülettel és szűrési lehetőségekkel.

## 📋 Funkciók

- **Automatikus adatgyűjtés**: 33 különböző kategóriából gyűjt vállalkozási adatokat
- **Adattárolás**: SQLite adatbázisban tárolja a letöltött információkat
- **Szűrés és keresés**: Kategória és szöveges keresés alapján szűrheted az adatokat
- **Modern felület**: Egyszerű, könnyen kezelhető webes felület
- **Exportálható adatok**: Az adatbázisból könnyen exportálhatók az adatok

## 🚀 Telepítés

### 1. Python telepítése
Győződj meg róla, hogy Python 3.8 vagy újabb verzió telepítve van a gépeden.

### 2. Függőségek telepítése
```bash
pip install -r requirements.txt
```

## 💻 Használat

### Alkalmazás indítása
```bash
python app.py
```

Az alkalmazás elindul a `http://localhost:5000` címen.

### Webes felület használata

1. **Nyisd meg a böngészőt** és menj a `http://localhost:5000` címre
2. **Válassz kategóriát** a legördülő menüből (pl. Lebensmittelproduktion)
3. **Kattints az "Adatok letöltése" gombra** - ez letölti és elmenti az adatokat
4. **Keress az adatok között** a keresőmező segítségével
5. **Szűrj kategória szerint** a legördülő menü használatával

## 📊 Elérhető kategóriák

Az alkalmazás 33 különböző kategóriából tud adatokat gyűjteni:

- Lebensmittelproduktion (Élelmiszergyártás)
- IT-Dienstleistungen (IT szolgáltatások)
- Bauen, Wohnen, Einrichten (Építés, lakás, berendezés)
- Gastronomie, Essen & Trinken (Vendéglátás)
- Auto & Zweirad (Autó és kétkerekű)
- ... és még 28 további kategória

## 🗂️ Projekt struktúra

```
windsurf-project-9/
│
├── app.py                 # Flask alkalmazás (API végpontok)
├── scraper.py            # Web scraping logika
├── database.py           # Adatbázis műveletek
├── requirements.txt      # Python függőségek
├── README.md            # Dokumentáció
│
├── templates/
│   └── index.html       # Webes felület
│
└── companies.db         # SQLite adatbázis (automatikusan létrejön)
```

## 🔧 API végpontok

### GET `/api/categories`
Visszaadja az összes elérhető kategóriát.

### POST `/api/scrape`
Adatok letöltése egy adott kategóriából.
```json
{
  "category": "lebensmittelproduktion"
}
```

### GET `/api/companies`
Vállalkozások lekérdezése szűrési lehetőségekkel.
- `category`: Kategória szerinti szűrés
- `search`: Szöveges keresés

### DELETE `/api/companies/delete`
Adatok törlése az adatbázisból.
- `category`: Csak egy kategória törlése (opcionális)

## 📝 Gyűjtött adatok

Minden vállalkozásról a következő adatokat gyűjti:

- **Név**: A vállalkozás neve
- **Cím**: Székhely címe
- **Telefon**: Telefonszám
- **Email**: Email cím
- **Weboldal**: Weboldal URL
- **Leírás**: Rövid leírás a vállalkozásról
- **Kategória**: Melyik kategóriába tartozik
- **Letöltés ideje**: Mikor lett letöltve az adat

## ⚠️ Fontos megjegyzések

1. **Etikus használat**: Az adatgyűjtés során tartsd tiszteletben a weboldal használati feltételeit
2. **Késleltetés**: A scraper 1 másodperces késleltetést használ a kérések között
3. **Adatvédelem**: A gyűjtött adatok csak helyben, az SQLite adatbázisban tárolódnak

## 🛠️ Hibaelhárítás

### "ModuleNotFoundError" hiba
Futtasd újra: `pip install -r requirements.txt`

### Az oldal nem tölt be
Ellenőrizd, hogy a 5000-es port szabad-e, vagy változtasd meg az `app.py` fájlban.

### Nincs adat letöltve
Lehet, hogy az oldal struktúrája megváltozott. Ellenőrizd a `scraper.py` fájlt.

## 📄 Licenc

Ez a projekt oktatási és személyes használatra készült.

## 🤝 Közreműködés

Ha hibát találsz vagy fejlesztési ötleted van, nyugodtan jelezd!
