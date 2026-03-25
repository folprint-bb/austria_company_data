import requests
from bs4 import BeautifulSoup

url = "https://www.firmenabc.at/lebensmittelproduktion"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Letöltés: {url}")
response = requests.get(url, headers=headers, timeout=10)
print(f"Státusz kód: {response.status_code}")

soup = BeautifulSoup(response.content, 'html.parser')

print("\n=== HTML struktúra elemzése ===\n")

print("1. Keresés 'company' osztályú elemekre:")
company_divs = soup.find_all('div', class_=lambda x: x and 'company' in str(x).lower())
print(f"   Találatok: {len(company_divs)}")

print("\n2. Keresés 'firm' osztályú elemekre:")
firm_divs = soup.find_all('div', class_=lambda x: x and 'firm' in str(x).lower())
print(f"   Találatok: {len(firm_divs)}")

print("\n3. Keresés 'card' osztályú elemekre:")
card_divs = soup.find_all('div', class_=lambda x: x and 'card' in str(x).lower())
print(f"   Találatok: {len(card_divs)}")

print("\n4. Keresés article elemekre:")
articles = soup.find_all('article')
print(f"   Találatok: {len(articles)}")

print("\n5. Keresés 'list' osztályú elemekre:")
list_divs = soup.find_all(['div', 'ul'], class_=lambda x: x and 'list' in str(x).lower())
print(f"   Találatok: {len(list_divs)}")

print("\n6. Összes div osztály (első 50):")
all_divs = soup.find_all('div', class_=True)
classes = set()
for div in all_divs[:100]:
    if div.get('class'):
        classes.update(div.get('class'))
print(f"   Egyedi osztályok: {sorted(list(classes))[:30]}")

print("\n7. Keresés linkekre (a elemek):")
links = soup.find_all('a', href=lambda x: x and 'firmen' in str(x))
print(f"   'firmen' linkek száma: {len(links)}")
if links:
    print(f"   Első 5 link:")
    for link in links[:5]:
        print(f"   - {link.get('href')} | {link.get_text(strip=True)[:50]}")

print("\n8. HTML tartalom minta (első 2000 karakter):")
print(soup.prettify()[:2000])
