#!/usr/bin/env python3
"""
NZZ Reader - Tool zum Lesen von NZZ-Artikeln aus dem lokalen Scraping-Archiv.

Verwendung:
    nzz-reader [NUMMER]           - Zeigt die neuesten 10 Artikel oder einen bestimmten Artikel
    nzz-reader --list, -l         - Zeigt die neuesten 10 Artikel (Standard)
    nzz-reader --date, -d DATUM   - Zeigt alle Artikel eines bestimmten Tages (Format: YYYY-MM-DD)
    nzz-reader --help, -h         - Zeigt diese Hilfe

Beispiele:
    nzz-reader                    - Zeigt die neuesten 10 Artikel
    nzz-reader 3                  - Zeigt den vollständigen Text des Artikels #3
    nzz-reader --date 2025-03-15  - Zeigt alle Artikel vom 15.03.2025
    nzz-reader -d 2025-03-15      - Zeigt alle Artikel vom 15.03.2025
    nzz-reader --date 2025-03-15 3 - Zeigt den 3. Artikel vom 15.03.2025
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Konfiguration
ARTICLES_DIR = Path("/home/reto/Development/NZZApp/backend/articles")


def parse_article_metadata(filepath: Path) -> dict:
    """Liest Titel und URL aus einer Artikel-Datei."""
    title = filepath.stem.replace('_', ' ')
    url = ''
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    title = line[2:].strip()
                elif '→ Original auf NZZ.ch öffnen' in line or line.startswith('**[→'):
                    # Extract URL from markdown link
                    start = line.find('(https://')
                    end = line.find(')', start)
                    if start != -1 and end != -1:
                        url = line[start+1:end]
                    break
    except Exception:
        pass
    return {'title': title, 'url': url, 'filepath': filepath}


def load_articles():
    """Scannt das Artikelverzeichnis und gibt eine Liste von Artikeln zurück."""
    if not ARTICLES_DIR.exists():
        print(f"❌ Artikelverzeichnis nicht gefunden: {ARTICLES_DIR}")
        sys.exit(1)

    articles = []
    # Datum-Verzeichnisse (Format YYYY-MM-DD)
    for date_dir in sorted(ARTICLES_DIR.iterdir(), reverse=True):
        if not date_dir.is_dir() or not date_dir.name[:4].isdigit():
            continue
        scraped_date = date_dir.name
        for category_dir in sorted(date_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            for md_file in sorted(category_dir.glob('*.md')):
                meta = parse_article_metadata(md_file)
                articles.append({
                    'title': meta['title'],
                    'url': meta['url'],
                    'scraped_date': scraped_date,
                    'category': category.capitalize(),
                    'filepath': str(md_file),
                })
    return articles


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
    category = article.get('category', 'Allgemein')

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
    filepath = article.get('filepath', '')
    if not filepath or not Path(filepath).exists():
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
        print(f"❌ Artikel-Inhalt nicht gefunden: {article.get('filepath')}")
    
    print()
    print("=" * 80)


def show_articles_for_date(articles, date_str):
    """Zeigt alle Artikel eines bestimmten Tages an."""
    filtered = [a for a in articles if a.get('scraped_date') == date_str]

    if not filtered:
        print(f"📭 Keine Artikel für den {date_str} gefunden.")
        return

    print(f"\n📰 NZZ-Artikel vom {date_str}:\n")
    print("=" * 80)

    for i, article in enumerate(filtered, 1):
        print(format_article_summary(i, article))
        print()

    print("=" * 80)
    print(f"\n💡 Insgesamt {len(filtered)} Artikel gefunden.")
    print(f"   Tippe 'nzz-reader --date {date_str} <nummer>' für den vollständigen Text.")


def show_help():
    """Zeigt die Hilfe an."""
    print(__doc__)


def main():
    args = sys.argv[1:]

    # Hilfe anzeigen
    if '--help' in args or '-h' in args:
        show_help()
        return

    # Datum-Parameter auslesen
    date_str = None
    for flag in ('--date', '-d'):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                date_str = args[idx + 1]
                args = args[:idx] + args[idx + 2:]
            else:
                print(f"❌ '{flag}' erfordert ein Datum im Format YYYY-MM-DD.")
                sys.exit(1)
            break

    # Artikel laden
    articles = load_articles()

    if not articles:
        print("📭 Keine Artikel im Index gefunden.")
        return

    # Datum-Filter
    if date_str is not None:
        if args:
            try:
                number = int(args[0])
                filtered = [a for a in articles if a.get('scraped_date') == date_str]
                if not filtered:
                    print(f"📭 Keine Artikel für den {date_str} gefunden.")
                    return
                if number < 1 or number > len(filtered):
                    print(f"❌ Ungültige Nummer. Bitte wähle eine Zahl zwischen 1 und {len(filtered)}.")
                    return
                article = filtered[number - 1]
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
                    print(f"❌ Artikel-Inhalt nicht gefunden: {article.get('filepath')}")
                print()
                print("=" * 80)
                return
            except ValueError:
                print(f"❌ Ungültiges Argument: {args[0]}")
                sys.exit(1)
        show_articles_for_date(articles, date_str)
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
