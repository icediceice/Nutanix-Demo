# Codex Instructions (Nutanix-Demo)

This repo is a branch-driven GitOps demo. Prefer reading targeted docs and making small, scoped changes.

## First: Use The Architecture Doc (Avoid AGENTS.md Bloat)
- Architecture and repo structure live in `docs/architect.md`.
- When you need architecture context, open `docs/architect.md` and read only the relevant section(s).
- If you need deep details, follow links from `docs/architect.md` (for example `docs/demo-spec.md`) instead of loading large docs by default.

## Operator Docs (When The Task Is “How Do I Run This Demo?”)
- Start here: `partner/QUICKSTART.md`
- Full runbook: `partner/RUNBOOK.md`
- Copy/paste commands: `partner/COMMANDS.md`
- Scenario matrix: `partner/SCENARIOS.md`
- Troubleshooting/reset: `partner/TROUBLESHOOTING.md`, `partner/RESET.md`

## Working Rules (Repo-Specific)
- The demo is controlled by switching ArgoCD `targetRevision` to a `scenario/*` branch; do not rely on live-editing YAML in the cluster.
- Do not open/merge PRs from `scenario/*` into `main`; `scenario/*` represent runtime demo states.
- Avoid “two controllers manage the same resources”: ArgoCD should be the GitOps driver for the demo namespaces.
- Never commit secrets or kubeconfigs. `auth/` is intentionally git-ignored.

## Token Discipline (How To Explore)
- Prefer `rg` for discovery and open only the files you need.
- When inspecting large files, use `sed -n '1,200p' <file>` style slices.
- For manifests, validate with `kubectl kustomize <path>` (or `kustomize build <path>`) when available.

