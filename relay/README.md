# Refresh relay

A Cloudflare Worker that lets the site's **Refresh** button start the "Refresh odds"
workflow. The site is static, so it cannot hold a GitHub token; the Worker holds one,
accepts requests only from the published site, and refuses a new refresh within 15 minutes
of the last one's start (scheduled or manual). Until it is set up, the button stays hidden
and the site works as before.

Everything runs on free tiers: Cloudflare Workers allows 100,000 requests a day, and the
token makes a few GitHub API calls per page load.

## 1. Create the GitHub token

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
   → **Generate new token**.
2. Name it `ffapp-refresh-relay`, pick an expiration (GitHub's maximum is a year; set a
   reminder to renew it).
3. Repository access: **Only select repositories** → this repository.
4. Repository permissions: **Actions: Read and write**. Leave everything else at
   "No access". (Metadata: Read-only is added automatically.)
5. Generate and copy the token. It can start and list workflow runs in this one repository
   and nothing else: it cannot push code or read private data.

## 2. Create the Worker

1. Sign up at <https://dash.cloudflare.com> (free plan).
2. From this folder, deploy the Worker with Wrangler (Cloudflare's CLI, run through `npx`,
   nothing to install globally):

   ```bash
   cd relay
   npx wrangler login
   npx wrangler deploy worker.js --name ffapp-refresh --compatibility-date 2026-11-01
   ```

   Wrangler prints the Worker's address, e.g. `https://ffapp-refresh.<your-account>.workers.dev`.

## 3. Set the Worker's settings

```bash
npx wrangler secret put GITHUB_TOKEN --name ffapp-refresh   # paste the token when asked
```

Then in the Cloudflare dashboard → Workers & Pages → `ffapp-refresh` → Settings →
Variables and secrets, add two plain-text variables:

| Name | Value |
|---|---|
| `REPO` | `tgraham1212/Fantasy-Football-App` (owner/name of this repository) |
| `SITE_ORIGIN` | `https://tgraham1212.github.io` (the published site's origin, no path, no trailing slash) |

Optional: `WORKFLOW` (default `refresh.yml`) and `REF` (default `main`).

Check it from a terminal (the origin header must match `SITE_ORIGIN`):

```bash
curl -H "Origin: https://tgraham1212.github.io" https://ffapp-refresh.<your-account>.workers.dev/status
# {"available":true,"minutes":0,"last_start":null}
```

## 4. Turn the button on

Add the Worker's address to `config/leagues.yaml`:

```yaml
site:
  refresh_url: https://ffapp-refresh.<your-account>.workers.dev
```

Commit and push; the next refresh's export puts the address in `site/data/index.json` and
the button appears on both pages.

## How it decides

- `GET /status` → `{available, minutes, last_start}`; `POST /refresh` → `202 {started}` or
  `429 {minutes}`. Any other origin gets `403` and GitHub is never called.
- It lists the workflow's runs from the last 15 minutes. A manual run counts from when it
  was created (queued runs included); a scheduled run counts only if its `refresh` job ran,
  so hourly checks that decided not to refresh do not hold the button.
- GitHub can take a few seconds to list a run it just started, so the Worker also remembers
  its own last dispatch; two clicks a few seconds apart start one run.

## Tests

```bash
node --test relay/worker.test.mjs
```

## Turning it off

Remove `site.refresh_url` from the config (the button disappears on the next deploy), then
delete the Worker in the Cloudflare dashboard and revoke the token on GitHub.
