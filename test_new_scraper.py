from scraper_simple import FirmenABCScraper

scraper = FirmenABCScraper()

print("Tesztelés: Gastronomie kategória")
print("="*80)

companies = scraper.scrape_category('gastronomie-essen-trinken')

print("\n" + "="*80)
print(f"EREDMÉNY: {len(companies)} vállalkozás")
print("="*80)

for i, company in enumerate(companies[:5], 1):
    print(f"\n{i}. {company['name']}")
    print(f"   Cím: {company['address']}")
    print(f"   Telefon: {company['phone']}")
    print(f"   Email: {company['email']}")
    print(f"   Weboldal: {company['website']}")
