import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class FirmenABCScraper:
    def __init__(self):
        self.base_url = "https://www.firmenabc.at"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.driver = None
        
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
    
    def _init_driver(self):
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def scrape_category(self, category_url):
        url = f"{self.base_url}/{category_url}"
        companies = []
        
        try:
            self._init_driver()
            
            print(f"Oldal betöltése: {url}")
            self.driver.get(url)
            
            time.sleep(3)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            company_cards = soup.find_all('div', class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['company', 'firm', 'business', 'card']))
            
            if not company_cards:
                company_cards = soup.find_all('article')
            
            if not company_cards:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if '/firmen/' in href and len(href.split('/')) > 2:
                        parent = link.find_parent(['div', 'article', 'section'])
                        if parent and parent not in company_cards:
                            company_cards.append(parent)
            
            print(f"Talált elemek száma: {len(company_cards)}")
            
            for card in company_cards:
                company_data = self._extract_company_data(card)
                if company_data and company_data.get('name') != 'N/A':
                    companies.append(company_data)
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Hiba a scraping során: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        return companies
    
    def __del__(self):
        if self.driver:
            self.driver.quit()
    
    def _extract_company_data(self, card):
        try:
            name = card.find(['h2', 'h3', 'h4'])
            name = name.get_text(strip=True) if name else "N/A"
            
            address_elem = card.find('address') or card.find(class_=lambda x: x and 'address' in str(x).lower())
            address = address_elem.get_text(strip=True) if address_elem else "N/A"
            
            phone_elem = card.find('a', href=lambda x: x and 'tel:' in str(x))
            phone = phone_elem.get_text(strip=True) if phone_elem else "N/A"
            
            email_elem = card.find('a', href=lambda x: x and 'mailto:' in str(x))
            email = email_elem.get_text(strip=True) if email_elem else "N/A"
            
            website_elem = card.find('a', href=lambda x: x and ('http' in str(x) or 'www' in str(x)))
            website = website_elem.get('href', 'N/A') if website_elem else "N/A"
            
            description_elem = card.find('p')
            description = description_elem.get_text(strip=True) if description_elem else "N/A"
            
            return {
                'name': name,
                'address': address,
                'phone': phone,
                'email': email,
                'website': website,
                'description': description
            }
        except Exception as e:
            print(f"Hiba az adatok kinyerése során: {str(e)}")
            return None
