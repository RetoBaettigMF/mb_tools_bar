# Moneyhouse Scraper

CLI-Tool in Python zum automatisierten Auslesen von Firmeninformationen von [moneyhouse.ch](https://www.moneyhouse.ch) via Playwright.

## Features

- Login mit Session-Persistenz (`session.json`)
- Automatische Cookie-Banner-Behandlung (consentmanager.net)
- Firmensuche mit stopwort-bewusster Namenszuordnung
- Extraktion aller verfügbaren Firmendetails (Handelsregister, Kennzahlen, Zeichnungsberechtigte)
- Numerische Felder werden automatisch in `int` umgewandelt; Bereiche (z.B. `20-49`) ergeben den gerundeten Mittelwert
- JSON-Output (Konsole + Datei)
- Anti-Bot-Massnahmen (zufällige Verzögerungen, realistischer User-Agent)

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
chmod +x moneyhouse_scraper.py
```

## Verwendung

```bash
# Browser sichtbar (Standard, empfohlen für erste Tests)
./moneyhouse_scraper.py "Cudos AG" --email user@example.com --password geheim

# Headless-Modus
./moneyhouse_scraper.py "Cudos AG" --email user@example.com --password geheim --headless

# Eigene Output-Datei
./moneyhouse_scraper.py "Cudos AG" --email user@example.com --password geheim -o cudos.json
```

## Parameter

| Parameter | Beschreibung | Pflicht |
|-----------|--------------|---------|
| `search_term` | Firmenname (z.B. `"Cudos AG"`) | Ja |
| `--email` | Moneyhouse Login-E-Mail | Ja |
| `--password` | Moneyhouse Passwort | Ja |
| `--headless` | Browser im Hintergrund ausführen | Nein |
| `-o, --output` | Output-Datei (Standard: `output.json`) | Nein |

## Output-Format

```json
{
  "search_term": "Cudos AG",
  "results_count": 2,
  "companies": [
    {
      "Firmenname": "Cudos AG",
      "Strasse": null,
      "Hausnummer": null,
      "Postleitzahl": null,
      "Ort": "Weiningen",
      "AnzahlMitarbeitende": 35,
      "Umsatz": null,
      "Zeichnungsberechtigte": [
        {
          "Vorname": "Rachel",
          "Name": "Blaser",
          "Funktion": "Zeichnungsberechtigt"
        }
      ],
      "Rechtsform": "Aktiengesellschaft",
      "MWSTNr": "CHE-100.618.212",
      "Branche": "Erbringen von IT-Dienstleistungen",
      "Firmenzweck": "Die Gesellschaft bezweckt ...",
      "ListeZweigniederlassungen": [
        "Cudos AG, Zweigniederlassung Chur"
      ]
    }
  ]
}
```

### Hinweise zu Feldern

- `Strasse` / `Hausnummer`: Nicht strukturiert im Handelsregister verfügbar — bleibt `null`
- `Postleitzahl` / `Ort`: Aus dem Rechtssitz extrahiert; PLZ nur wenn im Format `XXXX Ort` angegeben
- `AnzahlMitarbeitende` / `Umsatz`: Erfordern Premium-Account; bei Bereichen (z.B. `20-49`) wird der gerundete Mittelwert zurückgegeben
- `Zeichnungsberechtigte`: Basiert auf «neuste Zeichnungsberechtigte» aus dem Handelsregister

## Session-Management

Nach erfolgreichem Login wird `session.json` angelegt. Beim nächsten Aufruf wird die Session automatisch wiederverwendet.

Session zurücksetzen (z.B. nach Passwortänderung oder bei abgelaufener Session):

```bash
rm session.json
```

## Abhängigkeiten

- Python 3.9+
- `playwright` (siehe `requirements.txt`)
