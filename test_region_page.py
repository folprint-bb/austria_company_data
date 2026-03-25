import requests
from bs4 import BeautifulSoup

test_urls = [
    "https://www.firmenabc.at/firmen/bgld/gastronomie-essen-trinken_CXl",
    "https://www.firmenabc.at/firmen/stmk/chemie-pharmazie_CXe"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for url in test_urls:
    print(f"\n{'='*80}")
    print(f"Tesztelés: {url}")
    print('='*80)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Státusz: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("\n1. Keresés 'company' vagy 'firm' osztályokra:")
        company_divs = soup.find_all(['div', 'article', 'section'], 
                                     class_=lambda x: x and any(k in str(x).lower() 
                                     for k in ['company', 'firm', 'business', 'card', 'item', 'list']))
        print(f"   Találatok: {len(company_divs)}")
        if company_divs:
            print(f"   Első elem osztályai: {company_divs[0].get('class')}")
        
        print("\n2. Keresés article elemekre:")
        articles = soup.find_all('article')
        print(f"   Találatok: {len(articles)}")
        
        print("\n3. Keresés h2, h3 címsorokra:")
        headings = soup.find_all(['h2', 'h3'])
        print(f"   Találatok: {len(headings)}")
        if headings:
            for i, h in enumerate(headings[:5]):
                print(f"   {i+1}. {h.get_text(strip=True)[:60]}")
        
        print("\n4. Keresés linkekre (a elemek):")
        links = soup.find_all('a', href=True)
        company_links = [l for l in links if l.get_text(strip=True) and len(l.get_text(strip=True)) > 5]
        print(f"   Összes link: {len(links)}")
        print(f"   Szöveges linkek: {len(company_links)}")
        if company_links:
            print(f"   Első 3 szöveges link:")
            for link in company_links[:3]:
                print(f"   - {link.get_text(strip=True)[:50]} | {link.get('href')[:50]}")
        
        print("\n5. Keresés 'ul' vagy 'ol' listákra:")
        lists = soup.find_all(['ul', 'ol'])
        print(f"   Találatok: {len(lists)}")
        
        print("\n6. Összes div osztály (első 30):")
        all_divs = soup.find_all('div', class_=True)
        classes = set()
        for div in all_divs[:100]:
            if div.get('class'):
                classes.update(div.get('class'))
        print(f"   Egyedi osztályok: {sorted(list(classes))[:30]}")
        
    except Exception as e:
        print(f"Hiba: {str(e)}")
