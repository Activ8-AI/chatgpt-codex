#!/usr/bin/env python3
"""
Enhanced Notion → GCP Secret Manager sync using hierarchical secret IDs.

This script reads secrets from a Notion database where each row contains
at least the following properties:

* **Name**: the base key name of the secret (e.g. `JWT_SECRET` or `SLACK_BOT_TOKEN`).
* **Secret**: the secret value.
* **Tenant**: the tenant identifier (e.g. `activ8ai`, `leverage`).
* **System**: the system or service category (e.g. `codex_portal`, `slack`, `teamwork`, `hubspot`).
* **Env**: the deployment environment (e.g. `prod`, `staging`, `dev`).

The resulting Secret Manager ID is built using a hierarchical scheme:

    maos/<env>/<tenant>/<system>/<name>

All components are lower‑cased and sanitized to meet GCP Secret Manager
requirements (only alphanumeric characters, underscores and hyphens are
allowed). A forward slash separates each hierarchy level. Example:

    PROD_ACTIV8AI_CODEX_PORTAL_JWT_SECRET

becomes the Secret Manager secret:

    maos/prod/activ8ai/codex_portal/jwt_secret

Usage (inside a GitHub Action after the `google-github-actions/auth` step has
run):

    python scripts/notion_to_sm_wif_hierarchical.py \
      --notion-token "${{ secrets.NOTION_TOKEN }}" \
      --db-id "<NOTION_DB_ID>" \
      --gcp-project "${{ secrets.GCP_PROJECT }}" \
      [--dry-run]

The script creates or updates secrets in Secret Manager. When the `--dry-run`
flag is provided, it prints the actions it would take without performing any
writes. Each invocation adds a new secret version; previous versions remain
available for auditing and rollback.

Requirements:

* Python packages: `google-cloud-secret-manager` and `requests` must be
  installed.
* The executing environment must be authenticated to GCP using a method
  supported by `google-cloud-secret-manager` (e.g. Workload Identity
  Federation via `google-github-actions/auth`).

Note: This script is deliberately independent of the shared
`notion_secrets_lib` to avoid coupling assumptions about Notion property
names. It expects a simple Notion schema with explicit columns for Name,
Secret, Tenant, System and Env.
"""

import argparse
import re
from typing import Dict

import requests
from google.cloud import secretmanager
from google.api_core.exceptions import AlreadyExists, PermissionDenied


NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"



def _req_headers(token: str) -> Dict[str, str]:
    """Construct standard headers for Notion API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_database(token: str, database_id: str, page_size: int = 100):
    """Query a Notion database and return all pages with automatic pagination."""
    url = f"{NOTION_API_BASE}/databases/{database_id}/query"
    results = []
    payload = {"page_size": page_size}
    while True:
        resp = requests.post(url, headers=_req_headers(token), json=payload)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        cursor = data.get("next_cursor")
        if not cursor:
            break
        payload["start_cursor"] = cursor
    return results


def extract_text(prop: dict) -> str:
    """Extract plain text from a Notion property."""
    if not prop:
        return ""
    ptype = prop.get("type")
    if ptype == "title":
        arr = prop.get("title", [])
        return arr[0].get("plain_text", "") if arr else ""
    if ptype == "rich_text":
        arr = prop.get("rich_text", [])
        return arr[0].get("plain_text", "") if arr else ""
    # Some Notion APIs return plain_text at top level
    if "plain_text" in prop:
        return prop.get("plain_text", "")
    # Fallback through lists
    for key in ("rich_text", "title", "text"):
        val = prop.get(key)
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, dict):
                return first.get("plain_text") or first.get("text", {}).get("content", "")
    return ""


def sanitize_component(component: str) -> str:
    """Sanitize a component of the secret ID (lowercase and replace invalid chars)."""
    comp = component.lower().replace(" ", "_")
    comp = re.sub(r"[^a-z0-9_-]", "_", comp)
    return comp


def build_secret_id(env: str, tenant: str, system: str, name: str) -> str:
    """Build a hierarchical Secret Manager ID from environment, tenant, system and name."""
    env_s = sanitize_component(env)
    tenant_s = sanitize_component(tenant)
    system_s = sanitize_component(system)
    name_s = sanitize_component(name)
    return f"maos/{env_s}/{tenant_s}/{system_s}/{name_s}"


def upsert_secret(client: secretmanager.SecretManagerServiceClient, project: str, secret_id: str, payload: str):
    """Create or update a secret in GCP Secret Manager."""
    parent = f"projects/{project}"
    name = f"projects/{project}/secrets/{secret_id}"
    try:
        client.create_secret(
            parent=parent,
            secret_id=secret_id,
            secret=secretmanager.Secret(
                replication=secretmanager.Replication(
                    automatic=secretmanager.Replication.Automatic()
                )
            ),
        )
        print(f"Created secret: {secret_id}")
    except AlreadyExists:
        print(f"Secret {secret_id} already exists; adding new version.")
    except PermissionDenied as e:
        print(f"Permission denied when creating secret {secret_id}: {e}")
        return
    except Exception as e:
        # Log unexpected errors but continue with other secrets
        print(f"Unexpected error creating secret {secret_id}: {e}")
    # Always attempt to add a new version
    payload_bytes = payload.encode("utf-8")
    response = client.add_secret_version(
        parent=name,
        payload={"data": payload_bytes},
    )
    print(f"Added secret version for {secret_id}: {response.name}")


def main():
    parser = argparse.ArgumentParser(description="Sync Notion secrets to GCP Secret Manager using hierarchical naming.")
    parser.add_argument("--notion-token", required=True, help="Notion integration token with read access to the database.")
    parser.add_argument("--db-id", required=True, help="Notion database ID containing secrets.")
    parser.add_argument("--gcp-project", required=True, help="GCP project ID for Secret Manager.")
    parser.add_argument("--dry-run", action="store_true", help="If set, log actions without writing to Secret Manager.")
    args = parser.parse_args()

    pages = query_database(args.notion_token, args.db_id)
    if not pages:
        print("No pages returned from Notion; verify database ID and permissions.")
        return
    print(f"Fetched {len(pages)} pages from Notion database.")

    client = secretmanager.SecretManagerServiceClient() if not args.dry_run else None
    synced = 0
    for page in pages:
        props = page.get("properties", {}) or {}
        # Extract fields
        def get(field: str) -> str:
            prop = props.get(field)
            return extract_text(prop).strip() if prop else ""

        name = get("Name")
        secret_value = get("Secret")
        tenant = get("Tenant")
        system = get("System")
        env = get("Env")

        if not (name and secret_value and tenant and system and env):
            print(f"Skipping page missing required fields: {page.get('id')}")
            continue
        secret_id = build_secret_id(env, tenant, system, name)
        if args.dry_run:
            print(f"Would upsert {secret_id} (len={len(secret_value)})")
        else:
            upsert_secret(client, args.gcp_project, secret_id, secret_value)
            synced += 1

    if not args.dry_run:
        print(f"Synced {synced} secrets to GCP Secret Manager.")


if __name__ == "__main__":
    main()
