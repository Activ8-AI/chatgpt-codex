#!/usr/bin/env python3
"""
Codex Portal Secret Loader
==========================

This helper module encapsulates the logic for loading secrets from
Google Secret Manager into the Codex Portal runtime. It resolves the
tenant and surface from the incoming HTTP host header and then fetches
all secrets under the appropriate `maos/<env>/<tenant>/` hierarchy.

The primary entry point is `load_secrets_for_request(host: str, env: str)`,
which returns a dictionary of secrets keyed by their secret name. The
function performs the following steps:

1. **Resolve tenant and surface** from the host (e.g.
   `activ8ai.app` → (`activ8ai`, `codex_portal`)).
2. **Identify systems** needed for the surface. For the Codex Portal this
   typically includes `codex_portal`, `slack`, `teamwork`, `hubspot`, and
   optionally `cdp` and `email_auto` depending on features.
3. **List and fetch secrets** from Secret Manager using the
   `google-cloud-secret-manager` API. Only secrets under
   `maos/<env>/<tenant>/<system>/` are retrieved.
4. **Return a mapping** where keys are uppercased environment variable
   names (e.g. `MAOS_PROD_ACTIV8AI_CODEX_PORTAL_JWT_SECRET`) and values
   are the secret strings.

This module can be imported into the Codex Portal backend (e.g. a FastAPI
app) and called during startup or per request. Secrets are cached in
memory for the duration of the process to minimize Secret Manager calls.

Note: The module depends on `google-cloud-secret-manager`. The
environment should be authenticated via Workload Identity or another
supported mechanism.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple

from google.cloud import secretmanager


@dataclass
class TenantSurface:
    tenant: str
    surface: str


def resolve_tenant_surface(host: str) -> TenantSurface:
    """Determine the tenant and surface from the request host.

    The mapping is based on domain conventions:

    * `activ8ai.app` → (`activ8ai`, `codex_portal`)
    * `clients.leverageway.com` → (`leverage`, `client_portal`)
    * `partners.leverageway.com` → (`leverage`, `partner_portal`)
    * `leverageway.com` → (`leverage`, `marketing_site`)
    * any other host returns (`unknown`, `unknown`)
    """
    host = host.lower()
    if host == "activ8ai.app":
        return TenantSurface("activ8ai", "codex_portal")
    if host == "leverageway.com":
        return TenantSurface("leverage", "marketing_site")
    if host == "clients.leverageway.com":
        return TenantSurface("leverage", "client_portal")
    if host == "partners.leverageway.com":
        return TenantSurface("leverage", "partner_portal")
    # Fallback: derive tenant from second level domain if possible
    m = re.match(r"([^.]+)\.([^.]+)\.([^.]+)", host)
    if m:
        sub, domain, tld = m.groups()
        # simple heuristic: treat the parent domain as the tenant
        tenant = domain
        return TenantSurface(tenant, sub)
    return TenantSurface("unknown", "unknown")


def list_secret_names(client: secretmanager.SecretManagerServiceClient, project: str, prefix: str) -> List[str]:
    """List secret IDs under a given prefix in a GCP project."""
    parent = f"projects/{project}"
    secret_names = []
    for secret in client.list_secrets(request={"parent": parent}):
        name = secret.name.split("/secrets/")[1]
        if name.startswith(prefix):
            secret_names.append(name)
    return secret_names


def fetch_secret(client: secretmanager.SecretManagerServiceClient, project: str, secret_id: str) -> str:
    """Access the latest version of a secret."""
    name = f"projects/{project}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")


@lru_cache(maxsize=32)
def load_secrets_for_request(host: str, env: str, project: str) -> Dict[str, str]:
    """Load secrets for the given host and environment.

    Args:
        host: The incoming request host header (e.g. 'activ8ai.app').
        env: Deployment environment (`prod`, `staging`, `dev`, etc.).
        project: GCP project ID where secrets are stored.

    Returns:
        A dictionary mapping environment variable names to secret values.
    """
    ts = resolve_tenant_surface(host)
    tenant = ts.tenant
    # Determine which systems are relevant for the surface
    systems: List[str] = []
    if ts.surface == "codex_portal":
        systems = ["codex_portal", "slack", "teamwork", "hubspot", "cdp", "email_auto"]
    elif ts.surface in ("client_portal", "partner_portal"):
        systems = ["codex_portal", "hubspot"]
    elif ts.surface == "marketing_site":
        systems = ["marketing_site"]
    else:
        systems = []

    client = secretmanager.SecretManagerServiceClient()
    secrets: Dict[str, str] = {}
    for system in systems:
        prefix = f"maos/{sanitize(env)}/{sanitize(tenant)}/{sanitize(system)}/"
        names = list_secret_names(client, project, prefix)
        for name in names:
            value = fetch_secret(client, project, name)
            # Convert to env var name (uppercase, slashes to underscores)
            env_var = name.replace("/", "_").upper()
            secrets[env_var] = value
    return secrets


def sanitize(s: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "_", s.lower())


__all__ = [
    "load_secrets_for_request",
    "resolve_tenant_surface",
]
