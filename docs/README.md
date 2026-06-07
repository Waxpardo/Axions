# Documentation Index

This directory is the human-facing project notebook. It contains setup guides,
runbooks, physics assumptions, validation notes, and references.

## Start Here

| File | Use |
|---|---|
| `final-analysis-rundown.md` | Current end-to-end status, methods, assumptions, commands, and limitations. |
| `project-status.md` | Short checklist of what is complete and what remains. |
| `report-and-presentation-outline.md` | Map from repo artifacts to the final report and slide deck. |
| `repository-build-and-pipeline-report.md` | Full narrative of how the repo was built, why choices were made, branch integration, and full pipeline execution. |
| `file-provenance-report.md` | File-by-file provenance: authored, generated, imported, downloaded, and derived files. |
| `detector-assumptions-fccee-zpole.md` | FCC-ee detector and analysis assumptions. |
| `belle2-closure-test.md` | Belle II public-contour closure details and metrics. |
| `fccee-zpole-projection-2026-06-05.md` | FCC-ee projection note and production history. |
| `alp-full-pipeline-verification-2026-06-05.md` | Detector-level ALP pipeline verification note. |

## Nikhef Setup

| File | Use |
|---|---|
| `nikhef-first-login-github-ssh.md` | First cluster login, `/data/alice/<username>`, and GitHub SSH setup. |
| `nikhef-mg5-pythia-hepmc-smoke-test.md` | Software-chain setup and smoke-test guide. |
| `nikhef-vscode-remote-ssh-guide.md` | VS Code Remote SSH setup for login and Stoomboot nodes. |

## Project References

| File | Use |
|---|---|
| `references.bib` | Bibliography entries for the report. |
| `branch-audit-2026-06-05.md` | Historical branch audit. |
| `project-strategy-fccee-money-plot.md` | Strategy notes for constraints and projection plotting. |

## Documentation Policy

Use the root `README.md` for the stable top-level map. Use this `docs/`
directory for longer context and run history.

When an assumption becomes part of the final result, put the machine-readable
value in `analysis/configs/` and explain it in:

```text
docs/final-analysis-rundown.md
docs/detector-assumptions-fccee-zpole.md
```

When a production campaign changes a result, update the relevant summary JSON in
`results/` and record the command or campaign ID in the appropriate note.
