# Agent Secret Contracts

This document defines the **expected secret contracts** between MAOS
domain agents and the environment in which they run. Each agent is
responsible for interacting with a particular system (e.g. Slack,
Teamwork, HubSpot). To function, the agent must have specific
credentials and configuration values made available via environment
variables. These variables are typically populated by the
`fetch_secrets_from_secretmanager.yml` workflow, which reads secret
values from GCP Secret Manager.

## Naming Conventions

Environment variable names follow this pattern:

```
MAOS_<ENV>_<TENANT>_<SYSTEM>_<KEY>
```

* **ENV**: Deployment environment (PROD, STAGING, DEV, etc.).
* **TENANT**: Tenant identifier (e.g. ACTIV8AI, LEVERAGE).
* **SYSTEM**: System name (e.g. SLACK, TEAMWORK, HUBSPOT).
* **KEY**: Specific key purpose (e.g. BOT_TOKEN, API_KEY).

The `fetch_secrets_from_secretmanager.yml` workflow automatically
converts Secret Manager IDs into environment variables by uppercasing
and replacing `/` separators and punctuation with underscores.

## Slack Agent

The Slack agent posts messages, receives events and operates a bot. It
requires the following secrets:

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_SLACK_BOT_TOKEN` | OAuth bot token used to call Slack APIs. |
| `MAOS_<ENV>_<TENANT>_SLACK_SIGNING_SECRET` | Signing secret for verifying Slack requests (slash commands, interactions). |
| `MAOS_<ENV>_<TENANT>_SLACK_APP_LEVEL_TOKEN` | Optional: token for Socket Mode if using it. |

## Teamwork Agent

The Teamwork agent manages tasks and projects. Required secrets:

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_TEAMWORK_API_KEY` | API key for authenticating with Teamwork. |
| `MAOS_<ENV>_<TENANT>_TEAMWORK_BASE_URL` | Base URL of the Teamwork site (e.g. `https://company.teamwork.com`). |

## Recording/Transcripts Agent

Responsible for fetching and processing meeting transcripts from
integrations like Fathom, Zoom, or Gong.

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_FATHOM_API_KEY` | API key for Fathom (if used). |
| `MAOS_<ENV>_<TENANT>_ZOOM_JWT_SECRET` | JWT secret or OAuth client secret for Zoom. |
| `MAOS_<ENV>_<TENANT>_GONG_API_TOKEN` | API token for Gong. |

Only include the keys that correspond to the integrations in use. The
agent should check for the presence of each before enabling that
integration.

## Google Drive Agent

Handles document ingestion from Google Drive.

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_GDRIVE_SA_JSON` | Service account JSON (base64 or raw). |
| `MAOS_<ENV>_<TENANT>_GDRIVE_CLIENT_ID` | OAuth client ID (if using OAuth). |
| `MAOS_<ENV>_<TENANT>_GDRIVE_CLIENT_SECRET` | OAuth client secret (if using OAuth). |
| `MAOS_<ENV>_<TENANT>_GDRIVE_REFRESH_TOKEN` | Refresh token (if using OAuth). |

## HubSpot/CRM Agent

Integrates with HubSpot to manage contacts, companies and deals.

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_HUBSPOT_PRIVATE_APP_TOKEN` | Private app token for HubSpot APIs. |
| `MAOS_<ENV>_<TENANT>_HUBSPOT_PORTAL_ID` | HubSpot portal (account) ID. |

Depending on the integration, you may also require `HUBSPOT_CLIENT_ID`
and `HUBSPOT_CLIENT_SECRET` for OAuth-based flows.

## CDP Agent (Segment/RudderStack)

Emits customer events and user traits to a Customer Data Platform (CDP).

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_SEGMENT_WRITE_KEY` | Write key for Segment or RudderStack. |
| `MAOS_<ENV>_<TENANT>_SEGMENT_SOURCE_ID` | Source ID (if required). |

## Email/Marketing Automation Agent

Manages email flows through Klaviyo, Mailchimp, Customer.io or
similar platforms. Only the relevant platform keys need to be
present.

| Environment Variable | Description |
|----------------------|-------------|
| `MAOS_<ENV>_<TENANT>_KLAVIYO_PRIVATE_API_KEY` | Private API key for Klaviyo. |
| `MAOS_<ENV>_<TENANT>_KLAVIYO_PUBLIC_API_KEY` | Public API key for Klaviyo (some operations require both). |
| `MAOS_<ENV>_<TENANT>_KLAVIYO_MAIN_LIST_ID` | Default list ID for Klaviyo. |
| `MAOS_<ENV>_<TENANT>_MAILCHIMP_API_KEY` | API key for Mailchimp. |
| `MAOS_<ENV>_<TENANT>_MAILCHIMP_SERVER_PREFIX` | Mailchimp server prefix (e.g. `us1`). |
| `MAOS_<ENV>_<TENANT>_MAILCHIMP_LIST_ID` | Default audience/list ID for Mailchimp. |
| `MAOS_<ENV>_<TENANT>_CUSTOMERIO_SITE_ID` | Site ID for Customer.io (if using). |
| `MAOS_<ENV>_<TENANT>_CUSTOMERIO_API_KEY` | API key for Customer.io. |

## Notes

* Agents should **never log secret values**. Only the names of the
  environment variables and masked values should appear in logs.
* Each agent should validate the presence of required env vars at
  startup and provide clear error messages if missing.
* Secrets that are common across tenants (e.g. a global CDP key) may
  reside under the `global` tenant and be surfaced as
  `MAOS_<ENV>_GLOBAL_<SYSTEM>_<KEY>`. Agents should look for
  tenant‑specific keys first and fall back to `GLOBAL` if present.

Adhering to these contracts ensures that domain agents can be
configured consistently across environments and tenants, promoting
security and maintainability.
