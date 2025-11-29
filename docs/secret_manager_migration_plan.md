# Secret Manager Migration Plan

## Introduction

This document outlines the migration from the original `codex/`-prefixed
Secret Manager structure to the new **hierarchical naming** convention for
MAOS (Multi‑Agent Operating System). The new structure organizes secrets
by environment, tenant and system, enabling fine‑grained access control
and easier discovery.

## Current State

Historically, all secrets synchronized from Notion were stored under a
flat `codex/` prefix in Secret Manager. For example, a secret named
`PROD_ACTIV8AI_SLACK_BOT_TOKEN` was stored as:

```
projects/PROJECT_ID/secrets/codex/prod_activ8ai_slack_bot_token
```

While this worked for small scopes, it quickly becomes unwieldy as
multiple tenants and systems are added. It also prevents granular IAM
policies based on environment or system.

## New Hierarchical Structure

Under the new scheme, secret IDs follow this pattern:

```
maos/<env>/<tenant>/<system>/<name>
```

Where:

| Component | Description |
|-----------|------------|
| **env**   | Deployment environment (e.g. `prod`, `staging`, `dev`). |
| **tenant** | Logical tenant or customer (e.g. `activ8ai`, `leverage`). |
| **system** | Subsystem or service category (e.g. `codex_portal`, `slack`, `teamwork`). |
| **name**  | Base key name from the Notion row (e.g. `jwt_secret`, `bot_token`). |

Components are lower‑cased and sanitized to include only
letters, numbers, underscores or hyphens. For instance,
`PROD_ACTIV8AI_CODEX_PORTAL_JWT_SECRET` becomes
`maos/prod/activ8ai/codex_portal/jwt_secret`.

### Benefits

* **Granular IAM**: Access can be restricted to a specific environment,
  tenant or system.
* **Clarity**: The secret ID conveys environment, tenant and purpose at a
  glance.
* **Scalability**: Easily accommodates new tenants and systems.

## Migration Steps

1. **Update Notion schema** to include `Tenant`, `System` and `Env` columns
   in your secrets database. Each row should specify these values.
2. **Deploy the hierarchical sync script** (`notion_to_sm_wif_hierarchical.py`)
   alongside the existing sync script.
3. **Run the hierarchical sync** in a dry run to preview actions:

   ```bash
   python scripts/notion_to_sm_wif_hierarchical.py \
     --notion-token $NOTION_TOKEN \
     --db-id $NOTION_DB_ID \
     --gcp-project $GCP_PROJECT \
     --dry-run
   ```

   Review the list of `maos/…` secret IDs that would be created.
4. **Perform a real run** (without `--dry-run`) to create the hierarchical
   secrets and new versions:

   ```bash
   python scripts/notion_to_sm_wif_hierarchical.py \
     --notion-token $NOTION_TOKEN \
     --db-id $NOTION_DB_ID \
     --gcp-project $GCP_PROJECT
   ```

5. **Verify secrets in GCP** using the Cloud Console or CLI:

   ```bash
   gcloud secrets list --filter="name~maos/" --format="value(name)"
   ```

6. **Update downstream workflows** to reference the new hierarchical IDs.
   For GitHub Actions, the fetch workflow should now retrieve secret
   names like `maos/prod/activ8ai/codex_portal/jwt_secret` instead of
   `codex/prod_activ8ai_codex_portal_jwt_secret`. The env var will
   automatically map to `MAOS_PROD_ACTIV8AI_CODEX_PORTAL_JWT_SECRET`.
7. **Phase out old secrets** by removing the `codex/…` secrets once all
   consumers have switched to the hierarchical names. Do this only after
   verifying no references remain.

## Considerations

* **Tenant vs. Domain**: The `tenant` component distinguishes separate
  customers or internal business units. For multi‑domain organizations like
  Leverage Marketing Agency, you might set `tenant` to `leverage` and
  differentiate surfaces in the `system` or `name` field if necessary.
* **Global Secrets**: Secrets that apply to multiple tenants (e.g. CDP
  keys) can use `global` as the tenant component: `maos/prod/global/cdp/...`.
* **Access Control**: Grant IAM roles on prefixes. For example, a
  Slack integration service account for Activ8 AI can be granted access
  only to `maos/prod/activ8ai/slack/*`.

## Rollback Plan

The migration is additive: hierarchical secrets are created alongside
existing ones. To rollback, simply continue using the old `codex/…`
prefix and ignore the new secrets. Once confident, deprecate the old
secrets to avoid confusion and cost.

## Conclusion

Moving to the hierarchical Secret Manager structure improves clarity,
security and scalability. Follow this plan to migrate gradually and
ensure all dependent workflows, agents and services update their
configurations accordingly.
