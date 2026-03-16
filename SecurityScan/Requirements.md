# Security Scan

Baue ein Kommandozeilen Tool, welches alle Markdown Dateien in einem Verzeichnis rekursiv durchsucht und nach potenziell unsicheren Inhalten sucht. 

## Allgemeines
Verwende das .env File im Parent-Directory für die Schlüssel
Verwende das Modell 'moonshotai/kimi-k2.5'
Verwende das git repo im Parent-Directory
Verwende das venv im Parent-Directory

## Parameter
- Startverzeichnis - In diesem Verzeichnis und allen Unterverzeichnissen wird nach .md Files gesucht
- DaysBack - Nur Files, welche jünger als DaysBack sind, bzw. in dieser Zeit geändert wurden, werden angeschaut


## Funktion
Finde alle Files, welche jünger als DaysBack Tage sind bzw. in dieser Zeit geändert wurden, werden angeschaut.
Nur Markdown Files werden angeschaut.

Die entsprechenden Files werden mit KI auf potentiell schadhafte Inhalte geprüft.
Der Prompt für die KI ist:

```
Das File wird von meinem OpenClaw Agenten gelesen und interpretiert.
Ich möchte sicher stellen, dass sich nichts eingeschlichen hat, was potentiell Schaden anrichtet, wie z.B.
- Schadhafter Code
- Installation von Viren
- Exfiltration von Daten an unberechtigte
- Exfiltration von Schlüsseln und Geheimnissen
- usw.

Gib als Ergebnis der Prüfung immer nur ein JSON mit folgendem Inhalt bzw eine Liste mit diesen JSON objekten zurück:
{
    "File": "/home/baettig/test.md",
    "Result":["OK"|"DANGER"],
    "Comment": "I found a problem in Line XY: ...."
}
```
