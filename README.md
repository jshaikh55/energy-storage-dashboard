# Energy Storage Briefing Dashboard

A self-updating dashboard tracking energy storage market news, technology
developments, and regulatory/policy changes. Runs entirely on GitHub's free
tier: GitHub Actions calls the Claude API (with web search) once a day,
writes the results as JSON, and GitHub Pages serves a static page that
displays it. No server to maintain.

Today's briefing is already seeded in `docs/data/` so the page works the
moment you turn on Pages — the daily Action will keep it fresh from there.

## Setup (about 10 minutes)

### 1. Create the repo
Create a new **public** GitHub repository (Pages' free tier requires public,
unless you have GitHub Pro/Team/Enterprise) and push all these files to it:

```bash
cd energy-storage-dashboard
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 2. Get an Anthropic API key
Go to [console.anthropic.com](https://console.anthropic.com), create an API
key. Note that this uses pay-as-you-go API credits (separate from a
claude.ai subscription) — one run per day costs a small fraction of a cent
to a few cents depending on how much searching the model does, so expect
well under $1/month.

### 3. Add the key as a GitHub secret
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**
- Name: `ANTHROPIC_API_KEY`
- Value: (paste your key)

### 4. Turn on GitHub Pages
**Settings → Pages** → under "Build and deployment", set:
- Source: `Deploy from a branch`
- Branch: `main`, folder: `/docs`
- Save

GitHub will give you a URL like `https://<your-username>.github.io/<your-repo>/`.
It can take a minute or two to go live the first time.

### 5. Test the automation
Go to the **Actions** tab → "Update Energy Storage Dashboard" → **Run
workflow** to trigger it manually and confirm it works, rather than waiting
for the schedule. Check the workflow logs if anything fails — the most
common issue is a missing/incorrect `ANTHROPIC_API_KEY` secret.

From then on, it runs automatically every day at 12:00 UTC (edit the `cron`
line in `.github/workflows/update.yml` to change the time — cron times are
always UTC).

## How it works

- `scripts/generate_dashboard.py` — asks Claude to research the day's
  developments across three categories (market/deployment, technology,
  regulatory/policy) using its web search tool, and returns structured JSON.
- `.github/workflows/update.yml` — the daily cron job that runs the script
  and commits the new data.
- `docs/index.html` — the static page, reads `docs/data/latest.json` and
  `docs/data/manifest.json` (list of past dates) client-side. No build step.
- `docs/data/history/YYYY-MM-DD.json` — one snapshot per day, kept for
  ~60 days so you can look back via the date dropdown.

## Customizing

- **Categories/sources**: edit the `PROMPT` in `generate_dashboard.py` —
  e.g. add a "Company earnings" category, or ask it to prioritize specific
  publications.
- **Frequency**: change the `cron` schedule, or add a second scheduled run
  for twice-daily updates.
- **Look**: all styling is in `docs/index.html` in a single `<style>` block
  — colors are set as CSS variables at the top.
- **Email instead of/alongside a webpage**: you could add a step to the
  workflow that emails the JSON summary (e.g. via a service like SendGrid)
  if you'd rather get it pushed to your inbox too.

## Cost

- GitHub Actions: free for public repos.
- GitHub Pages hosting: free.
- Anthropic API: roughly a few cents/day depending on how many searches the
  model runs — check current pricing at
  [anthropic.com/pricing](https://www.anthropic.com/pricing).
