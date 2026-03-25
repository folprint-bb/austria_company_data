import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
import re
from urllib.parse import urljoin, urlparse

import os
from pathlib import Path

from bs4 import BeautifulSoup


@dataclass
class ScrapeResult:
    companies: list
    visited_pages: int
    visited_company_pages: int


class FirmenABCSeleniumScraper:
    def __init__(self):
        self.base_url = "https://www.firmenabc.at"
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self._cookie_autoclick_enabled = True

    def scrape_listing_to_companies(self, url, *, max_pages=1, wait_for_user_seconds=180):
        if not url:
            raise ValueError("URL megadása kötelező")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Csak http/https URL engedélyezett")

        if parsed.netloc and "firmenabc" not in parsed.netloc:
            raise ValueError("Csak firmenabc oldalról lehet adatot letölteni")

        if max_pages is None:
            max_pages = 0

        if isinstance(max_pages, str) and max_pages.strip() == "":
            max_pages = 0

        try:
            max_pages = int(max_pages)
        except Exception:
            raise ValueError("A max oldalszám csak szám lehet")

        if max_pages < 0:
            raise ValueError("A max oldalszám nem lehet negatív")

        driver = self._create_driver()
        try:
            driver.get(url)
            self._maybe_accept_cookiebot(driver)

            listing_pages = self._collect_listing_pages(
                driver,
                url,
                max_pages=max_pages,
                wait_for_user_seconds=wait_for_user_seconds,
            )

            company_urls = []
            for page_url in listing_pages:
                driver.get(page_url)
                self._wait_for_ready(driver, wait_for_user_seconds=wait_for_user_seconds)
                self._maybe_accept_cookiebot(driver)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                company_urls.extend(self._extract_company_profile_urls(soup, current_url=page_url))

            # dedupe, keep order
            seen = set()
            unique_company_urls = []
            for u in company_urls:
                if u in seen:
                    continue
                seen.add(u)
                unique_company_urls.append(u)

            companies = []
            visited_company_pages = 0
            for company_url in unique_company_urls:
                driver.get(company_url)
                self._wait_for_ready(driver, wait_for_user_seconds=wait_for_user_seconds)
                self._maybe_accept_cookiebot(driver)
                company = self._extract_company_details(driver, company_url=company_url)
                if self._is_allowed_company_name(company.get("name", "")) and self._has_valid_vat(company.get("vat_id", "")):
                    companies.append(company)
                visited_company_pages += 1

            if len(companies) == 0:
                raise ValueError("Nem találtam cégeket ezen az oldalon")

            return ScrapeResult(
                companies=self._deduplicate_by_name(companies),
                visited_pages=len(listing_pages),
                visited_company_pages=visited_company_pages,
            )
        finally:
            with suppress(Exception):
                driver.quit()

    def _maybe_accept_cookiebot(self, driver):
        if not self._cookie_autoclick_enabled:
            return

        underlay_selector = "#CybotCookiebotDialogBodyUnderlay"
        allow_all_selector = "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"

        # Try for up to 2 seconds. If the banner is not present, do nothing,
        # because it might appear on the next pages.
        end = time.time() + 2.0
        saw_underlay = False
        while time.time() < end:
            if self._is_element_present_including_iframes(driver, underlay_selector):
                saw_underlay = True
                if self._try_click_including_iframes(driver, allow_all_selector):
                    # Once accepted, it shouldn't appear again in the same browser profile.
                    self._cookie_autoclick_enabled = False
                    return

            time.sleep(0.1)

        if saw_underlay:
            raise ValueError(
                "Cookie consent ablak aktív (Cookiebot), de nem sikerült automatikusan elfogadni 2 másodperc alatt. "
                "Valószínűleg a banner blokkolja az oldalt."
            )

    def _is_element_present_including_iframes(self, driver, selector):
        try:
            from selenium.webdriver.common.by import By
        except Exception:
            return False

        # main document
        with suppress(Exception):
            driver.switch_to.default_content()
        with suppress(Exception):
            if driver.find_elements(By.CSS_SELECTOR, selector):
                return True

        # iframes
        frames = []
        with suppress(Exception):
            frames = driver.find_elements(By.TAG_NAME, "iframe")

        for fr in frames:
            with suppress(Exception):
                driver.switch_to.default_content()
                driver.switch_to.frame(fr)
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    with suppress(Exception):
                        driver.switch_to.default_content()
                    return True

        with suppress(Exception):
            driver.switch_to.default_content()
        return False

    def _try_click_including_iframes(self, driver, selector):
        try:
            from selenium.webdriver.common.by import By
        except Exception:
            return False

        # main document
        with suppress(Exception):
            driver.switch_to.default_content()
        if self._try_click(driver, By.CSS_SELECTOR, selector):
            return True

        # iframes
        frames = []
        with suppress(Exception):
            frames = driver.find_elements(By.TAG_NAME, "iframe")

        for fr in frames:
            with suppress(Exception):
                driver.switch_to.default_content()
                driver.switch_to.frame(fr)
                if self._try_click(driver, By.CSS_SELECTOR, selector):
                    with suppress(Exception):
                        driver.switch_to.default_content()
                    return True

        with suppress(Exception):
            driver.switch_to.default_content()
        return False

    def _try_click(self, driver, by, selector):
        elements = []
        with suppress(Exception):
            elements = driver.find_elements(by, selector)

        for el in elements:
            with suppress(Exception):
                if not el.is_displayed():
                    continue
                if not el.is_enabled():
                    continue
                el.click()
                return True

        return False

    def _create_driver(self):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
        except Exception as e:
            raise ValueError(
                "A Selenium nincs telepítve vagy nem elérhető. Futtsd: pip install -r requirements.txt. Eredeti hiba: "
                + str(e)
            )

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1400,900")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=" + self.user_agent)

        # Visible Chrome with an isolated profile.
        user_data_dir = tempfile.mkdtemp(prefix="firmenabc_profile_")
        chrome_options.add_argument("--user-data-dir=" + user_data_dir)

        driver_path = ChromeDriverManager().install()
        driver_path = self._resolve_chromedriver_binary(driver_path)
        with suppress(Exception):
            os.chmod(driver_path, 0o755)

        service = Service(driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

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

    def _wait_for_ready(self, driver, *, wait_for_user_seconds):
        # If a bot protection page appears, user can solve it in the visible Chrome window.
        end = time.time() + wait_for_user_seconds
        while True:
            html = driver.page_source or ""
            soup = BeautifulSoup(html, "html.parser")
            if not self._is_blocked_page(soup):
                return

            if time.time() > end:
                raise ValueError(
                    "A FirmenABC bot-védelme blokkolta a letöltést (\"One moment\"). "
                    "Kérlek a megnyitott Chrome ablakban oldd meg az ellenőrzést, majd próbáld újra."
                )

            time.sleep(1)

    def _is_blocked_page(self, soup):
        title = (soup.title.get_text(" ", strip=True) if soup.title else "").lower()
        h1 = (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "").lower()
        body_text = soup.get_text(" ", strip=True).lower()

        if "one moment" in title or "one moment" in h1 or "einen moment" in h1:
            return True

        if "checking your browser" in body_text and "moment" in body_text:
            return True

        return False

    def _collect_listing_pages(self, driver, start_url, *, max_pages, wait_for_user_seconds):
        # max_pages == 0 means unlimited until no next page (with a safety cap)
        safety_cap = 200

        pages = []
        current_url = start_url
        page = 0

        while current_url:
            if page >= safety_cap:
                break
            if max_pages and page >= max_pages:
                break

            pages.append(current_url)
            driver.get(current_url)
            self._wait_for_ready(driver, wait_for_user_seconds=wait_for_user_seconds)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            next_url = self._find_next_page_url(soup, current_url=current_url)
            if not next_url:
                break

            current_url = next_url
            page += 1

        return pages

    def _find_next_page_url(self, soup, *, current_url):
        next_link = soup.find("a", rel=lambda x: x and "next" in x)
        if not next_link:
            for a in soup.find_all("a", href=True):
                text = a.get_text(" ", strip=True).lower()
                if text in ("weiter", "nächste", "next", "weiter »", ">", "»"):
                    next_link = a
                    break

        if not next_link:
            return None

        href = next_link.get("href")
        if not href:
            return None

        absolute = urljoin(current_url, href)
        if absolute == current_url:
            return None

        return absolute

    def _extract_company_profile_urls(self, soup, *, current_url):
        urls = []

        for a in soup.find_all("a", href=True):
            title = (a.get("title") or "").strip()
            href = a.get("href")
            if not href or not title:
                continue

            parsed = urlparse(href)
            path = parsed.path or href

            if not path.startswith("/"):
                continue

            if "_" not in path:
                continue

            if "?" in path or "#" in path:
                continue

            if path.startswith("/firmen/") or path.startswith("/static/"):
                continue

            if any(path.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".ico", ".pdf")):
                continue

            # FirmenABC company profile links look like /slug_CODE
            urls.append(urljoin(current_url, path))

        return urls

    def _extract_company_details(self, driver, *, company_url):
        soup = BeautifulSoup(driver.page_source, "html.parser")

        name = ""
        h1 = soup.find("h1")
        if h1:
            name = h1.get_text(" ", strip=True)

        if not name and soup.title:
            name = soup.title.get_text(" ", strip=True)

        # Basic, robust extraction: first mailto/tel + first address-like block
        phone = ""
        email = ""
        website = ""
        street = ""
        zip_code = ""
        city = ""
        description = ""
        vat_id = ""
        managing_directors = ""
        shareholders = ""

        tel = soup.find("a", href=lambda x: x and "tel:" in x)
        if tel:
            phone = tel.get_text(" ", strip=True)

        mail = soup.find("a", href=lambda x: x and "mailto:" in x)
        if mail:
            email = mail.get_text(" ", strip=True)

        # external website
        ext = soup.find("a", href=lambda x: x and x.startswith("http") and "firmenabc" not in x)
        if ext:
            website = ext.get("href", "")

        # FirmenABC (Crefo block) targeted selectors provided by user
        crefo_address_selector = r"#crefo > div.max-w-215.grid.grid-cols-7.gap-x-2\.5.lg\:gap-y-2\.5.mb-16.pt-5.md\:pt-0.\[\&_a\]\:underline > div:nth-child(5)"
        crefo_vat_selector = r"#crefo > div.max-w-215.grid.grid-cols-7.gap-x-2\.5.lg\:gap-y-2\.5.mb-16.pt-5.md\:pt-0.\[\&_a\]\:underline > div:nth-child(9)"
        crefo_description_selector = r"#crefo > div.max-w-215.grid.grid-cols-7.gap-x-2\.5.lg\:gap-y-2\.5.mb-16.pt-5.md\:pt-0.\[\&_a\]\:underline > div:nth-child(13)"
        crefo_directors_selector = r"#crefo > div.max-w-215.grid.grid-cols-7.gap-x-2\.5.lg\:gap-y-2\.5.mb-16.pt-5.md\:pt-0.\[\&_a\]\:underline > div:nth-child(18)"
        crefo_shareholders_selector = r"#crefo > div.max-w-215.grid.grid-cols-7.gap-x-2\.5.lg\:gap-y-2\.5.mb-16.pt-5.md\:pt-0.\[\&_a\]\:underline > div:nth-child(20)"
        website_selector = r"#main-content > div > div.fluid-container-xl.max-2xl\:\!px-0 > div.mb-4.sm\:mb-12.lg\:mb-18 > div > div.flex.flex-col.gap-2 > div.overflow-hidden > div > div.xs\:col-span-2.order-4.col-span-4.sm\:col-span-4.xl\:col-span-3 > p.mb-0.overflow-hidden.text-ellipsis > a"

        # Website: take explicit selector first, then fallback to external link, then infer from email domain
        website_href = self._selenium_get_attr_by_css(driver, website_selector, "href")
        if website_href:
            website = website_href

        addr_text = self._selenium_get_text_by_css(driver, crefo_address_selector)
        if addr_text:
            street, zip_code, city = self._split_address(addr_text)

        desc_text = self._selenium_get_text_by_css(driver, crefo_description_selector)
        if desc_text:
            description = desc_text
        else:
            p = soup.find("p")
            if p:
                description = p.get_text(" ", strip=True)

        vat_text = self._selenium_get_text_by_css(driver, crefo_vat_selector)
        if vat_text:
            vat_id = self._extract_vat_id_from_text(vat_text)
        if not vat_id:
            vat_id = self._extract_vat_id(soup)

        directors_text = self._selenium_get_text_by_css(driver, crefo_directors_selector)
        if directors_text:
            managing_directors = self._extract_names_from_block(directors_text)
        else:
            managing_directors = self._extract_people_list(
                soup,
                labels=(
                    "geschäftsführer",
                    "geschaeftsfuehrer",
                    "managing director",
                    "management",
                    "vertretungsbefugt",
                ),
            )

        shareholders_text = self._selenium_get_text_by_css(driver, crefo_shareholders_selector)
        if shareholders_text:
            shareholders = self._extract_names_from_block(shareholders_text)
        else:
            shareholders = self._extract_people_list(
                soup,
                labels=(
                    "gesellschafter",
                    "shareholder",
                    "inhaber",
                    "owner",
                    "beteiligung",
                ),
            )

        if not website and email and "@" in email:
            domain = email.split("@", 1)[1].strip().strip("/ ")
            if domain:
                website = "https://" + domain

        phone = self._normalize_phone(phone)

        if not street and not zip_code and not city:
            addr = soup.find("address")
            if addr:
                street, zip_code, city = self._split_address(addr.get_text(" ", strip=True))
            else:
                addr2 = soup.find(class_=lambda x: x and "address" in str(x).lower())
                if addr2:
                    street, zip_code, city = self._split_address(addr2.get_text(" ", strip=True))

        # If selector-based extraction didn't work, use the fallback.
        if not managing_directors:
            managing_directors = self._extract_people_list(
                soup,
                labels=(
                    "geschäftsführer",
                    "geschaeftsfuehrer",
                    "managing director",
                    "management",
                    "vertretungsbefugt",
                ),
            )

        if not shareholders:
            shareholders = self._extract_people_list(
                soup,
                labels=(
                    "gesellschafter",
                    "shareholder",
                    "inhaber",
                    "owner",
                    "beteiligung",
                ),
            )

        return {
            "name": name.strip(),
            "street": street.strip(),
            "zip": zip_code.strip(),
            "city": city.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "website": website.strip(),
            "vat_id": vat_id.strip(),
            "description": description.strip(),
            "managing_directors": managing_directors.strip(),
            "shareholders": shareholders.strip(),
            "company_url": company_url,
        }

    def _is_allowed_company_name(self, name):
        n = (name or "").lower()
        if not n:
            return False

        # Requested legal forms:
        # - GmbH
        # - Gesellschaft m.b.H
        # - GmbH & Co. KG
        # - e.U.
        # - OG
        allowed_tokens = (
            "gmbh & co. kg",
            "gmbh & co kg",
            "gmbh",
            "gesellschaft m.b.h",
            "gesellschaft m. b. h",
            "gesellschaft mbh",
            " e.u.",
            "e.u.",
            " og",
            "og ",
            "(og)",
        )

        return any(tok in n for tok in allowed_tokens)

    def _has_valid_vat(self, vat_id):
        v = (vat_id or "").strip().upper()
        return bool(re.fullmatch(r"ATU\d{8}", v))

    def _normalize_phone(self, phone):
        p = (phone or "").strip()
        if not p:
            return ""

        # Common normalizations:
        # - remove spaces, parentheses, dashes
        # - keep leading +
        p = p.replace("(0)", "")
        p = re.sub(r"[\s\-()\/]+", "", p)

        if p.startswith("00"):
            p = "+" + p[2:]

        # If it starts with 0 and looks like a local AT number, convert to +43...
        if p.startswith("0") and not p.startswith("+0"):
            # best-effort, won't be perfect for all formats
            p = "+43" + p[1:]

        return p

    def _selenium_get_text_by_css(self, driver, selector):
        try:
            from selenium.webdriver.common.by import By
        except Exception:
            return ""

        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            return (el.text or "").strip()
        except Exception:
            return ""

    def _selenium_get_attr_by_css(self, driver, selector, attr):
        try:
            from selenium.webdriver.common.by import By
        except Exception:
            return ""

        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            return (el.get_attribute(attr) or "").strip()
        except Exception:
            return ""

    def _extract_vat_id_from_text(self, text):
        text = text or ""
        m = re.search(r"\bATU\d{8}\b", text, flags=re.IGNORECASE)
        if m:
            return m.group(0).upper()
        return ""

    def _split_address(self, address_text):
        text = re.sub(r"\s+", " ", (address_text or "").strip())
        if not text:
            return "", "", ""

        # Typical formats:
        #   "Street 1, 1234 City" or "Street 1 1234 City"
        m = re.search(r"\b(\d{4,5})\b\s+(.+)$", text)
        if m:
            zip_code = m.group(1)
            city = (m.group(2) or "").strip(" ,")
            street = text[: m.start(1)].strip(" ,")
            return street, zip_code, city

        return text, "", ""

    def _extract_names_from_block(self, text):
        # A Crefo block often contains a small table-like text.
        # We extract the first "wordy" part of each non-empty line.
        raw_lines = [re.sub(r"\s+", " ", ln).strip() for ln in (text or "").splitlines()]
        raw_lines = [ln for ln in raw_lines if ln]
        if not raw_lines:
            return ""

        names = []
        for ln in raw_lines:
            # Cut off obvious metadata after separators
            ln = re.split(r"\s{2,}|\t|\|", ln, maxsplit=1)[0].strip()
            ln = ln.strip("-:;,")
            if not ln:
                continue
            # Avoid adding label-like lines
            if any(k in ln.lower() for k in ("geschäftsführer", "gesellschafter", "shareholder", "inhaber")):
                continue
            names.append(ln)

        names = list(dict.fromkeys(names))
        return "; ".join(names)

    def _extract_vat_id(self, soup):
        text = soup.get_text("\n", strip=True)
        if not text:
            return ""

        m = re.search(r"\bATU\d{8}\b", text, flags=re.IGNORECASE)
        if m:
            return m.group(0).upper()

        return ""

    def _extract_people_list(self, soup, *, labels):
        label_set = tuple(l.lower() for l in labels)

        def normalize(s):
            return re.sub(r"\s+", " ", (s or "").strip())

        def contains_label(s):
            s = (s or "").lower()
            return any(lbl in s for lbl in label_set)

        # Strategy 1: find an element that looks like a section header and read the next list/table.
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
            title = normalize(tag.get_text(" ", strip=True))
            if not title or not contains_label(title):
                continue

            container = tag.parent if tag.parent else tag

            ul = container.find_next(["ul", "ol"])
            if ul:
                items = [normalize(li.get_text(" ", strip=True)) for li in ul.find_all("li")]
                items = [i for i in items if i]
                if items:
                    return "; ".join(items)

            table = container.find_next("table")
            if table:
                values = []
                for tr in table.find_all("tr"):
                    cells = [normalize(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
                    cells = [c for c in cells if c]
                    if not cells:
                        continue
                    if len(cells) == 1:
                        values.append(cells[0])
                    else:
                        values.append(" ".join(cells))
                values = [v for v in values if v]
                if values:
                    return "; ".join(values)

        # Strategy 2: find rows where left side contains the label.
        candidates = []
        for tr in soup.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) < 2:
                continue
            key = normalize(tds[0].get_text(" ", strip=True))
            if not key or not contains_label(key):
                continue
            value = normalize(tds[1].get_text(" ", strip=True))
            if value:
                candidates.append(value)
        if candidates:
            return "; ".join(dict.fromkeys(candidates))

        # Strategy 3: scan definition lists.
        for dl in soup.find_all("dl"):
            dts = dl.find_all("dt")
            for dt in dts:
                key = normalize(dt.get_text(" ", strip=True))
                if not key or not contains_label(key):
                    continue
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue
                value = normalize(dd.get_text(" ", strip=True))
                if value:
                    return value

        return ""

    def _deduplicate_by_name(self, companies):
        seen = set()
        out = []
        for c in companies:
            key = (c.get("name") or "").strip().lower()
            if not key:
                continue
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out
