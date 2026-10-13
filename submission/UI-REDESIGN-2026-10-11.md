# Lumen UI redesign — 11 October 2026

This dated delivery contains the redesigned Lumen interface: a compact research workspace, a larger anatomy stage, clearer case/input and estimate panels, responsive layouts, readable chart colors, and self-hosted Figtree typography. The scientific procedure, input definitions, fitted models, thresholds, recorded labels, and frozen evaluation are retained.

## Current interface source

The presentation changes are in `public/index.html`, `public/style.css`, `public/app.js`, `public/evidence-journey.js`, `public/cohort-audit.js`, and `public/anatomy-controls.js`. The font and SIL Open Font License are in `public/assets/fonts/`. See `research/ui-redesign-2026-10-11/DESIGN.md` for the design contract and `research/ui-redesign-2026-10-11/font-provenance.json` for the exact font/license provenance. `THIRD_PARTY_NOTICES.md` records the attribution.

## Dated exports

The portable browser build is `dist/ui-redesign-2026-10-11/site/`; its exact payload is listed by `static-manifest.json`. The browser ZIP is `output/lumen-browser-ui-redesign-2026-10-11.zip`, with the site under `lumen-browser/`. Serve the extracted directory over HTTP rather than opening `index.html` directly:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory lumen-browser
```

The source ZIP is `dist/release-ui-redesign-2026-10-11/lumen-submission-source.zip`, with the source under `lumen/`. Its release manifest lists each payload file with SHA-256 and byte size. From the extracted source:

```sh
npm ci --ignore-scripts --no-audit --no-fund
python3 server.py
```

The source represents the reviewed local working tree based on commit `9a11b4a55761080324f20a9ac33d86c2426aaed2`. The UI changes are uncommitted; the export does not assert that its contents equal that Git commit. No new commit, push, repository, or account action is part of this delivery.

The final Node run reports 53 passing tests and zero failures; its journey runner also exercises 64 comparison assertions. The earlier Python run passed all 20 tests after the initial UI logic update; backend and model files remained unchanged through the final frontend changes. The responsive review covered the final desktop, tablet, and phone states without unresolved findings. These are software and browser checks, not human usability evidence.

## Scope and publication state

The static browser contains eight original public development examples and the outcome-aware 242-record development audit across five input profiles. It includes aggregate frozen final-test evidence and no final holdout inputs. The original 61-record final evaluation is preserved; this UI delivery does not retrain models or rescore that holdout.

Older reports, films, kits, and upload staging remain historical. Any older film or PDF retained in the source export describes its own dated presentation; the old film does not show this redesign. The prior 349-file GitHub upload staging folder must not be published as the new-look application. Use the dated source or browser export for the redesigned interface.

Public GitHub/demo/YouTube URLs, real human information and eligibility, human signoff, and the final Devpost submission remain pending. Preserve AI assistance disclosure and the existing one-track restriction. Local export verification does not constitute publication or human usability validation.

Exact archive hashes and verification receipts are recorded outside the archives in `output/UI-REDESIGN-HANDOFF-2026-10-11.md` and dated sidecar JSON files. This keeps archive identity checks free of self-reference.
