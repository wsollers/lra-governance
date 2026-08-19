# Repo Overlay -- lra-dashboard

Repo identity: Validator progress dashboard (static site).

Static GitHub Pages dashboard for LRA validator progress across the
`lra-volume-*` repositories. The site reads
`public/data/dashboard-data.json`, generated from GitHub issues labeled
`lra-validator`; local development falls back to
`public/data/dashboard-data.sample.json` when the generated file is absent.

Rules:

- Keep the dashboard static and dependency-light unless a build step becomes
  genuinely necessary.
- Generated dashboard data belongs under `public/data/dashboard-data.json`;
  do not hand-edit generated data.
- Shared issue export logic lives in `lra-governance`
  (`tools/governance/export_validator_issue_dashboard.py`); do not duplicate
  GitHub issue parsing here.
- Private volume repositories require the `LRA_DASHBOARD_PAT` repository
  secret with read access; public repos use the default `GITHUB_TOKEN`.

Success gates:

- `public/data/dashboard-data.json` (or the sample file) parses as JSON when
  changed.
- The site renders by opening `public/index.html` or serving the `public/`
  directory with any static server.
