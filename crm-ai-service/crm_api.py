"""
crm_api- API for search and retrieval in the beerli/vTiger CRM

"""

import hashlib
import json
import os
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