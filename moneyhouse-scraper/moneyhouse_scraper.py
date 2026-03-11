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

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# Konstanten
BASE_URL = "https://www.moneyhouse.ch"
SESSION_FILE = "session.json"
DEFAULT_TIMEOUT = 30000  # 30 Sekunden


class MoneyhouseScraper:
    """Scraper für Moneyhouse.ch"""
    
    def __init__(self, email: str, password: str, headless: bool = False):
        self.email = email
        self.password = password
        self.headless = headless
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
            
    async def _take_screenshot(self, name: str):
        """Mache Screenshot für Debugging"""
        try:
            screenshot_path = f"screenshot_{name}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot gespeichert: {screenshot_path}")
        except Exception as e:
            print(f"Screenshot fehlgeschlagen: {e}")

    async def _do_login(self):
        """Führe Login-Prozess durch"""
        print("Login erforderlich...")
        
        await self.page.goto(f"{BASE_URL}/", wait_until='networkidle')
        await self._random_delay(1000, 2000)
        await self._take_screenshot("01_startpage")

        await self._take_screenshot("02_before_login_click")

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
            
        await self._take_screenshot("03_login_page")
        
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
        
        await self._take_screenshot("04_after_login_submit")
        
        # Prüfe ob Login erfolgreich
        if await self._is_logged_in():
            print("Login erfolgreich!")
            await self._save_session()
            await self._take_screenshot("05_login_success")
        else:
            await self._take_screenshot("05_login_failed")
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

    async def _extract_company_details(self, url: str) -> dict:
        """Extrahiere Firmendetails von Detailseite"""
        print(f"Extrahiere Details von: {url}")
        
        # Bestehende Seite verwenden (kein neuer Tab — Session bleibt erhalten)
        await self.page.goto(url, wait_until='networkidle')
        await self._random_delay(1000, 1500)
        new_page = self.page  # Alias für den restlichen Code

        try:
            data = {
                "Firmenname": None,
                "Strasse": None,
                "Hausnummer": None,
                "Postleitzahl": None,
                "Ort": None,
                "AnzahlMitarbeitende": None,
                "Umsatz": None,
                "Zeichnungsberechtigte": [],
                "Rechtsform": None,
                "MWSTNr": None,
                "Branche": None,
                "Firmenzweck": None,
                "ListeZweigniederlassungen": []
            }
            
            # Alle h4.key + Wert-Paare extrahieren.
            # Struktur: h4.key → optional leeres div.section--small → span/p mit Wert
            pairs = await new_page.evaluate("""() => {
                const result = {};
                document.querySelectorAll('h4.key').forEach(h4 => {
                    const key = h4.textContent.trim();
                    let sibling = h4.nextElementSibling;
                    // Leere section--small Divs überspringen (Paywall-Platzhalter)
                    while (sibling && sibling.classList.contains('section--small') && !sibling.textContent.trim()) {
                        sibling = sibling.nextElementSibling;
                    }
                    if (sibling) result[key] = sibling.textContent.trim();
                });
                return result;
            }""")

            # Firmenname
            try:
                data["Firmenname"] = (await new_page.locator('h1').first.text_content()).strip()
            except Exception:
                pass

            # Strukturierte Felder direkt aus h4.key/p.value
            data["Rechtsform"] = pairs.get("Rechtsform") or None
            data["MWSTNr"] = pairs.get("UID/MWST") or None
            data["Branche"] = pairs.get("Branche") or None
            data["Firmenzweck"] = pairs.get("Firmenzweck") or None

            # Ort aus "Rechtssitz der Firma" (z.B. "Weiningen (ZH)" oder "8173 Neerach")
            sitz = pairs.get("Rechtssitz der Firma", "")
            if sitz:
                plz_match = re.match(r'(\d{4})\s+(.+)', sitz)
                if plz_match:
                    data["Postleitzahl"] = plz_match.group(1)
                    data["Ort"] = plz_match.group(2).strip()
                else:
                    data["Ort"] = re.sub(r'\s*\([^)]+\)', '', sitz).strip()

            data["AnzahlMitarbeitende"] = self._parse_int(pairs.get("Mitarbeiter", ""))
            data["Umsatz"] = self._parse_int(pairs.get("Umsatz in CHF", ""))
            data["Postleitzahl"] = self._parse_int(data.get("Postleitzahl"))

            # Zeichnungsberechtigte aus "neuste Zeichnungsberechtigte" (komma-getrennte Namen)
            zb_text = pairs.get("neuste Zeichnungsberechtigte", "")
            if zb_text:
                for name in [n.strip() for n in zb_text.split(',') if n.strip()]:
                    parts = name.split()
                    if len(parts) >= 2:
                        data["Zeichnungsberechtigte"].append({
                            "Vorname": parts[0],
                            "Name": ' '.join(parts[1:]),
                            "Funktion": "Zeichnungsberechtigt"
                        })

            # Zweigniederlassungen — nur echte Firmennamen, nicht CTA-Links
            branches = await new_page.evaluate("""() => {
                const h2 = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.includes('Zweigniederlassung'));
                if (!h2) return [];
                const container = h2.nextElementSibling || h2.parentElement;
                const ignore = new Set(['Mehr erfahren', 'Jetzt kostenlos abrufen', 'Mehr anzeigen']);
                return Array.from(container.querySelectorAll('a[href*=\"/de/company/\"]'))
                    .map(a => a.textContent.trim())
                    .filter(name => name.length > 3 && !ignore.has(name));
            }""")
            data["ListeZweigniederlassungen"] = branches

            return data

        except Exception as e:
            print(f"Fehler bei Extraktion: {e}")
            return None


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
    parser.add_argument('--email', required=True, help='E-Mail-Adresse für Moneyhouse-Login')
    parser.add_argument('--password', required=True, help='Passwort für Moneyhouse-Login')
    parser.add_argument('--headless', action='store_true', help='Browser im Hintergrund ausführen')
    parser.add_argument('-o', '--output', default='output.json', help='Ausgabedatei (Standard: output.json)')
    
    args = parser.parse_args()
    
    print(f"Moneyhouse Scraper gestartet...")
    print(f"Suchbegriff: {args.search_term}")
    print(f"Headless-Modus: {args.headless}")
    print(f"Output-Datei: {args.output}")
    print("-" * 50)
    
    async with MoneyhouseScraper(args.email, args.password, args.headless) as scraper:
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