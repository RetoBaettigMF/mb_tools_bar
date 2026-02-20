#!/usr/bin/env python3
"""
NZZ Reader - Tool zum Lesen von NZZ-Artikeln aus dem lokalen Scraping-Archiv.

Verwendung:
    nzz-reader [NUMMER]           - Zeigt die neuesten 10 Artikel oder einen bestimmten Artikel
    nzz-reader --list, -l         - Zeigt die neuesten 10 Artikel (Standard)
    nzz-reader --help, -h         - Zeigt diese Hilfe

Beispiele:
    nzz-reader                    - Zeigt die neuesten 10 Artikel
    nzz-reader 3                  - Zeigt den vollständigen Text des Artikels #3
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Konfiguration
ARTICLES_DIR = Path("/home/reto/Development/NZZApp/backend/articles")
INDEX_FILE = ARTICLES_DIR / "scraped_articles.json"


def load_articles():
    """Lädt die Artikel-Metadaten aus der Index-Datei."""
    if not INDEX_FILE.exists():
        print(f"❌ Index-Datei nicht gefunden: {INDEX_FILE}")
        sys.exit(1)
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('articles', [])


def get_latest_articles(articles, count=10):
    """Gibt die neuesten N Artikel zurück."""
    # Sortiere nach scraped_date (neueste zuerst)
    sorted_articles = sorted(
        articles,
        key=lambda x: x.get('scraped_date', ''),
        reverse=True
    )
    return sorted_articles[:count]


def format_article_summary(index, article):
    """Formatiert eine Artikel-Zusammenfassung."""
    title = article.get('title', 'Kein Titel')
    date = article.get('scraped_date', 'Unbekannt')
    filename = article.get('filename', '')
    
    # Kategorie aus dem Pfad extrahieren
    category = 'Allgemein'
    if '/' in filename:
        category = filename.split('/')[1].capitalize()
    
    # Titel auf 70 Zeichen kürzen
    if len(title) > 70:
        title = title[:67] + '...'
    
    return f"  {index:2}. [{category:12}] {title}\n      📅 {date}"


def show_article_list(articles):
    """Zeigt eine Liste der Artikel an."""
    latest = get_latest_articles(articles, 10)
    
    if not latest:
        print("📭 Keine Artikel gefunden.")
        return
    
    print("\n📰 Neueste NZZ-Artikel:\n")
    print("=" * 80)
    
    for i, article in enumerate(latest, 1):
        print(format_article_summary(i, article))
        print()
    
    print("=" * 80)
    print(f"\n💡 Tippe 'nzz-reader <nummer>' für den vollständigen Text (z.B. 'nzz-reader 3')")


def read_article_file(article):
    """Liest den Inhalt einer Artikel-Datei."""
    filename = article.get('filename', '')
    if not filename:
        return None
    
    filepath = ARTICLES_DIR / filename
    
    if not filepath.exists():
        # Versuche alternative Dateiendungen
        for ext in ['.md', '.txt']:
            alt_path = filepath.with_suffix(ext)
            if alt_path.exists():
                filepath = alt_path
                break
    
    if not filepath.exists():
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def show_article(articles, number):
    """Zeigt einen bestimmten Artikel im Volltext an."""
    latest = get_latest_articles(articles, 10)
    
    if number < 1 or number > len(latest):
        print(f"❌ Ungültige Nummer. Bitte wähle eine Zahl zwischen 1 und {len(latest)}.")
        return
    
    article = latest[number - 1]
    
    print("\n" + "=" * 80)
    print(f"📰 {article.get('title', 'Kein Titel')}")
    print("=" * 80)
    print(f"🔗 {article.get('url', 'Keine URL')}")
    print(f"📅 {article.get('scraped_date', 'Unbekannt')}")
    print("=" * 80)
    print()
    
    content = read_article_file(article)
    
    if content:
        print(content)
    else:
        print(f"❌ Artikel-Inhalt nicht gefunden: {article.get('filename')}")
    
    print()
    print("=" * 80)


def show_help():
    """Zeigt die Hilfe an."""
    print(__doc__)


def main():
    args = sys.argv[1:]
    
    # Hilfe anzeigen
    if '--help' in args or '-h' in args:
        show_help()
        return
    
    # Artikel laden
    articles = load_articles()
    
    if not articles:
        print("📭 Keine Artikel im Index gefunden.")
        return
    
    # Liste anzeigen (Standard)
    if not args or '--list' in args or '-l' in args:
        show_article_list(articles)
        return
    
    # Versuche, eine Artikel-Nummer zu parsen
    try:
        number = int(args[0])
        show_article(articles, number)
    except ValueError:
        print(f"❌ Ungültiges Argument: {args[0]}")
        print("💡 Verwende 'nzz-reader --help' für Hilfe.")


if __name__ == '__main__':
    main()
