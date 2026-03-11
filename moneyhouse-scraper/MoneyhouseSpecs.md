# Anforderungsdokument: Playwright Web Scraper für Moneyhouse

## 1. Projektübersicht

Erstellung eines Kommandozeilen-Tools (CLI) in Python, welches mittels der Bibliothek `Playwright` automatisiert Informationen über Firmen von der Webseite `https://www.moneyhouse.ch/` ausliest (Scraping) und als strukturierte JSON-Liste zurückgibt.

## 2. Technologie-Stack

* **Sprache:** Python 3.9+
* **Kern-Bibliothek:** `playwright` (synchronous oder asynchronous API, vorzugsweise `asyncio` mit `async_playwright`)
* **CLI-Parsing:** `argparse` (Standardbibliothek)
* **Datenverarbeitung:** `json`, `os`

## 3. Funktionale Anforderungen

### 3.1. Kommandozeilen-Interface (CLI)

Das Skript muss als CLI-Tool aufrufbar sein und folgende Parameter akzeptieren:

* `search_term`: Der Suchbegriff (z.B. "Cudos AG").
* `--email`: E-Mail-Adresse für das Moneyhouse-Login.
* `--password`: Passwort für das Moneyhouse-Login.
* *Optional:* `--headless` (Flag, um den Browser im Hintergrund auszuführen. Standardmäßig soll er für Debugging-Zwecke sichtbar sein, also `headless=False`).

### 3.2. Session Management & Login

* **Persistenz:** Das Tool muss Cookies und den Local Storage speichern können (z.B. über die Playwright-Funktion `storage_state="session.json"`).
* **Login-Logik:**
1. Beim Start prüft das Skript, ob eine gültige Session-Datei (`session.json`) existiert.
2. Falls *ja*, wird diese geladen und das Login übersprungen.
3. Falls *nein* oder falls die Session abgelaufen ist:
* Navigiere zu `https://www.moneyhouse.ch/`.
* Klicke auf den Menüpunkt "Anmelden".
* Fülle die Felder für E-Mail und Passwort aus den CLI-Argumenten aus.
* Sende das Formular ab und warte, bis der Login erfolgreich war (z.B. durch Warten auf ein Element, das nur im eingeloggten Zustand sichtbar ist).
* Speichere den Status in `session.json`.





### 3.3. Navigation und Such-Logik

* Navigiere nach erfolgreichem Login / Session-Load zur Suchmaske.
* Gib den `search_term` in das Suchfeld ein und löse die Suche aus.
* Warte auf das Laden der Suchresultate.
* Iteriere über die Resultate: Prüfe, ob der Name des Resultats mit dem Suchbegriff übereinstimmt (Toleranz für leichte Abweichungen, wie Groß-/Kleinschreibung, einbauen).
* Klicke bei passenden Resultaten auf den Link, um zur Detailseite der Firma zu gelangen. *(Tipp für den Agenten: Öffne Detailseiten am besten in neuen Tabs/Pages innerhalb des Contexts, um die Suchresultate-Seite nicht zu verlieren).*

### 3.4. Daten-Extraktion (Scraping)

Auf der Detailseite der Firma müssen folgende Daten extrahiert werden (inklusive Parsing-Logik, falls Werte zusammenhängend im HTML stehen):

* `Firmenname`
* `Strasse`
* `Hausnummer`
* `Postleitzahl`
* `Ort`
* `AnzahlMitarbeitende` (Falls eine Spanne angegeben ist, muss der Mittelwert als Zahl berechnet/ausgelesen werden).
* `Umsatz` (Falls eine Spanne angegeben ist, muss der Mittelwert als Zahl berechnet/ausgelesen werden).
* `Zeichnungsberechtigte` (Eine Liste von Objekten, siehe Datenmodell).
* `Rechtsform`
* `MWSTNr`
* `Branche`
* `Firmenzweck`
* `ListeZweigniederlassungen` (Liste von Strings)

### 3.5. Output

Das Skript soll am Ende der Ausführung eine strukturierte JSON-Liste (`[]`) aller gefundenen und extrahierten Firmen in die Konsole ausgeben (`print`) oder optional in eine Datei `output.json` schreiben.

## 4. Datenmodell (Ziel-JSON Struktur)

Das resultierende JSON-Objekt für *eine* Firma muss exakt folgendem Schema entsprechen:

```json
{
  "Firmenname": "String",
  "Strasse": "String",
  "Hausnummer": "String",
  "Postleitzahl": "String",
  "Ort": "String",
  "AnzahlMitarbeitende": 0,    // Numerischer Mittelwert
  "Umsatz": 0,                 // Numerischer Mittelwert
  "Zeichnungsberechtigte": [
    {
      "Name": "String",
      "Vorname": "String",
      "Funktion": "GL"         // Mögliche Werte: "GL", "VR", "Zeichnungsberechtigt", etc.
    }
  ],
  "Rechtsform": "String",
  "MWSTNr": "String",
  "Branche": "String",
  "Firmenzweck": "String",
  "ListeZweigniederlassungen": [
    "String",
    "String"
  ]
}

```

## 5. Nicht-funktionale Anforderungen & Best Practices für den Agenten

* **Robustheit:** Implementiere Timeouts und `try/except`-Blöcke. Falls ein Datenfeld auf der Seite nicht existiert, soll der Wert `null` (in Python `None`) oder eine leere Liste gesetzt werden, anstatt dass das Skript abstürzt.
* **Anti-Bot-Erkennung:** Füge realistische Wartezeiten (Random Delays) zwischen den Klicks ein, um nicht sofort blockiert zu werden.
* **Cookie-Banner:** Implementiere einen Check, um eventuelle Cookie-Zustimmungs-Banner (Consent-Popups) auf der Startseite automatisch wegzuklicken.
