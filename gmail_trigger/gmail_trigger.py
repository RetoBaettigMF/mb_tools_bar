#!/usr/bin/env python3
"""
gmail_trigger.py - Lauscht auf neue Gmail-Mails via IMAP IDLE
und benachrichtigt OpenClaw bei neuen Nachrichten.

Verwendung:
    ./gmail_trigger.py
    ./gmail_trigger.py --once  # Einmalige Prüfung, dann beenden
    ./gmail_trigger.py --label INBOX --label Sent  # Mehrere Labels
"""

import imaplib
import ssl
import socket
import subprocess
import time
import logging
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# .env aus Parent-Verzeichnis laden
_env_path = Path(__file__).parent.parent / '.env'
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path)
except ImportError:
    pass

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gmail-trigger")

# Config aus Umgebung oder .env
class Config:
    IMAP_SERVER = os.getenv('GMAIL_IMAP_SERVER', 'imap.gmail.com')
    EMAIL = os.getenv('GMAIL_EMAIL')
    APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
    OPENCLAW_SESSION = os.getenv('OPENCLAW_SESSION', 'main')
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
    IDLE_TIMEOUT = int(os.getenv('IDLE_TIMEOUT', '600'))  # 10 Minuten
    LABELS = os.getenv('GMAIL_LABELS', 'INBOX').split(',')
    PROCESSED_IDS_FILE = os.getenv('PROCESSED_IDS_FILE', '/tmp/gmail_trigger_processed.json')


def load_processed_ids():
    """Lädt bereits verarbeitete Message-IDs"""
    try:
        import json
        if os.path.exists(Config.PROCESSED_IDS_FILE):
            with open(Config.PROCESSED_IDS_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        logger.warning(f"Konnte processed IDs nicht laden: {e}")
    return set()


def save_processed_ids(ids):
    """Speichert verarbeitete Message-IDs"""
    try:
        import json
        # Max 1000 IDs speichern (alte löschen)
        ids_list = list(ids)[-1000:]
        os.makedirs(os.path.dirname(Config.PROCESSED_IDS_FILE) or '/tmp', exist_ok=True)
        with open(Config.PROCESSED_IDS_FILE, 'w') as f:
            json.dump(ids_list, f)
    except Exception as e:
        logger.warning(f"Konnte processed IDs nicht speichern: {e}")


def notify_openclaw(subject, sender, message_id, label):
    """Sendet Event an OpenClaw Gateway"""
    # Duplikat-Check
    processed = load_processed_ids()
    if message_id in processed:
        logger.debug(f"Bereits verarbeitet: {message_id}")
        return False
    
    # Kurzer subject
    short_subject = subject[:60] + "..." if len(subject) > 60 else subject
    
    # Label-Emoji
    emoji = "📧" if label == "INBOX" else "📤" if label == "Sent" else "📨"
    
    text = f"{emoji} Neue Email in [{label}] von {sender}: {short_subject}. Bitte verarbeite sie jetzt gemäss prompts/AnswerEmails.md. Schreibe kurz auf meinen Telegram-Kanal, was läuft."
    
    try:
        subprocess.Popen(
            ["openclaw", "agent", "--agent", Config.OPENCLAW_SESSION, "--message", text]
        )
        logger.info(f"Benachrichtigt: {short_subject}")
        processed.add(message_id)
        save_processed_ids(processed)
        return True

    except Exception as e:
        logger.error(f"Fehler beim Benachrichtigen: {e}")

    return False


def parse_email_header(header_data):
    """Parst Email-Header nach Subject, From, Message-ID"""
    import email
    from email.header import decode_header
    
    try:
        msg = email.message_from_bytes(header_data)
        
        # Subject dekodieren
        subject = ""
        raw_subject = msg.get('Subject', '')
        if raw_subject:
            decoded = decode_header(raw_subject)
            parts = []
            for part, charset in decoded:
                if isinstance(part, bytes):
                    try:
                        parts.append(part.decode(charset or 'utf-8', errors='ignore'))
                    except:
                        parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    parts.append(part)
            subject = ''.join(parts)
        
        # From dekodieren
        sender = ""
        raw_from = msg.get('From', '')
        if raw_from:
            decoded = decode_header(raw_from)
            parts = []
            for part, charset in decoded:
                if isinstance(part, bytes):
                    try:
                        parts.append(part.decode(charset or 'utf-8', errors='ignore'))
                    except:
                        parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    parts.append(part)
            sender = ''.join(parts)
        
        # Message-ID
        message_id = msg.get('Message-ID', '').strip('<>')
        
        return subject, sender, message_id
        
    except Exception as e:
        logger.error(f"Fehler beim Parsen des Headers: {e}")
        return "", "", ""


def check_mailbox(mail, label):
    """Prüft ein Mailbox-Label auf neue/ungelesene Emails"""
    try:
        status, _ = mail.select(label)
        if status != 'OK':
            logger.error(f"Konnte Label {label} nicht selektieren")
            return 0
        
        # Suche nach ungelesenen
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.warning(f"Suche fehlgeschlagen in {label}")
            return 0
        
        count = 0
        msg_nums = messages[0].split()
        
        for num in msg_nums:
            try:
                status, data = mail.fetch(num, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT MESSAGE-ID)])')
                if status != 'OK' or not data or not data[0]:
                    continue
                
                header_data = data[0][1]
                subject, sender, message_id = parse_email_header(header_data)
                
                if sender and message_id:
                    if notify_openclaw(subject, sender, message_id, label):
                        count += 1
                        
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von Mail {num}: {e}")
        
        logger.info(f"{label}: {count} neue Benachrichtigungen")
        return count
        
    except Exception as e:
        logger.error(f"Fehler bei Mailbox {label}: {e}")
        return 0


