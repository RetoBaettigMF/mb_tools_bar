#!/usr/bin/env python3
"""
sales_report — Sales-Report aus CRM → Google Sheet

Holt alle offenen Potentiale (sales_stage leer/null), summiert das gewichtete
Potential (cf_659) und die Anzahl pro Mitarbeitenden und schreibt je eine Zeile
in die Google-Sheet-Tabs «Summen» und «Anzahl».

Usage:
  sales_report.py
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SHEET_ID = "1ZpOfJDWRGm61MqUOgch6n4B0Ziia5ShbH1STlF18d1k"
CRM_TOOL = Path(__file__).parent.parent / "crm-rest" / "crm_tool.py"

# Reihenfolge der Spalten im Sheet (ohne "Datum", das wird separat vorangestellt)
COLUMN_ORDER = [
    "Riccardo Gubser",
    "Reto Bättig",
    "Adrian Kohlbrenner",
    "Christian Hecht",
    "Bruno Knöpfel",
    "Rachel Blaser",
    "Public",
    "Marianne Petitpierre",
    "Ruth Bopp",
    "Sibille Hablützel",
    "Cudos Gast",
]

USER_LOOKUP = {
    "19x17725": "Riccardo Gubser",
    "19x1":     "Administrator",
    "19x7":     "Reto Bättig",
    "19x17312": "Rachel Blaser",
    "19x17731": "Ruth Bopp",
    "19x17730": "Sibille Hablützel",
    "19x17729": "Christian Hecht",
    "19x17310": "Bruno Knöpfel",
    "19x17732": "Adrian Kohlbrenner",
    "19x17736": "Cudos Gast",
    "19x17735": "Marianne Petitpierre",
    "19x17734": "Public",
}

# ---------------------------------------------------------------------------
# CRM helpers
# ---------------------------------------------------------------------------

def crm_query(sql: str) -> list:
    """Führt ein SQL-Query via crm_tool.py aus und gibt die Ergebnisliste zurück."""
    result = subprocess.run(
        [sys.executable, str(CRM_TOOL), "query", sql],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"CRM-Fehler: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"JSON-Parse-Fehler: {e}\nOutput: {result.stdout}", file=sys.stderr)
        sys.exit(1)


def fetch_all_potentials() -> list:
    """Holt alle Potentiale seitenweise (je 100) bis keine mehr zurückkommen."""
    all_records = []
    offset = 0
    while True:
        sql = (
            f"select assigned_user_id, cf_659 from Potentials "
            f"where sales_stage = '' or sales_stage is null "
            f"limit {offset},100"
        )
        page = crm_query(sql)
        if not page:
            break
        all_records.extend(page)
        if len(page) < 100:
            break
        offset += 100
    return all_records


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate(potentials: list) -> tuple[dict, dict]:
    """Gibt (summen, anzahl) dicts zurück, Keys sind Mitarbeitenden-Namen."""
    summen: dict[str, float] = {}
    anzahl: dict[str, int] = {}

    for p in potentials:
        uid = p.get("assigned_user_id", "")
        name = USER_LOOKUP.get(uid, f"Unbekannt ({uid})")

        raw = p.get("cf_659") or "0"
        try:
            wert = float(raw)
        except (ValueError, TypeError):
            wert = 0.0

        summen[name] = summen.get(name, 0.0) + wert
        anzahl[name] = anzahl.get(name, 0) + 1

    return summen, anzahl


# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------

def sheets_append(tab: str, row_values: list) -> None:
    """Fügt eine Zeile an den angegebenen Sheet-Tab an."""
    range_notation = f"{tab}!A:L"
    row_str = " | ".join(str(v) for v in row_values)
    result = subprocess.run(
        ["gog", "sheets", "append", SHEET_ID, range_notation, row_str],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Sheets-Fehler ({tab}): {result.stderr}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Lade Potentiale aus CRM …")
    potentials = fetch_all_potentials()
    print(f"  {len(potentials)} Potentiale gefunden.")

    summen, anzahl = aggregate(potentials)

    today = date.today().isoformat()

    # Zeile Summen
    summen_row = [today] + [summen.get(name, 0.0) for name in COLUMN_ORDER]
    print("\nSchreibe Summen ins Sheet …")
    sheets_append("Summen", summen_row)

    # Zeile Anzahl
    anzahl_row = [today] + [anzahl.get(name, 0) for name in COLUMN_ORDER]
    print("Schreibe Anzahl ins Sheet …")
    sheets_append("Anzahl", anzahl_row)

    # Zusammenfassung
    print("\n=== Zusammenfassung ===")
    print(f"{'Mitarbeitende':<25} {'Anzahl':>7} {'Summe gewichtet':>17}")
    print("-" * 53)
    for name in COLUMN_ORDER:
        n = anzahl.get(name, 0)
        s = summen.get(name, 0.0)
        if n > 0:
            print(f"{name:<25} {n:>7}   {s:>15.2f}")

    # Unbekannte / Administrator (nicht im Sheet, aber in der Konsole)
    extras = {k: v for k, v in anzahl.items() if k not in COLUMN_ORDER}
    if extras:
        print("\nNicht im Sheet (Administrator / Unbekannte):")
        for name, n in extras.items():
            s = summen.get(name, 0.0)
            print(f"  {name:<25} {n:>7}   {s:>15.2f}")

    total_n = sum(anzahl.values())
    total_s = sum(summen.values())
    print("-" * 53)
    print(f"{'Total':<25} {total_n:>7}   {total_s:>15.2f}")
    print(f"\nSheet-Zeilen erfolgreich geschrieben ({today}).")


if __name__ == "__main__":
    main()
