# SalesReminderTool

Automated email reminder for sales potential updates, triggered on the Wednesday before the 4th Monday of each month.

## Features

- Calculates target date: Wednesday before 4th Monday
- Sends email via `gog gmail send` CLI command
- Designed for cron automation
- Exits silently when not the target date (no unnecessary noise)

## Usage

### Manual Execution

```bash
python3 sales_reminder.py recipient@example.com
```

The script will:
- Check if today is the target Wednesday
- If yes: Send email reminder
- If no: Exit silently with status 0

### Cron Setup

Add to crontab to run every Wednesday at 09:00:

```bash
crontab -e
```

Add this line:

```
0 9 * * 3 cd /path/to/openclaw_toolbox && python3 sales-reminder bu@cudos.ch
```

Or with absolute path:

```
0 9 * * 3 python3 /path/to/SalesReminderTool/sales_reminder.py bu@cudos.ch
```

## Date Calculation Algorithm

The script finds "Wednesday before 4th Monday":

1. Find all Mondays in the current month
2. Select the 4th Monday
3. Subtract 5 days to get the prior Wednesday

Example for February 2026:
- 4th Monday: February 23
- Target Wednesday: February 18 (23 - 5 days)

## Email Details

- **Sender**: bar.ai.bot@cudos.ch (via gog CLI)
- **Subject**: "Reminder: Sales Potential Update"
- **Signature**: "Retos Bot Morticia 💪"
- **Body**: Brief reminder to update sales potential in vTiger CRM

## Dependencies

- Python 3 standard library (calendar, datetime)
- `gog` CLI tool for sending emails
- Must be authenticated with bar.ai.bot@cudos.ch account

## Testing

To test the email sending logic without waiting for the target date:

1. Temporarily modify the date check in the script
2. Or use the current date when it happens to be a Wednesday
3. Check the email arrives at the recipient

```bash
# Test with your email
python3 sales_reminder.py your-email@example.com
```

## Exit Codes

- `0` - Success (email sent or not target date)
- `1` - Error (missing recipient, gog command failed, etc.)