def connect_imap():
    """Stellt IMAP-Verbindung her"""
    context = ssl.create_default_context()
    mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, ssl_context=context)
    mail.login(Config.EMAIL, Config.APP_PASSWORD)
    logger.info(f"Eingeloggt als {Config.EMAIL}")
    return mail


def idle_mode(mail, label):
    """Führt IDLE für ein Label durch"""
    try:
        status, data = mail.select(label)
        logger.info(f"IDLE Modus für {label}")

        # Socket timeout gegen ewiges Hängen (Gmail schliesst TCP manchmal still)
        mail.sock.settimeout(30)

        # IDLE starten
        tag = mail._new_tag()
        mail.send(tag + b" IDLE\r\n")

        tag_str = tag.decode('ascii')
        deadline = time.time() + Config.IDLE_TIMEOUT
        while time.time() < deadline:
            try:
                line = mail.readline().decode('utf-8', errors='ignore')
                if line.startswith('*'):
                    if 'EXISTS' in line or 'RECENT' in line:
                        logger.info(f"IDLE Event in {label}: {line.strip()}")
                        mail.send(b"DONE\r\n")
                        time.sleep(0.5)
                        return True
                elif line.startswith(tag_str):
                    return False
            except socket.timeout:
                continue  # Kein Event, weiterwarten
            except Exception as e:
                logger.error(f"IDLE Fehler: {e}")
                return False

        mail.send(b"DONE\r\n")
        return False

    except Exception as e:
        logger.error(f"IDLE Setup Fehler: {e}")
        return False


def stop_idle(mail):
    """Beendet IDLE Mode"""
    try:
        mail.send(b"DONE\r\n")
        time.sleep(0.5)
    except:
        pass


def run_once():
    """Einmaliger Durchlauf - prüft alle Labels und beendet sich"""
    if not Config.EMAIL or not Config.APP_PASSWORD:
        logger.error("GMAIL_EMAIL oder GMAIL_APP_PASSWORD nicht gesetzt!")
        logger.error("Bitte .env im Parent-Verzeichnis prüfen.")
        sys.exit(1)
    
    mail = None
    try:
        mail = connect_imap()
        total = 0
        for label in Config.LABELS:
            label = label.strip()
            if label:
                total += check_mailbox(mail, label)
        logger.info(f"Insgesamt {total} neue Emails gefunden")
        return total
        
    except Exception as e:
        logger.error(f"Fehler: {e}")
        return -1
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except:
                pass


def run_daemon():
    """Dauerhafter Daemon mit IDLE"""
    if not Config.EMAIL or not Config.APP_PASSWORD:
        logger.error("GMAIL_EMAIL oder GMAIL_APP_PASSWORD nicht gesetzt!")
        logger.error("Bitte .env im Parent-Verzeichnis prüfen.")
        sys.exit(1)
    
    logger.info("Gmail Trigger Daemon gestartet")
    logger.info(f"Überwachte Labels: {Config.LABELS}")
    
    while True:
        mail = None
        try:
            mail = connect_imap()
            
            # Erste Prüfung aller Labels
            for label in Config.LABELS:
                label = label.strip()
                if label:
                    check_mailbox(mail, label)
            
            # IDLE Loop für INBOX (primäres Label)
            primary_label = Config.LABELS[0].strip() if Config.LABELS else 'INBOX'
            
            idle_start = time.time()
            while time.time() - idle_start < Config.IDLE_TIMEOUT:
                if idle_mode(mail, primary_label):
                    # Neues Event - prüfen
                    time.sleep(2)  # Kurz warten bis Mail vollständig
                    check_mailbox(mail, primary_label)
                    # IDLE neu starten
                    idle_start = time.time()
                else:
                    # IDLE unerwartet beendet
                    break
            
            # IDLE Timeout erreicht - Reconnect
            logger.info("IDLE Timeout - Reconnect")
            
        except imaplib.IMAP4.abort as e:
            logger.warning(f"IMAP Verbindung abgebrochen: {e}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {e}")
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass
        
        logger.info("Reconnect in 10 Sekunden...")
        time.sleep(10)


def main():
    parser = argparse.ArgumentParser(description='Gmail Trigger für OpenClaw')
    parser.add_argument('--once', action='store_true', 
                        help='Einmalige Prüfung und beenden')
    parser.add_argument('--label', action='append', dest='labels',
                        help='Zu überwachendes Label (mehrfach möglich)')
    
    args = parser.parse_args()
    
    # Labels aus Args überschreiben Config
    if args.labels:
        Config.LABELS = args.labels
    
    if args.once:
        sys.exit(0 if run_once() >= 0 else 1)
    else:
        run_daemon()


if __name__ == "__main__":
    main()
