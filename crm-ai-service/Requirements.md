# AI-Powered CRM Tool

## Overview
This is a command-line tool which takes free-text inputs for CRM-Tasks and uses an internal AI-Agent with tools that tries to solve the task in multiple turns if needed. Then it returns the result in .JSON format to the console.

## CRM Interface
The CRM Interface is already implemented in cr_ai_tool.py
Refactor it into a module that you can import from the main program.

## AI Agent
- Use the specified openrouter model and key from the .env file as AI model.
- Implement an Agent that can access the CRM Interface and can solve a task from the command line input, doing multiple turns if needed.
- Implement a timeout which can be configured from the command line. Default to 2 Minutes.
- Return the result as .JSON
- Use a separate file for the system prompt for the Agent
- Use SQL-Like queries for the api (see infos below)
- Write detailed instructions about how to use the SQL-Like queries to the system prompt such that the agent is as fast and reliable as possible in using the API

## Additional requirements
- Add it to the git repo in the parent dir, commit and push regularly
- Test the solution
- Add a Readme.md

## SQL-Like queries

Run a raw SQL-like query directly against the CRM API. Useful for precise filtering, custom field selection, and sorting.

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

**Examples**
```
# All contacts with a cudos.ch email
"select * from Contacts where email like '%cudos.ch%' limit 0, 50;"

# Accounts whose name starts with "Bau"
"select id, accountname, phone from Accounts where accountname like 'Bau%' limit 0, 100;"

# Potentials closing after a specific date, sorted by closing date
"select * from Potentials where closingdate > '2025-01-01' order by closingdate limit 0, 50;"

# Count all open potentials
"select count(*) from Potentials where sales_stage != 'Closed Won' and sales_stage != 'Closed Lost';"

# Comments on a specific account
"select * from ModComments where related_to = '3x12345' order by createdtime limit 0, 100;"
```

