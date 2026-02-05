# Anforderungsdokument: CRM MCP Server (Python & Playwright)
Erstelle einen neuen MCP Server im Verzeichnis ./cudos-crm-mcp
Er bietet eine Schnittstelle zum webbasierten CRM-System der Cudos

## 1. Architektur-Prinzipien

* **Transport:** `stdio` (Standard-Kommunikation für Claude Code).
* **Page Object Model (POM):** Jedes Modul (Contacts, Accounts, Potentials) hat eine eigene Klasse für Selektoren und Logik.
* **Persistent Context:** Speicherung der Session in `./.auth/state.json`.
* **Fuzzy Search:** Retry-Logik (3-5 Versuche) bei unvollständigen Suchbegriffen; keine globale Suche.
* **Datenformat:** Bei Suchfunktionen, rufe immer die Detailseite auf und gib eine Datenstruktur mit sämtlichen vorhandenen Feldern zurück, auch wenn sie leer sind. Bei Schreib- und Update-Funktionen: Ermögliche sämtliche Felder auf der Detailseite zu editieren.

---

## 2. Detaillierte Funktionsliste (Tools)

### A. Such- & Lese-Funktionen

* **`search_account(name, ort)`**: Sucht Firmen in der Listenansicht.
* **`search_person(vorname, nachname, firma)`**: Sucht Personen in der Listenansicht.
* **`search_potential(name, firma, inhaber, status)`**: Sucht Potenziale mit Statusfilter.
* **`get_comments(account_id)`**:
* Öffnet die Detailansicht der Firma (`record=account_id`).
* Extrahiert die **letzten 5 Kommentare** (Inhalt, Autor, Datum).
* Gibt diese als strukturierte Liste zurück.



### B. Erstellungs-Funktionen (mit Dublettenprüfung)

* **`create_account(data_dict)`**: Prüft vorab via `search_account`, ob die Firma existiert.
* **`create_person(firma_id, data_dict)`**: Prüft vorab via `search_person`, ob die Person bei dieser Firma bereits existiert.
* **`create_potential(firma_id, data_dict)`**: Erstellt ein neues Potenzial verknüpft mit der `firma_id`.

### C. Update-Funktionen (Modulspezifisch)

Diese Tools rufen direkt die Edit-Ansicht (`view=Edit&record=ID`) auf und aktualisieren nur die übergebenen Felder:

* **`update_account(account_id, updates_dict)`**
* **`update_person(person_id, updates_dict)`**
* **`update_potential(potential_id, updates_dict)`**

### D. Interaktion

* **`add_comment_to_account(account_id, autor, text)`**: Postet einen neuen Kommentar in der Detailansicht.

### E. Schnittstelle
Steuere einen Browser. Hier noch einige konkrete Hinweise, wie das UI gesteuert werden kann:

- Personensuche nach Name, Vorname, Firma
  - Verwende https://mf250.co.crm-now.de/index.php?module=Contacts&view=List
  - Suche über Eingabe in die Felder "Vorname", "Nachname", "Organisation"
- Firmensuche nach Name, Ort
  - Verwende https://mf250.co.crm-now.de/index.php?module=Accounts&view=List
  - Suche über Eingabe der Fleder "Organisationsname", "Rechnung Ort"
- Potentialsuche nach Name, Firma, Zuständiger Person, Endstatus
  - Verwende https://mf250.co.crm-now.de/index.php?module=Potentials&view=List
  - Suche über Eingabe der Felder "Potentialname", "Organisationsname", "zuständig", "Endstatus" [inaktiv|gewonnen|verloren|gestorben|(leer)]
- Erstellen einer neuen Person (muss immer einer bestehenden Firma hinzugefügt werden)
- Erstellen eines neuen Potentials (muss immer einer bestehenden Firma hinzugefügt werden)
- Erstellen eines neuen Kommentars zu einer Firma:
  - Öffne die Detailansicht der Firma
  - Trage im Editfeld unter "Kommentare" den Kommentar ein inkl. dem Autor und klicke auf "veröffentlichen"
---

## 3. Workflow-Logik für "Intelligente Suche"

Falls ein Suchbegriff (z.B. "Müller*") im Webinterface keine Treffer liefert:

1. Entferne Sonderzeichen (`*`, `?`).
1. Kürze den Begriff schrittweise (z.B. "Mülle", "Müll").
1. Wiederhole die Suche maximal 5-mal.
1. Ersetze die Umlaute (ü->ue etc.) 
1. Gibt es mehrere Treffer, wird eine Liste mit Namen und der `record_id` (aus der URL extrahiert) zurückgegeben.

---

## 4. Implementierungs-Anweisungen für Claude Code

> "Erstelle einen Python MCP Server für das CRM [https://mf250.co.crm-now.de/](https://mf250.co.crm-now.de/).
> **Vorgaben:**
> 1. **Framework:** Python `mcp` SDK, `playwright` (async), `stdio` Transport.
> 2. **Session:** Nutze einen Persistent Context in `./.auth/state.json`.
> 3. **Page Objects:** Erstelle Klassen für `AccountPage`, `ContactPage` und `PotentialPage`.
> 4. **Dubletten-Check:** Vor jedem `create_account` oder `create_person` muss eine Suche erfolgen. Falls Treffer existieren, brich mit einer Fehlermeldung ab.
> 5. **Tools:**
> * `search_account`, `search_person`, `search_potential` (inkl. Fuzzy-Retry-Logik).
> * `update_account`, `update_person`, `update_potential` (via `view=Edit&record=ID`).
> * `create_account`, `create_person` (verknüpft mit Firma), `create_potential`.
> * `add_comment_to_account(account_id, autor, text)`.
> * `get_comments(account_id)`: Extrahiere die letzten 5 Kommentare aus der Detailansicht.
> 6. **Details:** Extrahiere bei Suchergebnissen immer die `record_id` aus den Links. Logs nur nach `sys.stderr`."
> 
