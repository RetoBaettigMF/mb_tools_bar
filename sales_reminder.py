#!/usr/bin/env python3
"""
Sales Potential Reminder Tool
Sends reminder email on the Wednesday before the 4th Monday of each month
Usage: python3 sales_reminder.py <recipient_email>
"""

import sys
import subprocess
from datetime import date, timedelta
from calendar import monthcalendar

def is_wednesday_before_4th_monday(check_date: date = None) -> bool:
    """
    Check if the given date is the Wednesday before the 4th Monday of the month.
    The 4th Monday is the Monday of week 4 (between 22nd-28th of the month).
    The Wednesday before that would be 5 days earlier (between 17th-23rd).
    """
    if check_date is None:
        check_date = date.today()
    
    # Must be a Wednesday
    if check_date.weekday() != 2:  # Monday=0, Tuesday=1, Wednesday=2
        return False
    
    # Get the calendar for this month
    cal = monthcalendar(check_date.year, check_date.month)
    
    # Find the 4th Monday
    # week 0 is the first week, but it might not have a Monday
    monday_count = 0
    fourth_monday = None
    
    for week in cal:
        if week[0] != 0:  # Monday is column 0, 0 means no day in this week
            monday_count += 1
            if monday_count == 4:
                fourth_monday = week[0]
                break
    
    if fourth_monday is None:
        return False
    
    # Calculate the Wednesday before the 4th Monday
    # Monday - 5 days = previous Wednesday
    fourth_monday_date = date(check_date.year, check_date.month, fourth_monday)
    wednesday_before = fourth_monday_date - timedelta(days=5)
    
    return check_date == wednesday_before

def send_reminder_email(recipient: str) -> bool:
    """Send reminder email using gog"""
    subject = "Reminder: Sales-Potentiale aktualisieren"
    body = """Hoi zusammen

Dies ist eine freundliche Erinnerung, die Sales-Potentiale bitte zu aktualisieren.

Besten Dank!

Gruss
Retos Bot Morticia 💪"""
    
    try:
        result = subprocess.run(
            ['gog', 'gmail', 'send', '--to', recipient, '--subject', subject, '--body', body],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✓ Reminder email sent successfully to {recipient}")
            return True
        else:
            print(f"✗ Failed to send email: {result.stderr}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Email command timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("✗ 'gog' command not found. Please install gog CLI.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Error sending email: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sales_reminder.py <recipient_email>")
        print("Example: python3 sales_reminder.py bu@cudos.ch")
        print("\nThis script checks if today is the Wednesday before the 4th Monday of the month.")
        print("If yes, it sends a reminder email to update sales potentials.")
        sys.exit(1)
    
    recipient = sys.argv[1]
    today = date.today()
    
    print(f"Checking date: {today.strftime('%A, %d.%m.%Y')}")
    
    if is_wednesday_before_4th_monday(today):
        print(f"✓ Today IS the Wednesday before the 4th Monday!")
        print(f"Sending reminder to {recipient}...")
        
        if send_reminder_email(recipient):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"✗ Today is NOT the Wednesday before the 4th Monday. No action needed.")
        print("Exiting silently.")
        sys.exit(0)

if __name__ == '__main__':
    main()
