# One-time setup / Configuración inicial

About 15 minutes. Needs: owner access to the GitHub repo, and to the Google Cloud project
registered for Earth Engine (currently `hab-quiz-ae5a8`).

## 1. Service account for Earth Engine

1. Open https://console.cloud.google.com/iam-admin/serviceaccounts and select the project.
2. **Create service account**, name e.g. `s2-monitor`.
3. Grant these roles to it:
   - **Earth Engine Resource Viewer** (`roles/earthengine.viewer`)
   - **Service Usage Consumer** (`roles/serviceusage.serviceUsageConsumer`)
4. Open the account → **Keys** → **Add key** → **Create new key** → JSON. A file downloads.
   Treat it like a password and never commit it.
5. Check that the **Earth Engine API** is enabled for the project
   (APIs & Services → Library → "Google Earth Engine API").

## 2. GitHub secret

Repo → **Settings → Secrets and variables → Actions → New repository secret**
- Name: `EE_SERVICE_ACCOUNT_KEY`
- Value: the full content of the JSON file.

Then delete the downloaded file from your computer.

The project is read from the key. To force another one, add a repository *variable*
(not secret) `EE_PROJECT`.

## 3. GitHub Pages

Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.

## 4. First run (backfill since 2017)

Repo → **Actions → Update data → Run workflow**
- `full_rebuild`: ticked
- `max_images`: `2000` (renders all images in one run, ~1–2 h), or leave 300 and let
  the daily runs finish the backfill over a few days.

When it is green, the dashboard is at `https://kristofm854.github.io/embalses-s2-monitor/`.

## Handing over / Traspaso

- **Move the repo to a team account or organisation:** Settings → General → Transfer.
  Secrets go with the repo. The Pages URL changes to the new owner's name.
- **Switch to a team-owned Google Cloud project:** register the new project for
  non-commercial Earth Engine use (https://code.earthengine.google.com/register), repeat
  step 1 there, and replace the secret in step 2. Then disable the old key.
- **Add maintainers:** Settings → Collaborators. Ask them to **Watch** the repo so they
  get failure e-mails.

## Optional: no stored key

Instead of a JSON key, GitHub can authenticate to Google with Workload Identity Federation
(`google-github-actions/auth`). This is more secure but takes more setup. The pipeline
falls back to application-default credentials when no key secret is set, so it should work
without code changes, but this path is untested.
