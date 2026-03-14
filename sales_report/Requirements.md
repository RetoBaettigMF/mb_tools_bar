# Sales-Report

Dieses Tool erstellt einen Sales-Report aus dem CRM und schreibt die Resultate in ein Google Sheet.

# Anforderungen
- Command line tool in python
- Rufe command-line tools auf für CRM, Google Sheet
- Rufe alle Potentiale auf mit folgender Logik
  - ./crm_tool.py query "select assigned_user_id, cf_659 from Potentials where sales_stage = '' or sales_stage is null limit 0,100"
  - Es werden maximal 100 Potentiale zurückgegeben, hole die nächsten Pages, bis du alle Potentiale hast
- Weise die Potentiale Mitarbeitenden zu nach folgender Lookup-Table:
```
19x17725: Riccardo Gubser
19x1: Administrator
19x7: Reto Bättig
19x17312: Rachel Blaser
19x17731: Ruth Bopp
19x17730: Sibille Hablützel
19x17729: Christian Hecht
19x17310: Bruno Knöpfel
19x17732: Adrian Kohlbrenner
19x17736: Cudos Gast
19x17735: Marianne Petitpierre
19x17734: Public
```
- Summiere das gewichtete Potential aus dem Feld cf_659 für jeden Mitarbeitenden
- Zähle die Anzahl Potentiale für jeden Mitarbeitenden
- Füge eine Zeile an das Google Sheet an mit der Summe der gewichteten Potentiale in genau der vorgegebenen Spaltenreihenfolge:
gog sheets append 1ZpOfJDWRGm61MqUOgch6n4B0Ziia5ShbH1STlF18d1k 'Summen!A:L' 'Datum | Riccardo Gubser | Reto Bättig | Adrian Kohlbrenner | Christian Hecht | Bruno Knöpfel | Rachel Blaser | Public | Marianne Petitpierre | Ruth Bopp | Sibille Hablützel | Cudos Gast'
- Füge eine Zeile an's google Sheet an und fülle die anzahl Potentiale pro person genau in der vorgegebenen Spaltenreihenfolge ein:
  gog sheets append 1ZpOfJDWRGm61MqUOgch6n4B0Ziia5ShbH1STlF18d1k 'Anzahl!A:L' 'Datum |Riccardo Gubser | Reto Bättig | Adrian Kohlbrenner | Christian Hecht | Bruno Knöpfel | Rachel Blaser | Public | Marianne Petitpierre | Ruth Bopp | Sibille Hablützel | Cudos Gast'
- Gib eine Zusammenfassung der Resultate auf der Kommandozeile zurück