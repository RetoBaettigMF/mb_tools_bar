#!/usr/bin/env python3
"""
Session-to-Markdown Exporter

Exportiert eine OpenClaw Session (JSONL) 1:1 in ein Markdown-File.
Keine Zusammenfassung, kein Kürzen - reine Konversation.

Verwendung:
    ./session2md.py <session-id>
    ./session2md.py /pfad/zur/session.jsonl

Output:
    session-<id>-export.md im aktuellen Verzeichnis
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def format_timestamp(ts_str):
    """Formatiert ISO-Timestamp für bessere Lesbarkeit"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts_str

def extract_message_content(msg):
    """Extrahiert den Text-Inhalt aus einer Nachricht"""
    if not msg:
        return ""
    
    if isinstance(msg, str):
        return msg
    
    if isinstance(msg, list):
        parts = []
        for item in msg:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(item.get('text', ''))
                elif item.get('type') == 'thinking':
                    parts.append(f"[Thinking: {item.get('thinking', '')}]")
                elif item.get('type') == 'toolCall':
                    tool_name = item.get('name', 'unknown')
                    args = item.get('arguments', {})
                    parts.append(f"[Tool: {tool_name}({args})]")
                elif item.get('type') == 'toolResult':
                    tool_name = item.get('toolName', 'unknown')
                    content = item.get('content', [])
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get('text', '') if isinstance(content[0], dict) else str(content)
                    else:
                        text_content = str(content)
                    # Truncate very long tool results
                    if len(text_content) > 1000:
                        text_content = text_content[:500] + "\n... [truncated] ...\n" + text_content[-500:]
                    parts.append(f"[ToolResult: {tool_name}]\n{text_content}")
            elif isinstance(item, str):
                parts.append(item)
        return '\n'.join(parts)
    
    if isinstance(msg, dict):
        return msg.get('text', str(msg))
    
    return str(msg)

def parse_session(file_path):
    """Parst die JSONL Session-Datei"""
    entries = []
    session_info = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
                
                # Session-Info aus erster Zeile extrahieren
                if entry.get('type') == 'session':
                    session_info = {
                        'id': entry.get('id'),
                        'timestamp': entry.get('timestamp'),
                        'cwd': entry.get('cwd'),
                        'version': entry.get('version')
                    }
            except json.JSONDecodeError as e:
                print(f"Warnung: Konnte Zeile nicht parsen: {e}")
                continue
    
    return session_info, entries

def export_to_markdown(session_info, entries, output_path):
    """Exportiert die Session 1:1 als Markdown"""
    
    lines = []
    
    # Header
    lines.append("# Session Export")
    lines.append("")
    lines.append(f"**Session ID:** `{session_info.get('id', 'unknown')}`")
    lines.append(f"**Exportiert:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Version:** {session_info.get('version', 'unknown')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Konversation
    for entry in entries:
        entry_type = entry.get('type')
        
        if entry_type == 'message':
            msg = entry.get('message', {})
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = format_timestamp(entry.get('timestamp', ''))
            
            # Role als Header
            if role == 'user':
                lines.append(f"## 👤 User ({timestamp})")
            elif role == 'assistant':
                lines.append(f"## 🤖 Assistant ({timestamp})")
            elif role == 'system':
                lines.append(f"## ⚙️ System ({timestamp})")
            elif role == 'toolResult':
                lines.append(f"## 🔧 Tool Result ({timestamp})")
            else:
                lines.append(f"## {role.upper()} ({timestamp})")
            
            lines.append("")
            
            # Content extrahieren und formatieren
            text = extract_message_content(content)
            if text:
                lines.append(text)
            
            lines.append("")
            lines.append("---")
            lines.append("")
            
        elif entry_type == 'session':
            # Session-Start Info
            lines.append(f"## 📁 Session Start ({format_timestamp(entry.get('timestamp', ''))})")
            lines.append("")
            lines.append(f"- **Working Directory:** `{entry.get('cwd', 'unknown')}`")
            lines.append(f"- **Session ID:** `{entry.get('id', 'unknown')}`")
            lines.append("")
            lines.append("---")
            lines.append("")
            
        elif entry_type == 'model_change':
            lines.append(f"## 🔄 Model Change ({format_timestamp(entry.get('timestamp', ''))})")
            lines.append("")
            lines.append(f"- **Provider:** {entry.get('provider', 'unknown')}")
            lines.append(f"- **Model:** `{entry.get('modelId', 'unknown')}`")
            lines.append("")
            lines.append("---")
            lines.append("")
            
        elif entry_type == 'thinking_level_change':
            lines.append(f"## 💭 Thinking Level Change ({format_timestamp(entry.get('timestamp', ''))})")
            lines.append("")
            lines.append(f"- **Level:** {entry.get('thinkingLevel', 'unknown')}")
            lines.append("")
            lines.append("---")
            lines.append("")
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return len(lines)

def find_session(session_id):
    """Sucht nach einer Session-Datei an verschiedenen Orten"""
    
    # Mögliche Pfade
    search_paths = [
        # Direkter Pfad
        session_id if session_id.endswith('.jsonl') else None,
        # Im Sessions-Verzeichnis
        f"/home/reto/.openclaw/agents/main/sessions/{session_id}.jsonl",
        f"{os.path.expanduser('~')}/.openclaw/agents/main/sessions/{session_id}.jsonl",
        # Aktuelles Verzeichnis
        f"./{session_id}.jsonl",
        f"./{session_id}",
    ]
    
    for path in search_paths:
        if path and os.path.exists(path):
            return path
    
    return None

def main():
    if len(sys.argv) < 2:
        print("Verwendung: session2md.py <session-id> | <pfad/zur/session.jsonl>")
        print("")
        print("Beispiele:")
        print("  ./session2md.py 61ed1bdf-cd0c-4cb9-83c6-23509d6bff2d")
        print("  ./session2md.py /home/reto/.openclaw/agents/main/sessions/61ed1bdf-cd0c-4cb9-83c6-23509d6bff2d.jsonl")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # Session-Datei finden
    session_file = find_session(input_arg)
    
    if not session_file:
        print(f"Fehler: Konnte Session nicht finden: {input_arg}")
        print("")
        print("Gesucht in:")
        print(f"  - {input_arg}")
        print(f"  - {input_arg}.jsonl")
        print(f"  - ~/.openclaw/agents/main/sessions/{input_arg}.jsonl")
        sys.exit(1)
    
    print(f"Gefunden: {session_file}")
    
    # Session-ID für Output-Filename extrahieren
    if '/' in input_arg and not input_arg.endswith('.jsonl'):
        session_id = input_arg.split('/')[-1].replace('.jsonl', '')
    else:
        session_id = input_arg.replace('.jsonl', '')
    
    output_file = f"session-{session_id}-export.md"
    
    # Parsen
    print(f"Parse Session...")
    session_info, entries = parse_session(session_file)
    
    # Exportieren
    print(f"Exportiere nach {output_file}...")
    line_count = export_to_markdown(session_info, entries, output_file)
    
    print(f"")
    print(f"✅ Export erfolgreich!")
    print(f"   Datei: {output_file}")
    print(f"   Einträge: {len(entries)}")
    print(f"   Zeilen: {line_count}")

if __name__ == '__main__':
    main()
