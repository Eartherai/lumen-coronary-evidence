# Lumen final local review kit — 10 October 2026

Lumen makes a coronary prediction traceable and challengeable: compare one recorded case across five independently fitted input profiles, select a source-identified reference artery, inspect the complete SHAP score, then reveal a recorded mistake.

This dated kit contains polished submission copy and the exact evidence behind it. It is a documentation overlay for local human review. The project has not been published or submitted by preparing this kit. The existing application, frozen models, evaluation, six-page report and verified narrated video remain the authoritative artifacts.

## Review in this order

1. [Devpost copy](devpost-ready.md): ready to paste after actual links and human fields are completed.
2. [Built With values](built-with.json): technology tags, required AI disclosures and source resources.
3. [Judge walkthrough](judge-walkthrough.md): a three-minute live route through concrete controls, plus exact saved examples.
4. [Publication handoff](publication-handoff.md): source, video, optional hosted demo and final submission steps.
5. [Human review checklist](review-checklist.md): specific checks before an entry is submitted.
6. [Claim ledger](claims.md) and [structured claims](claims.json): sources, scope and limitations for every material claim.
7. [Unresolved fields](handoff-fields.json): real people, account/eligibility, publication URLs and final receipt.
8. [Source snapshot](source-manifest.json): SHA-256 identities for the unchanged material used by this kit.

## Existing deliverables

- Source release: `../../dist/lumen-submission-source.zip` (35,626,895 bytes at this snapshot).
- Six-page report: `../../output/pdf/lumen-report.pdf`.
- English narrated video: `../../output/video/lumen-demo.mp4` (4 minutes 40.46 seconds).
- Python/local run: `npm ci`, then `python3 server.py` from the project root; open `http://127.0.0.1:8766/`.
- Optional static judge demo: existing `dist/site`; public URL is pending.

The supplied submission guidelines require project description, a public GitHub repository with README setup/run instructions, a 3–10-minute public/unlisted YouTube demonstration with English audio or subtitles, and real full names plus Devpost accounts for every actual teammate. Track A also limits the technical report to six pages. The [official rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules), rechecked by the root reviewer on 10 October, permit one track per team and one submitting team per individual. Preparing Lumen and Akash locally does not authorize a second entry by an overlapping team.

## What still requires completion

Actual human names/accounts and eligibility; the permitted submitting team/track; human code/evidence/narration review and rehearsal; ordinary-browser performance evidence; confirmed public GitHub and public/unlisted YouTube links; optional hosted-demo verification; and the actual Devpost confirmation. Existing release status keeps these fields unresolved. This kit does not invent identities, URLs or completion status.

The release archive in this snapshot passed its recorded clean-extraction verification. If a later source change is included in the public release, use the newly verified archive and update the publication hashes; a documentation snapshot cannot certify a changed archive. No training, tests, inference calls, holdout scoring or media rerendering were performed to create this kit.
