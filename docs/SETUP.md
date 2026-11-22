# One-time setup / Configuración inicial

About 15 minutes. Needs: owner access to the GitHub repo, and to the Google Cloud project
registered for Earth Engine (currently `hab-quiz-ae5a8`).

German labels of the Google Cloud console are given in [brackets]. GitHub has no German
interface, so GitHub menu names are given in English only.

## 1. Service account for Earth Engine

1. Open https://console.cloud.google.com/iam-admin/serviceaccounts
   (**IAM & Admin → Service Accounts** [**IAM und Verwaltung → Dienstkonten**]) and select
   the project at the top (**Select a project** [**Projekt auswählen**]).
2. **Create service account** [**Dienstkonto erstellen**], name e.g. `s2-monitor`, then
   **Create and continue** [**Erstellen und fortfahren**].
3. Under **Grant this service account access to project** [**Diesem Dienstkonto Zugriff
   auf das Projekt gewähren**] → **Select a role** [**Rolle auswählen**], add these two roles:
   - **Earth Engine Resource Viewer** (`roles/earthengine.viewer`)
   - **Service Usage Consumer** (`roles/serviceusage.serviceUsageConsumer`)

   Role names are translated in the German console. Type the role ID into the filter
   (`earthengine.viewer`, `serviceUsageConsumer`) to find them in any language.
   Then **Continue** [**Weiter**] → **Done** [**Fertig**].
4. Open the account → **Keys** [**Schlüssel**] → **Add key** [**Schlüssel hinzufügen**] →
   **Create new key** [**Neuen Schlüssel erstellen**] → key type **JSON** [**Schlüsseltyp:
   JSON**] → **Create** [**Erstellen**]. A file downloads. Treat it like a password and
   never commit it.

   If key creation is blocked with a message about an organisation policy
   [**Organisationsrichtlinie**] (`iam.disableServiceAccountKeyCreation`), the project
   belongs to an organisation that forbids keys. Use a personal project, or see
   "Optional: no stored key" below.
5. Check that the **Earth Engine API** is enabled for the project. Direct link:
   https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project=hab-quiz-ae5a8
   (change `project=` for another project). Click **Enable** [**Aktivieren**]. If the
   button says **Manage** [**Verwalten**], it is already enabled. If Earth Engine already
   works with this project (e.g. from R or Python), this is always the case.

   Via the menu: **☰** (top left) → **APIs & Services → Library** [**APIs und Dienste →
   Bibliothek**] (if not listed: **View all products** [**Alle Produkte anzeigen**]), or type
   "Earth Engine API" into the search bar at the top of the console.

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

Then open `data/aoi_Valdesia.geojson` and `data/aoi_Hatillo.geojson` on GitHub (shown on
a map) and check that the outlines fit. If a run log shows a warning that the outline
reaches the edge of the search circle, increase `radius_m` in `pipeline/config.py`. To
correct an outline by hand, see `data/aoi_overrides/README.md`.

## Handing over / Traspaso

- **Move the repo to a team account or organisation:** Settings → General → Transfer.
  Secrets go with the repo. The Pages URL changes to the new owner's name.
- **Switch to a team-owned Google Cloud project:** register the new project for
  non-commercial Earth Engine use [nicht kommerzielle Nutzung]
  (https://code.earthengine.google.com/register), repeat
  step 1 there, and replace the secret in step 2. Then disable the old key (service
  account → **Keys** [**Schlüssel**] → delete icon [**Löschen**]).
- **Add maintainers:** Settings → Collaborators. Ask them to **Watch** the repo so they
  get failure e-mails.

## Optional: no stored key

Instead of a JSON key, GitHub can authenticate to Google with Workload Identity Federation
[Workload Identity-Föderation, under **IAM & Admin** [**IAM und Verwaltung**]]
(`google-github-actions/auth`). This is more secure but takes more setup. The pipeline
falls back to application-default credentials when no key secret is set, so it should work
without code changes, but this path is untested.
