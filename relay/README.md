# Refresh relay

A Cloudflare Worker with three jobs (the whole design: [`docs/refresh-modes.md`](../docs/refresh-modes.md)):

- **The refresh clock.** Every minute it works out the refresh mode (Off-season, Quiet or Live)
  and starts the GitHub workflows that are due: `hot.yml` back to back during games and every
  15 minutes otherwise in season, `refresh.yml` (the cold run) every 15 minutes in season and
  when a slate of games goes final.
- **The live bundle.** Each hot run uploads this week's live forecast and game cards as one
  bundle; the Worker keeps it in a KV namespace and the site's pages fetch it.
- **The Refresh Data button.** The site is static, so it cannot hold a GitHub token; the Worker
  holds one, accepts button presses only from the published site, and starts a hot and a cold
  run (a cold run in the off-season), at most once every 5 minutes and never while games are in
  progress (they refresh every minute anyway).

Until it is set up the button stays hidden, there are no live updates, and the site refreshes
once a day from GitHub's own schedule.

Everything runs on free plans: Cloudflare Workers allows 100,000 requests a day and KV 1,000
writes a day (the Worker keeps to under 1,000: one write per hot run, skipped when nothing
changed and stopped at 950 a day).

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

## 2. Create the hot-run secret

The hot and cold runs prove who they are to the Worker with a shared secret, `HOT_TOKEN`: any
long random string, kept in two places and nowhere else.

1. Make one, for example in PowerShell:
   `[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))`
2. GitHub → this repository → Settings → Secrets and variables → Actions → **New repository
   secret**: name `HOT_TOKEN`, the string as its value.
3. Keep it to hand for step 4.

## 3. Create the Worker and its KV namespace

1. Sign up at <https://dash.cloudflare.com> (free plan) and register your account's
   `workers.dev` subdomain (dashboard → **Workers & Pages**; once per account).
2. From this folder, log in and create the KV namespace:

   ```bash
   cd relay
   npx wrangler login
   npx wrangler kv namespace create LIVE
   ```

   Wrangler prints an `id`. Paste it into `wrangler.toml` in place of
   `PASTE_THE_KV_NAMESPACE_ID_HERE` (the id is not a secret; commit it).
3. Check `REPO` and `SITE_ORIGIN` in `wrangler.toml` (the published site's origin, no path, no
   trailing slash; change it whenever the site's domain changes, or Refresh Data is refused).
4. Deploy:

   ```bash
   npx wrangler deploy
   ```

   This publishes the Worker, binds the KV namespace as `LIVE` and turns on the clock (a cron
   trigger every minute). Wrangler prints the Worker's address, e.g.
   `https://ffapp-refresh.<your-account>.workers.dev`.

## 4. Set the Worker's secrets

```bash
npx wrangler secret put GITHUB_TOKEN   # paste the token from step 1
npx wrangler secret put HOT_TOKEN      # paste the string from step 2
```

Optional plain variables: `WORKFLOW` (default `refresh.yml`), `HOT_WORKFLOW` (default
`hot.yml`) and `REF` (default `main`).

Check it from a terminal (the origin header must match `SITE_ORIGIN`):

```bash
# in Windows PowerShell type curl.exe: plain curl there is Invoke-WebRequest and rejects -H
curl -H "Origin: https://fantasyfoosball.net" https://ffapp-refresh.<your-account>.workers.dev/status
# {"available":true,"minutes":0,"last_start":null,"mode":"quiet","reason":null}
```

Until the first cold run uploads the schedule summary the mode reads `quiet`, so the clock
starts a cold run within a minute; that run uploads the summary.

## 5. Turn the button and live updates on

The Worker's address goes in `config/leagues.yaml`:

```yaml
site:
  refresh_url: https://ffapp-refresh.<your-account>.workers.dev
```

The workflows read it from there too (to upload the bundle and the schedule summary). Commit
and push; the next deploy puts it in `site/data/index.json` and the pages show the button and
read the live bundle.

## How it decides

- `GET /status` → `{available, minutes, last_start, mode, reason}`, where `reason` is `live`
  (games in progress), `running` (a hot run, or in the off-season a cold run, is going),
  `cooldown` (a button refresh started under 5 minutes ago) or `null`. `POST /refresh` → `202
  {started, mode}`, `409 {reason: "live"}` or `429 {minutes, reason}`. Any other origin gets
  `403` and GitHub is never called.
- `GET /live?since=<time>` → the bundle, or `204` when there is none newer than `since`.
  `PUT /live` and `PUT /schedule` need `Authorization: Bearer <HOT_TOKEN>`; `PUT /live` also
  needs `X-Bundle-Meta` (base64 JSON: the content hash, the time and each game's state), which
  the Worker keeps as the KV entry's metadata so it never has to parse the bundle.
- The mode: Off-season when the summary says no league is in season; Live when a game's
  kickoff has passed and neither the summary nor the latest bundle shows it final (a game
  counts as final 6 hours after kickoff regardless); otherwise Quiet.
- GitHub is the source of truth for runs: the Worker lists the workflow's recent runs. It
  also remembers its own dispatches for a minute, since a new run takes a few seconds to
  show up; two clicks a few seconds apart start one refresh.

## Tests

```bash
node --test relay/worker.test.mjs
```

## Turning it off

Comment out the `[triggers]` block in `wrangler.toml` and deploy again to stop the clock (the
site then refreshes daily from GitHub's schedule), or remove `site.refresh_url` from the config
to hide the button and stop live updates as well. To remove it entirely, delete the Worker
and the KV namespace in the Cloudflare dashboard, revoke the GitHub token and delete the
`HOT_TOKEN` repository secret.
