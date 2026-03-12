#!/usr/bin/env python3
"""
crm - berliCRM command-line tool

Usage:
  crm search-contacts "Max Muster"
  crm search-accounts "Cudos AG"
  crm search-potentials "Projekt XY"
  crm search-comments "meeting"
  crm account-comments "Cudos AG"
  crm account-comments 3x12345
  crm details 4x2712
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config():
    env_file = Path(__file__).parent / ".env"
    config = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    config[key.strip()] = value.strip()
    # Environment variables take precedence
    for key in ("CRM_URL", "CRM_USER", "CRM_API_KEY"):
        if key in os.environ:
            config[key] = os.environ[key]
    return config


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http_get(url, params):
    full_url = url + "/webservice.php?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full_url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _http_post(url, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url + "/webservice.php", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# API operations
# ---------------------------------------------------------------------------

def crm_login(base_url, username, api_key):
    """Authenticate and return session name."""
    r = _http_get(base_url, {"operation": "getchallenge", "username": username})
    if not r["success"]:
        raise RuntimeError(f"getchallenge failed: {r.get('error')}")

    token = r["result"]["token"]
    access_key = hashlib.md5((token + api_key).encode()).hexdigest()

    r = _http_post(base_url, {
        "operation": "login",
        "username": username,
        "accessKey": access_key,
    })
    if not r["success"]:
        raise RuntimeError(f"login failed: {r.get('error')}")

    return r["result"]["sessionName"]


def crm_query(base_url, session, sql):
    r = _http_get(base_url, {
        "operation": "query",
        "sessionName": session,
        "query": sql,
    })
    if not r["success"]:
        raise RuntimeError(f"query failed: {r.get('error')} | SQL: {sql}")
    return r["result"]


def crm_retrieve(base_url, session, object_id):
    r = _http_get(base_url, {
        "operation": "retrieve",
        "sessionName": session,
        "id": object_id,
    })
    if not r["success"]:
        raise RuntimeError(f"retrieve failed: {r.get('error')}")
    return r["result"]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def err(msg):
    print(json.dumps({"error": msg}, indent=2, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_search_contacts(base_url, session, args):
    q = args.query.replace("'", "\\'")
    sql = (
        f"select * from Contacts where "
        f"firstname like '%{q}%' or lastname like '%{q}%' or email like '%{q}%' "
        f"limit 0, 100;"
    )
    out(crm_query(base_url, session, sql))


def cmd_search_accounts(base_url, session, args):
    q = args.query.replace("'", "\\'")
    sql = (
        f"select * from Accounts where "
        f"accountname like '%{q}%' or email1 like '%{q}%' or phone like '%{q}%' "
        f"limit 0, 100;"
    )
    out(crm_query(base_url, session, sql))


def cmd_search_potentials(base_url, session, args):
    q = args.query.replace("'", "\\'")
    sql = (
        f"select * from Potentials where "
        f"potentialname like '%{q}%' "
        f"limit 0, 100;"
    )
    out(crm_query(base_url, session, sql))


def cmd_search_comments(base_url, session, args):
    q = args.query.replace("'", "\\'")
    sql = (
        f"select * from ModComments where "
        f"commentcontent like '%{q}%' "
        f"limit 0, 100;"
    )
    out(crm_query(base_url, session, sql))


def _resolve_account_id(base_url, session, account_ref):
    """Return a CRM account ID from either a CRM ID (3xNNN) or a name string."""
    if "x" in account_ref and account_ref.split("x")[0].isdigit():
        return account_ref

    q = account_ref.replace("'", "\\'")
    sql = f"select id, accountname from Accounts where accountname like '%{q}%' limit 0, 20;"
    accounts = crm_query(base_url, session, sql)

    if not accounts:
        err(f"No account found matching '{account_ref}'")

    if len(accounts) > 1:
        # Return the list so the user can pick
        out({
            "error": f"Multiple accounts found for '{account_ref}'. Use the exact ID.",
            "accounts": [{"id": a["id"], "accountname": a["accountname"]} for a in accounts],
        })
        sys.exit(1)

    return accounts[0]["id"]


def cmd_account_comments(base_url, session, args):
    account_id = _resolve_account_id(base_url, session, args.account)
    sql = (
        f"select * from ModComments where related_to = '{account_id}' "
        f"order by createdtime limit 0, 100;"
    )
    out(crm_query(base_url, session, sql))


def cmd_details(base_url, session, args):
    out(crm_retrieve(base_url, session, args.id))


def cmd_query(base_url, session, args):
    out(crm_query(base_url, session, args.sql))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    config = load_config()
    base_url = config.get("CRM_URL", "").rstrip("/")
    username = config.get("CRM_USER", "")
    api_key  = config.get("CRM_API_KEY", "").strip()

    if not base_url or not username or not api_key:
        err("CRM_URL, CRM_USER and CRM_API_KEY must be set (in .env or environment)")

    parser = argparse.ArgumentParser(
        prog="crm",
        description="berliCRM command-line tool – all output as JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  crm search-contacts "Max Muster"
  crm search-accounts "Cudos"
  crm search-potentials "Cloud Migration"
  crm search-comments "onboarding"
  crm account-comments "Cudos AG"
  crm account-comments 3x12345
  crm details 4x2712
  crm details 3x12345
  crm details 13x456
  crm query "select * from Contacts where email like '%cudos%' limit 0, 20;"
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search-contacts", help="Search contacts/persons by name or email")
    p.add_argument("query", help="Search term")

    p = sub.add_parser("search-accounts", help="Search companies/accounts by name, email or phone")
    p.add_argument("query", help="Search term")

    p = sub.add_parser("search-potentials", help="Search sales potentials by name")
    p.add_argument("query", help="Search term")

    p = sub.add_parser("search-comments", help="Search comments by content")
    p.add_argument("query", help="Search term")

    p = sub.add_parser("account-comments", help="List all comments for a specific account")
    p.add_argument("account", help="Account name or CRM ID (e.g. 3x12345)")

    p = sub.add_parser("details", help="Full details of any CRM object by ID")
    p.add_argument("id", help="CRM object ID (e.g. 4x2712, 3x123, 13x456)")

    p = sub.add_parser("query", help="Run a raw SQL-like query against the CRM")
    p.add_argument("sql", help="SQL-like query string (e.g. \"select * from Contacts where ...;\")")

    args = parser.parse_args()

    try:
        session = crm_login(base_url, username, api_key)
    except Exception as e:
        err(f"Authentication failed: {e}")

    try:
        dispatch = {
            "search-contacts":   cmd_search_contacts,
            "search-accounts":   cmd_search_accounts,
            "search-potentials": cmd_search_potentials,
            "search-comments":   cmd_search_comments,
            "account-comments":  cmd_account_comments,
            "details":           cmd_details,
            "query":             cmd_query,
        }
        dispatch[args.command](base_url, session, args)
    except SystemExit:
        raise
    except Exception as e:
        err(str(e))


if __name__ == "__main__":
    main()
