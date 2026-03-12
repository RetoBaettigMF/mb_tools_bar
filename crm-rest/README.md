# crm — berliCRM CLI

Command-line tool for querying berliCRM via its REST API. All output is JSON.

## Setup

Create a `.env` file in this directory:

```
CRM_URL=https://your-crm-instance.example.com
CRM_USER=your.username
CRM_API_KEY=your-api-key
```

Alternatively, export the variables in your shell:

```bash
export CRM_URL=https://your-crm-instance.example.com
export CRM_USER=your.username
export CRM_API_KEY=your-api-key
```

No external dependencies — Python stdlib only.

## Commands

### search-contacts

Search contacts by first name, last name, or email.

```bash
crm search-contacts "Max Muster"
crm search-contacts "max.muster@example.com"
```

### search-accounts

Search companies/accounts by name, email, or phone.

```bash
crm search-accounts "Cudos"
crm search-accounts "AG"
```

### search-potentials

Search sales potentials by name.

```bash
crm search-potentials "Cloud Migration"
crm search-potentials "Projekt XY"
```

### search-comments

Search all comments by content.

```bash
crm search-comments "onboarding"
crm search-comments "meeting notes"
```

### account-comments

List all comments for a specific account. Accepts either an account name or a CRM ID.

```bash
crm account-comments "Cudos AG"
crm account-comments 3x12345
```

If the name matches multiple accounts, the command returns the list of matches with their IDs so you can use the exact one.

### details

Retrieve full details of any CRM object by its ID.

```bash
crm details 4x2712     # Contact
crm details 3x12345    # Account
crm details 13x456     # Potential
```

### query

Run a raw SQL-like query directly against the CRM API. Useful for precise filtering, custom field selection, and sorting.

```bash
# All contacts with a cudos.ch email
crm query "select * from Contacts where email like '%cudos.ch%' limit 0, 50;"

# Accounts whose name starts with "Bau"
crm query "select id, accountname, phone from Accounts where accountname like 'Bau%' limit 0, 100;"

# Potentials closing after a specific date, sorted by closing date
crm query "select * from Potentials where closingdate > '2025-01-01' order by closingdate limit 0, 50;"

# Count all open potentials
crm query "select count(*) from Potentials where sales_stage != 'Closed Won' and sales_stage != 'Closed Lost';"

# Comments on a specific account
crm query "select * from ModComments where related_to = '3x12345' order by createdtime limit 0, 100;"
```

**Query syntax** (subset of SQL, no joins):

```
select * | <column_list> | count(*)
from <Module>
[where <conditions>]
[order by <columns>]
[limit [<offset>,] <count>];
```

- Supported operators: `<`, `>`, `<=`, `>=`, `=`, `!=`, `like`, `in ()`
- Conditions are evaluated left to right — no bracket grouping
- Maximum 100 records per call (use `limit <offset>, 100` to page through results)
- Only works on entity modules (Contacts, Accounts, Potentials, ModComments, etc.)

## Output

All commands print JSON to stdout. Errors are printed as JSON to stderr with exit code 1.

Pipe into `jq` for filtering:

```bash
crm search-accounts "Cudos" | jq '.[].accountname'
crm query "select id, firstname, lastname, email from Contacts limit 0, 10;" | jq '.[] | {id, email}'
```
