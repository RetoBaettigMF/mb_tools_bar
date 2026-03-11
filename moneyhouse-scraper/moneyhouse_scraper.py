#!/usr/bin/env python3
"""
Moneyhouse Web Scraper

Ein CLI-Tool zum automatisierten Scrapen von Firmeninformationen
von moneyhouse.ch mittels Playwright.
"""

import argparse
import asyncio
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# Konstanten
BASE_URL = "https://www.moneyhouse.ch"
SESSION_FILE = "session.json"
DEFAULT_TIMEOUT = 30000  # 30 Sekunden
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.0-flash-001"


class MoneyhouseScraper:
    """Scraper für Moneyhouse.ch"""
    
    def __init__(self, email: str, password: str, headless: bool = False,
                 openrouter_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.email = email
        self.password = password
        self.headless = headless
        self.openrouter_key = openrouter_key
        self.model = model
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """Async Context Manager Entry"""
        self.playwright = await async_playwright().start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async Context Manager Exit"""
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()
        
    async def _random_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Zufällige Verzögerung zur Vermeidung von Bot-Erkennung"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
        
    async def _load_session(self) -> bool:
        """Lade vorhandene Session aus Datei"""
        session_path = Path(SESSION_FILE)
        if session_path.exists():
            try:
                print(f"Lade bestehende Session aus {SESSION_FILE}...")
                return True
            except Exception:
                pass
        return False
        
    async def _save_session(self):
        """Speichere aktuelle Session in Datei"""
        if self.context:
            await self.context.storage_state(path=SESSION_FILE)
            print(f"Session gespeichert in {SESSION_FILE}")
            
    async def _init_browser(self):
        """Initialisiere Browser und Context"""
        session_exists = await self._load_session()
        
        storage_state = SESSION_FILE if session_exists else None
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            storage_state=storage_state,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0'
        )

        # Cookie-Banner (#cmpbox / #cmpbox2) dauerhaft unterdrücken.
        # Visuell sofort verstecken; Consent-Klick erst nach kurzer Wartezeit,
        # damit CMP-JS Zeit hat sich zu initialisieren (sonst kein echter Consent).
        await self.context.add_init_script("""
            var _cmpClicked = false;
            var _cmpStart = Date.now();
            setInterval(function() {
                var b = document.getElementById('cmpbox');
                var b2 = document.getElementById('cmpbox2');
                if (b) b.style.cssText = 'display:none!important;pointer-events:none!important;visibility:hidden!important;';
                if (b2) b2.style.cssText = 'display:none!important;pointer-events:none!important;visibility:hidden!important;';
                // Erst nach 1.5s klicken — CMP braucht Zeit zur Initialisierung
                if (!_cmpClicked && (Date.now() - _cmpStart) > 1500) {
                    var btn = document.getElementById('cmpbntyes');
                    if (btn) { btn.click(); _cmpClicked = true; }
                }
            }, 300);
        """)

        self.page = await self.context.new_page()
        self.page.set_default_timeout(DEFAULT_TIMEOUT)
        
    async def _is_logged_in(self) -> bool:
        """Prüfe ob Benutzer eingeloggt ist.

        Navigiert zur Account-Seite: eingeloggte User bleiben dort,
        nicht-eingeloggte werden zur Login-Seite weitergeleitet.
        """
        try:
            await self.page.goto(f"{BASE_URL}/account/overview", wait_until='networkidle')
            return '/login' not in self.page.url
        except Exception:
            return False
            
    async def _do_login(self):
        """Führe Login-Prozess durch"""
        print("Login erforderlich...")
        
        await self.page.goto(f"{BASE_URL}/", wait_until='networkidle')
        await self._random_delay(1000, 2000)

        # Klicke auf "Anmelden"
        login_selectors = [
            'a:has-text("Anmelden")',
            'text=Anmelden',
            'a[href*="/login"]',
            'button:has-text("Anmelden")',
        ]
        
        login_clicked = False
        for selector in login_selectors:
            try:
                login_link = await self.page.wait_for_selector(selector, timeout=5000)
                if login_link:
                    await login_link.click(force=True)
                    await self._random_delay(1000, 2000)
                    login_clicked = True
                    break
            except Exception:
                continue
                
        if not login_clicked:
            # Direkt zur Login-Seite gehen
            await self.page.goto(f"{BASE_URL}/login", wait_until='networkidle')
            await self._random_delay(1000, 2000)
            
        # Warte auf Login-Formular
        await self.page.wait_for_load_state('networkidle')
        
        # Fülle Login-Formular aus
        email_filled = False
        try:
            await self.page.fill('input[type="email"]', self.email)
            email_filled = True
        except Exception:
            # Versuche andere Selektoren
            try:
                await self.page.fill('input[name*="email"]', self.email)
                email_filled = True
            except Exception:
                try:
                    await self.page.fill('input[name*="user"]', self.email)
                    email_filled = True
                except Exception:
                    pass
                    
        if not email_filled:
            raise Exception("Konnte E-Mail-Feld nicht finden")
            
        await self._random_delay(500, 1000)
        
        password_filled = False
        try:
            await self.page.fill('input[type="password"]', self.password)
            password_filled = True
        except Exception:
            try:
                await self.page.fill('input[name*="password"]', self.password)
                password_filled = True
            except Exception:
                pass
                
        if not password_filled:
            raise Exception("Konnte Passwort-Feld nicht finden")
            
        await self._random_delay(500, 1000)
        
        # Sende Formular — Login-Seite nutzt input[type="submit"], kein <button>
        submit_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            'button:has-text("Anmelden")',
        ]

        for selector in submit_selectors:
            try:
                submit_btn = await self.page.wait_for_selector(selector, timeout=3000)
                if submit_btn:
                    await submit_btn.click(force=True)
                    break
            except Exception:
                continue
                
        # Warte auf Login-Abschluss
        await self.page.wait_for_load_state('networkidle')
        await self._random_delay(2000, 3000)

        # Prüfe ob Login erfolgreich
        if await self._is_logged_in():
            print("Login erfolgreich!")
            await self._save_session()
        else:
            raise Exception("Login fehlgeschlagen - bitte Zugangsdaten prüfen")
            
    async def login(self):
        """Login-Handler mit Session-Support"""
        await self._init_browser()
        
        # Prüfe ob bereits eingeloggt
        await self.page.goto(f"{BASE_URL}/", wait_until='networkidle')
        await self._random_delay(1000, 2000)

        if await self._is_logged_in():
            print("Bereits eingeloggt (Session gültig)")
        else:
            await self._do_login()
            
    async def search_company(self, search_term: str) -> list:
        """Suche nach Firma und extrahiere Details"""
        print(f"Suche nach: {search_term}")
        
        # Navigiere zur Suche
        await self.page.goto(f"{BASE_URL}/", wait_until='networkidle')
        await self._random_delay(1000, 2000)
        
        # Finde Suchfeld — es gibt zwei input[name="q"], das erste ist hidden.
        # Locator mit visible-Filter nimmt das sichtbare.
        search_locator = self.page.locator('input[name="q"]').filter(visible=True).first
        try:
            await search_locator.wait_for(state='visible', timeout=10000)
        except Exception:
            raise Exception("Suchfeld nicht gefunden")

        # Eingabe Suchbegriff
        await search_locator.fill(search_term)
        await self._random_delay(500, 1000)
        
        # Sende Suche
        await search_locator.press('Enter')
        await self.page.wait_for_load_state('networkidle')

        # Resultate laden per AJAX nach networkidle — auf Company-Links warten
        try:
            await self.page.wait_for_selector('a[href*="/de/company/"]', timeout=15000)
        except Exception:
            print("Keine Firmen-Links gefunden")
            return []

        results = []
        result_links = []
        links = await self.page.query_selector_all('a[href*="/de/company/"]')
        for link in links:
            href = await link.get_attribute('href')
            title = await link.text_content()
            if not href or not title:
                continue
            # Nur direkte Firmen-Seiten, keine Unterseiten (/brands, /persons etc.)
            path = href.split('?')[0]
            if path.count('/') > 3:
                continue
            if self._name_matches(search_term, title.strip()):
                full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                result_links.append({'url': full_url, 'title': title.strip()})
                
        print(f"Gefunden: {len(result_links)} passende Resultate")
        
        # Verarbeite jedes Resultat
        for result in result_links[:5]:  # Max 5 Resultate
            try:
                company_data = await self._extract_company_details(result['url'])
                if company_data:
                    results.append(company_data)
            except Exception as e:
                print(f"Fehler beim Extrahieren von {result['url']}: {e}")
                continue
                
        return results
        
    def _name_matches(self, search_term: str, result_name: str) -> bool:
        """Prüfe ob Resultat-Name mit Suchbegriff übereinstimmt"""
        search_lower = search_term.lower().strip()
        result_lower = result_name.lower().strip()

        # Exakte Übereinstimmung oder Suchbegriff ist im Resultat enthalten
        if search_lower == result_lower or search_lower in result_lower:
            return True

        # Wortweise Übereinstimmung — Gattungsbegriffe ausschliessen
        stopwords = {'ag', 'gmbh', 'sa', 'sarl', 'kg', 'ltd', 'inc', 'und', 'and', '&'}
        search_words = set(search_lower.split()) - stopwords
        result_words = set(result_lower.split()) - stopwords

        if not search_words:
            return False

        # Alle signifikanten Suchwörter müssen im Resultat vorkommen
        return search_words.issubset(result_words)
        
    def _parse_int(self, value: str) -> Optional[int]:
        """Wandle String in int um. Range 'X-Y' → gerundeter Mittelwert."""
        if not value or not re.search(r'\d', value):
            return None
        range_match = re.match(r"(\d[\d'\.]*)\s*[-–]\s*(\d[\d'\.]*)", value)
        if range_match:
            a = int(re.sub(r"[^\d]", "", range_match.group(1)))
            b = int(re.sub(r"[^\d]", "", range_match.group(2)))
            return (a + b + 1) // 2
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else None

    def _call_openrouter(self, page_text: str) -> Optional[dict]:
        """Extrahiere Firmendetails via OpenRouter LLM aus dem sichtbaren Seitentext."""
        system_prompt = """Du extrahierst Firmendetails aus dem sichtbaren Text einer moneyhouse.ch-Seite.

Antworte ausschliesslich mit gültigem JSON (kein Markdown, keine Code-Fences), mit folgender Struktur:

{
  "Firmenname": "string oder null",
  "Strasse": "Strassenname ohne Hausnummer, oder null",
  "Hausnummer": "Hausnummer als string oder null",
  "Postleitzahl": "int oder null — vierstellige Schweizer PLZ",
  "Ort": "string oder null",
  "AnzahlMitarbeitende": "int oder null — bei Bereichen wie '20-49' den Mittelwert (35) angeben",
  "Umsatz": "int oder null — bei Bereichen den Mittelwert angeben",
  "Zeichnungsberechtigte": [
    {"Vorname": "string", "Name": "string", "Funktion": "string — z.B. VR, GL, Zeichnungsberechtigt"}
  ],
  "Rechtsform": "string oder null — z.B. Aktiengesellschaft",
  "MWSTNr": "string oder null — z.B. CHE-123.456.789",
  "Branche": "string oder null",
  "Firmenzweck": "string oder null",
  "ListeZweigniederlassungen": ["string — nur echte Firmennamen, keine CTAs wie 'Mehr anzeigen'"]
}

Hinweise:
- Fehlende Felder → null bzw. []
- Postleitzahl, AnzahlMitarbeitende, Umsatz müssen int sein (nicht string)
- Zeichnungsberechtigte: Funktion aus Kontext ableiten (Verwaltungsrat → VR, Geschäftsleitung → GL, sonst Zeichnungsberechtigt)
- ListeZweigniederlassungen: nur echte Firmennamen, keine Buttons/Links-Texte"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": page_text}
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            # Markdown-Fences entfernen falls vorhanden
            if content.startswith("```"):
                content = re.sub(r'^```[a-z]*\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            data = json.loads(content)
            # Numerische Felder normalisieren
            for field in ("AnzahlMitarbeitende", "Umsatz", "Postleitzahl"):
                if isinstance(data.get(field), str):
                    data[field] = self._parse_int(data[field])
            return data
        except Exception as e:
            print(f"OpenRouter-Fehler: {e}", file=sys.stderr)
            return None

    async def _extract_company_details(self, url: str) -> Optional[dict]:
        """Extrahiere Firmendetails von Detailseite via LLM."""
        print(f"Extrahiere Details von: {url}")

        await self.page.goto(url, wait_until='networkidle')
        await self._random_delay(1000, 1500)

        page_text = await self.page.evaluate("() => document.body.innerText")
        data = await asyncio.to_thread(self._call_openrouter, page_text)
        if data is None:
            return None

        # Numerische Felder als Absicherung nochmals normalisieren
        for field in ("AnzahlMitarbeitende", "Umsatz", "Postleitzahl"):
            if isinstance(data.get(field), str):
                data[field] = self._parse_int(data[field])

        return data


async def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description='Moneyhouse Web Scraper - Extrahiert Firmeninformationen von moneyhouse.ch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Beispiele:
  %(prog)s "Cudos AG" --email user@example.com --password geheim
  %(prog)s "Muster Firma" --email user@example.com --password geheim --headless
        '''
    )
    
    parser.add_argument('search_term', help='Suchbegriff (z.B. "Cudos AG")')
    parser.add_argument('--email', help='E-Mail-Adresse für Moneyhouse-Login (oder MONEYHOUSE_EMAIL env var)')
    parser.add_argument('--password', help='Passwort für Moneyhouse-Login (oder MONEYHOUSE_PASSWORD env var)')
    parser.add_argument('--headless', action='store_true', help='Browser im Hintergrund ausführen')
    parser.add_argument('-o', '--output', default='output.json', help='Ausgabedatei (Standard: output.json)')
    parser.add_argument('--openrouter-key', help='OpenRouter API Key (oder OPENROUTER_API_KEY env var)')
    parser.add_argument('--model', default=DEFAULT_MODEL, help=f'OpenRouter-Modell (Standard: {DEFAULT_MODEL})')

    args = parser.parse_args()

    # .env-Datei laden (falls vorhanden)
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    os.environ.setdefault(k.strip(), v.strip())

    # Zugangsdaten auflösen: CLI-Arg > env var / .env
    openrouter_key = args.openrouter_key or os.environ.get('OPENROUTER_API_KEY')
    email = args.email or os.environ.get('MONEYHOUSE_EMAIL')
    password = args.password or os.environ.get('MONEYHOUSE_PASSWORD')

    if not openrouter_key:
        print("Fehler: OpenRouter API Key fehlt. Setze --openrouter-key oder OPENROUTER_API_KEY.", file=sys.stderr)
        sys.exit(1)
    if not email:
        print("Fehler: E-Mail fehlt. Setze --email oder MONEYHOUSE_EMAIL.", file=sys.stderr)
        sys.exit(1)
    if not password:
        print("Fehler: Passwort fehlt. Setze --password oder MONEYHOUSE_PASSWORD.", file=sys.stderr)
        sys.exit(1)

    print(f"Moneyhouse Scraper gestartet...")
    print(f"Suchbegriff: {args.search_term}")
    print(f"Headless-Modus: {args.headless}")
    print(f"Output-Datei: {args.output}")
    print(f"Modell: {args.model}")
    print("-" * 50)

    async with MoneyhouseScraper(email, password, args.headless,
                                  openrouter_key=openrouter_key, model=args.model) as scraper:
        try:
            # Login
            await scraper.login()
            
            # Suche und Extraktion
            results = await scraper.search_company(args.search_term)
            
            # Speichere Ergebnisse
            output_data = {
                "search_term": args.search_term,
                "results_count": len(results),
                "companies": results
            }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            print(f"\n{'='*50}")
            print(f"Ergebnisse gespeichert in: {args.output}")
            print(f"Gefundene Firmen: {len(results)}")
            print(f"{'='*50}")
            
            # Ausgabe in Konsole
            print("\nExtrahierte Daten:")
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"\nFehler: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())