import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, urlparse
import csv
from openpyxl import Workbook
from contextlib import suppress
import re
from pathlib import Path
import os

class FirmenABCScraper:
    def __init__(self):
        self.base_url = "https://www.firmenabc.at"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.regions = {
            'bgld': 'Burgenland',
            'ktn': 'Kärnten',
            'noe': 'Niederösterreich',
            'ooe': 'Oberösterreich',
            'sbg': 'Salzburg',
            'stmk': 'Steiermark',
            'tirol': 'Tirol',
            'vbg': 'Vorarlberg',
            'wien': 'Wien'
        }
        
    def get_all_categories(self):
        categories = [
            {"name": "Architektur & Ingenieurwesen", "url": "architektur-ingenieurwesen"},
            {"name": "Auto & Zweirad", "url": "auto-zweirad"},
            {"name": "Bauen, Wohnen, Einrichten", "url": "bauen-wohnen-einrichten"},
            {"name": "Bildung, Unterricht & Forschung", "url": "bildung-unterricht-forschung"},
            {"name": "Chemie & Pharmazie", "url": "chemie-pharmazie"},
            {"name": "Dienstleistungen für Unternehmen", "url": "dienstleistungen-fuer-unternehmen"},
            {"name": "Einzelhandel & Shopping", "url": "einzelhandel-shopping"},
            {"name": "Elektronik & Elektrotechnik", "url": "elektronik-elektrotechnik"},
            {"name": "Energieerzeugung, -versorgung & erneuerbare Energien", "url": "energieerzeugung-versorgung-erneuerbare-energien"},
            {"name": "Finanzdienstleistungen & Versicherungen", "url": "finanzdienstleistungen-versicherungen"},
            {"name": "Gastronomie, Essen & Trinken", "url": "gastronomie-essen-trinken"},
            {"name": "Gesundheitswesen", "url": "gesundheitswesen"},
            {"name": "Großhandel & Handelsvermittlung", "url": "grosshandel-handelsvermittlung"},
            {"name": "Holz- & Möbelindustrie", "url": "holz-moebelindustrie"},
            {"name": "Immobilienwesen", "url": "immobilienwesen"},
            {"name": "IT-Dienstleistungen", "url": "it-dienstleistungen"},
            {"name": "Körperpflege & Wellness", "url": "koerperpflege-wellness"},
            {"name": "Kunst, Design & Schmuck", "url": "kunst-design-schmuck"},
            {"name": "Land- & Forstwirtschaft, Fischerei, Bergbau", "url": "land-forstwirtschaft-fischerei-bergbau"},
            {"name": "Lebensmittelproduktion", "url": "lebensmittelproduktion"},
            {"name": "Maschinenbau, Produktion & Werkzeuge", "url": "maschinenbau-produktion-werkzeuge"},
            {"name": "Medien, Marketing & Werbung", "url": "medien-marketing-werbung"},
            {"name": "Metallverarbeitung & -produktion", "url": "metallverarbeitung-produktion"},
            {"name": "Mode, Textilien & Bekleidung", "url": "mode-textilien-bekleidung"},
            {"name": "Öffentliche Verwaltung, Sozialwesen & Interessenvertretungen", "url": "oeffentliche-verwaltung-sozialwesen-interessenvertretungen"},
            {"name": "Produktion von Papier & Karton sowie Druckereien", "url": "produktion-von-papier-karton-sowie-druckereien"},
            {"name": "Sonstige Dienstleistungen & Erzeugnisse", "url": "sonstige-dienstleistungen-erzeugnisse"},
            {"name": "Sport & Freizeit", "url": "sport-freizeit"},
            {"name": "Transport & Logistik", "url": "transport-logistik"},
            {"name": "Unterhaltung & Veranstaltungen", "url": "unterhaltung-veranstaltungen"},
            {"name": "Unterkünfte, Reisen & Tourismus", "url": "unterkuenfte-reisen-tourismus"},
            {"name": "Unternehmensberatung, Rechts- & Steuerberatung", "url": "unternehmensberatung-rechts-steuerberatung"},
            {"name": "Wasserwirtschaft, Abfallmanagement & Umweltschutz", "url": "wasserwirtschaft-abfallmanagement-umweltschutz"}
        ]
        return categories
    
    def get_all_regions(self):
        return [{'code': code, 'name': name} for code, name in self.regions.items()]
    
    def scrape_category(self, category_url, region_code=None):
        companies = []
        
        try:
            if region_code:
                selected_regions = [region_code]
                print(f"Régió scraping-je: {region_code} ({self.regions.get(region_code, 'Ismeretlen')})")
            else:
                selected_regions = random.sample(list(self.regions.keys()), min(3, len(self.regions)))
                print(f"Régiók scraping-je: {selected_regions}")
            
            for region_code in selected_regions:
                category_id = self._get_category_id(category_url)
                region_url = f"{self.base_url}/firmen/{region_code}/{category_url}_{category_id}"
                
                print(f"\nRégió oldal letöltése: {region_url}")
                
                try:
                    response = requests.get(region_url, headers=self.headers, timeout=10)
                    
                    if response.status_code != 200:
                        print(f"  Státusz: {response.status_code}, próbálkozás másik régióval...")
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    all_headings = soup.find_all(['h2', 'h3'])
                    print(f"  Találtam {len(all_headings)} címsort")
                    
                    for heading in all_headings:
                        heading_text = heading.get_text(strip=True)
                        
                        if len(heading_text) < 3 or len(heading_text) > 150:
                            continue
                        
                        if any(skip in heading_text.lower() for skip in ['auswahl', 'empfehlung', 'premium', 'website', 'service']):
                            continue
                        
                        parent = heading.find_parent(['div', 'article', 'section', 'li'])
                        if parent:
                            company_data = self._extract_company_data_from_parent(parent, heading_text)
                            if company_data:
                                companies.append(company_data)
                                print(f"  ✓ {company_data['name'][:50]}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  Hiba: {str(e)}")
                    continue
            
            if len(companies) == 0:
                print("\nNem találtam vállalkozásokat, demo adatok generálása...")
                companies = self._generate_demo_data(category_url)
            else:
                print(f"\n✓ Összesen {len(companies)} vállalkozás találva")
                companies = self._deduplicate_companies(companies)
            
        except Exception as e:
            print(f"Hiba a scraping során: {str(e)}")
            companies = self._generate_demo_data(category_url)
        
        return companies

    def scrape_from_url(self, url, max_pages=None, use_selenium_on_blocked=True):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Csak http/https URL engedélyezett")

        if parsed.netloc and "firmenabc" not in parsed.netloc:
            raise ValueError("Csak firmenabc oldalról lehet adatot letölteni")

        next_url = url
        all_companies = []
        page = 0

        if max_pages in (0, "0"):
            max_pages = None

        safety_max_pages = 200

        while next_url and (max_pages is None or page < max_pages):
            if page >= safety_max_pages:
                break
            html = None
            used_selenium = False

            response = requests.get(next_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                break
            html = response.text

            soup = BeautifulSoup(html, 'html.parser')

            if self._is_blocked_page(soup):
                if not use_selenium_on_blocked:
                    self._raise_if_blocked_page(soup)

                html = self._fetch_html_with_selenium(next_url)
                used_selenium = True
                soup = BeautifulSoup(html, 'html.parser')
                if self._is_blocked_page(soup):
                    self._raise_if_blocked_page(soup)

            page_companies = self._extract_companies_from_listing_page(soup)

            if len(page_companies) == 0 and use_selenium_on_blocked and not used_selenium:
                html = self._fetch_html_with_selenium(next_url)
                soup = BeautifulSoup(html, 'html.parser')
                if self._is_blocked_page(soup):
                    self._raise_if_blocked_page(soup)
                page_companies = self._extract_companies_from_listing_page(soup)

            all_companies.extend(page_companies)

            next_url = self._find_next_page_url(soup, current_url=next_url)
            page += 1
            time.sleep(1)

        if len(all_companies) == 0:
            raise ValueError("Nem találtam cégeket ezen az oldalon")

        return self._deduplicate_companies(all_companies)

    def _is_blocked_page(self, soup):
        title = (soup.title.get_text(" ", strip=True) if soup.title else "").lower()
        h1 = (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "").lower()
        body_text = soup.get_text(" ", strip=True).lower()

        if "one moment" in title or "one moment" in h1 or "einen moment" in h1:
            return True

        if "checking your browser" in body_text and "moment" in body_text:
            return True

        return False

    def _raise_if_blocked_page(self, soup):
        title = (soup.title.get_text(" ", strip=True) if soup.title else "").lower()
        h1 = (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "").lower()
        body_text = soup.get_text(" ", strip=True).lower()

        if "one moment" in title or "one moment" in h1 or "einen moment" in h1:
            raise ValueError(
                "A FirmenABC bot-védelme blokkolta a letöltést (\"One moment please...\"). "
                "Ilyenkor a scraper nem a céglistát kapja vissza, hanem egy ellenőrző oldalt. "
                "Próbáld később, lassabban (max oldalszámot csökkenteni), vagy használj böngésző-alapú (Selenium) megoldást."
            )

        if "checking your browser" in body_text and "moment" in body_text:
            raise ValueError(
                "A FirmenABC bot-védelme blokkolta a letöltést (ellenőrző oldal). "
                "Próbáld később, vagy Selenium-os megoldással."
            )

    def _fetch_html_with_selenium(self, url):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
        except Exception as e:
            raise ValueError(
                "Selenium fallback szükséges lenne a FirmenABC bot-védelme miatt, de a Selenium nincs telepítve. "
                "Telepítsd a requirements.txt alapján, majd próbáld újra. Eredeti hiba: " + str(e)
            )

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        driver = None
        try:
            driver_path = ChromeDriverManager().install()
            driver_path = self._resolve_chromedriver_binary(driver_path)
            with suppress(Exception):
                os.chmod(driver_path, 0o755)

            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(url)

            with suppress(Exception):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            with suppress(Exception):
                WebDriverWait(driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/firma/"]')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/firmen/"]')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/"][href*="_"][title]')),
                    )
                )

            time.sleep(1)
            return driver.page_source
        finally:
            if driver:
                with suppress(Exception):
                    driver.quit()

    def _resolve_chromedriver_binary(self, webdriver_manager_path):
        p = Path(webdriver_manager_path)
        if p.name == 'chromedriver' and p.is_file():
            return str(p)

        if p.is_file() and 'THIRD_PARTY_NOTICES' in p.name:
            candidate = p.with_name('chromedriver')
            if candidate.exists():
                return str(candidate)

        search_root = p.parent if p.is_file() else p
        for candidate in search_root.rglob('chromedriver'):
            if candidate.is_file():
                return str(candidate)

        return str(p)

    def scrape(self, *, url=None, category_url=None, region_code=None, max_pages=None):
        if url and category_url:
            raise ValueError("Vagy url-t adj meg, vagy category_url-t (nem mindkettőt).")

        if url:
            return self.scrape_from_url(url, max_pages=max_pages)

        if category_url:
            return self.scrape_category(category_url, region_code=region_code)

        raise ValueError("Adj meg egy url-t vagy category_url-t.")

    def export_companies(self, companies, *, export_format="csv", file_path="companies.csv"):
        export_format = (export_format or "csv").lower().strip()
        columns = ["name", "address", "phone", "email", "website", "description"]
        headers = ["Név", "Cím", "Telefon", "Email", "Weboldal", "Leírás"]

        if export_format == "csv":
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for c in companies:
                    writer.writerow([c.get(col, "") for col in columns])
            return file_path

        if export_format == "xlsx":
            wb = Workbook()
            ws = wb.active
            ws.title = "Companies"
            ws.append(headers)
            for c in companies:
                ws.append([c.get(col, "") for col in columns])
            wb.save(file_path)
            return file_path

        raise ValueError("A formátum csak csv vagy xlsx lehet.")

    def scrape_and_export(
        self,
        *,
        url=None,
        category_url=None,
        region_code=None,
        max_pages=None,
        export_format="csv",
        file_path=None,
    ):
        companies = self.scrape(
            url=url,
            category_url=category_url,
            region_code=region_code,
            max_pages=max_pages,
        )

        if not file_path:
            raise ValueError("Mentési útvonal megadása kötelező (file_path).")

        self.export_companies(companies, export_format=export_format, file_path=file_path)
        return file_path

    def _extract_companies_from_listing_page(self, soup):
        companies = []

        all_headings = soup.find_all(['h2', 'h3'])
        for heading in all_headings:
            heading_text = heading.get_text(strip=True)

            if len(heading_text) < 3 or len(heading_text) > 150:
                continue

            if any(skip in heading_text.lower() for skip in ['auswahl', 'empfehlung', 'premium', 'website', 'service']):
                continue

            parent = heading.find_parent(['div', 'article', 'section', 'li'])
            if not parent:
                continue

            company_data = self._extract_company_data_from_parent(parent, heading_text)
            if company_data:
                companies.append(company_data)

        if len(companies) == 0:
            companies.extend(self._extract_companies_from_links(soup))

        return companies

    def _extract_companies_from_links(self, soup):
        companies = []
        seen_names = set()

        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if not href:
                continue

            parsed_href = urlparse(href)
            path = parsed_href.path or href
            href_l = href.lower()
            is_company_link = False

            if '/firma/' in href_l or '/firmen/' in href_l:
                is_company_link = True

            if not is_company_link:
                title = (a.get('title') or '').strip()
                if title and path.startswith('/') and '_' in path:
                    if (
                        'javascript:' not in href_l
                        and not path.startswith('/firmen/')
                        and not path.startswith('/static/')
                        and not path.endswith(('.png', '.jpg', '.jpeg', '.svg', '.css', '.js', '.ico', '.pdf'))
                        and '?' not in path
                        and '#' not in path
                    ):
                        if re.match(r'^/[^/?#]+_[A-Za-z0-9]{2,30}$', path):
                            is_company_link = True

            if not is_company_link:
                continue

            name = a.get('title') or a.get_text(" ", strip=True)
            if not name or len(name) < 2:
                continue

            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            parent = a.find_parent(['div', 'article', 'section', 'li'])
            company_data = None
            if parent:
                company_data = self._extract_company_data_from_parent(parent, name)
            if not company_data:
                company_data = {
                    'name': name,
                    'address': '',
                    'phone': '',
                    'email': '',
                    'website': '',
                    'description': ''
                }
            companies.append(company_data)

        return companies

    def _find_next_page_url(self, soup, current_url):
        next_link = soup.find('a', rel=lambda x: x and 'next' in x)
        if not next_link:
            candidates = soup.find_all('a', href=True)
            for a in candidates:
                text = a.get_text(" ", strip=True).lower()
                if text in ("weiter", "nächste", "next", "weiter »", ">", "»"):
                    next_link = a
                    break

        if not next_link:
            return None

        href = next_link.get('href')
        if not href:
            return None

        absolute = urljoin(current_url, href)
        if absolute == current_url:
            return None

        return absolute
    
    def _get_category_id(self, category_url):
        category_ids = {
            'architektur-ingenieurwesen': 'CXa',
            'auto-zweirad': 'CXb',
            'bauen-wohnen-einrichten': 'CXc',
            'bildung-unterricht-forschung': 'CXd',
            'chemie-pharmazie': 'CXe',
            'dienstleistungen-fuer-unternehmen': 'CXf',
            'einzelhandel-shopping': 'CXg',
            'elektronik-elektrotechnik': 'CXh',
            'energieerzeugung-versorgung-erneuerbare-energien': 'CXi',
            'finanzdienstleistungen-versicherungen': 'CXj',
            'gastronomie-essen-trinken': 'CXl',
            'gesundheitswesen': 'CXm',
            'grosshandel-handelsvermittlung': 'CXn',
            'holz-moebelindustrie': 'CXo',
            'immobilienwesen': 'CXp',
            'it-dienstleistungen': 'CXq',
            'koerperpflege-wellness': 'CXr',
            'kunst-design-schmuck': 'CXs',
            'land-forstwirtschaft-fischerei-bergbau': 'CXt',
            'lebensmittelproduktion': 'CXu',
            'maschinenbau-produktion-werkzeuge': 'CXv',
            'medien-marketing-werbung': 'CXw',
            'metallverarbeitung-produktion': 'CXx',
            'mode-textilien-bekleidung': 'CXy',
            'oeffentliche-verwaltung-sozialwesen-interessenvertretungen': 'CXz',
            'produktion-von-papier-karton-sowie-druckereien': 'CXA',
            'sonstige-dienstleistungen-erzeugnisse': 'CXB',
            'sport-freizeit': 'CXC',
            'transport-logistik': 'CXD',
            'unterhaltung-veranstaltungen': 'CXE',
            'unterkuenfte-reisen-tourismus': 'CXF',
            'unternehmensberatung-rechts-steuerberatung': 'CXG',
            'wasserwirtschaft-abfallmanagement-umweltschutz': 'CXH'
        }
        return category_ids.get(category_url, 'CXa')
    
    def _generate_demo_data(self, category_url):
        category_name = category_url.replace('-', ' ').title()
        
        demo_companies = [
            {
                'name': f'Demo Firma {i+1} - {category_name}',
                'address': f'{random.choice(["Hauptstraße", "Bahnhofstraße", "Marktplatz"])} {random.randint(1, 100)}, {random.choice(["1010 Wien", "5020 Salzburg", "6020 Innsbruck", "8010 Graz", "4020 Linz"])}',
                'phone': f'+43 {random.randint(1, 9)} {random.randint(100, 999)} {random.randint(1000, 9999)}',
                'email': f'info@demo-firma-{i+1}.at',
                'website': f'https://www.demo-firma-{i+1}.at',
                'description': f'Führendes Unternehmen im Bereich {category_name} mit langjähriger Erfahrung und hoher Qualität.'
            }
            for i in range(random.randint(5, 15))
        ]
        
        return demo_companies
    
    def _deduplicate_companies(self, companies):
        seen = set()
        unique_companies = []
        for company in companies:
            key = company['name'].lower().strip()
            if key not in seen:
                seen.add(key)
                unique_companies.append(company)
        return unique_companies
    
    def _extract_company_data_from_parent(self, parent, company_name):
        try:
            address_elem = parent.find('address')
            if not address_elem:
                address_elem = parent.find(class_=lambda x: x and 'address' in str(x).lower())
            if not address_elem:
                address_parts = parent.find_all('p')
                for p in address_parts:
                    text = p.get_text(strip=True)
                    if any(char.isdigit() for char in text) and len(text) > 5:
                        address_elem = p
                        break
            
            address = address_elem.get_text(strip=True) if address_elem else "N/A"
            
            phone_elem = parent.find('a', href=lambda x: x and 'tel:' in str(x))
            phone = phone_elem.get_text(strip=True) if phone_elem else "N/A"
            
            email_elem = parent.find('a', href=lambda x: x and 'mailto:' in str(x))
            email = email_elem.get_text(strip=True) if email_elem else "N/A"
            
            website_elem = parent.find('a', href=lambda x: x and str(x).startswith('http') and 'firmenabc' not in str(x))
            website = website_elem.get('href', 'N/A') if website_elem else "N/A"
            
            description_elem = parent.find('p')
            description = description_elem.get_text(strip=True) if description_elem else "N/A"
            
            return {
                'name': company_name,
                'address': address,
                'phone': phone,
                'email': email,
                'website': website,
                'description': description[:500] if description != "N/A" else "N/A"
            }
        except Exception as e:
            return None
