# Lumen publication handoff — prepared locally

The prepared assets satisfy the local description/source/report/video shape of Track A. The mandatory public links and real human fields are still unresolved. Use `handoff-fields.json` as the single checklist of values to collect; retain actual confirmations after publication.

## Choose the permitted entry

The [current official rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules), checked by the root reviewer on 10 October, allow one track per team and one submitting team per individual. If the same person/team owns both prepared projects, choose one entry. Two entries require distinct eligible teams with no overlapping member. Do not infer a second team from the existence of Akash's local kit. Lumen is the prepared primary Track A candidate; the final team/track selection remains a human field.

The locally recorded deadline is 15 October 2026 at 00:15 IST. Aim to finish by 14 October evening IST, and verify the live event deadline before submitting. This snapshot does not establish a submitted entry, acceptance or award.

## Review the actual deliverables

- Paste-ready project copy: `devpost-ready.md`.
- Source release: `../../dist/lumen-submission-source.zip`.
- Existing clean-extraction record: `../../dist/release-verification.json`.
- Six-page technical report: `../../output/pdf/lumen-report.pdf`.
- English narrated video: `../../output/video/lumen-demo.mp4`.
- Optional browser demo build: `../../dist/site/`.
- README, setup and evidence: `../../README.md`, `../../REPRODUCIBILITY.md`.

The current source ZIP hash is `9dc17d5ea64e0eb3f5c84eb1811d7612e2a578fa8e951d2d8074065d21953cdc`. Its recorded clean-extraction verification passed without retraining or rescoring the final holdout. This dated documentation overlay is separately zipped and is not an updated application release. If later application files change, the root release reviewer must deliver a newly verified source archive before publication; the old hash only identifies the old payload.

## Public GitHub repository

Use the actual human's GitHub account. Publish the reviewed application release as a public repository, preserving the fixed split, portable weights, training source/data, evaluation evidence, README, report, anatomy credits, licenses and AI disclosure. Installed dependencies, environments, secrets and scratch captures do not belong in the release.

Link the six-page PDF directly from the README and Devpost. The new Devpost wording may be included as a dated supporting document after human review; the existing frozen report/video need no narrative rewrite to support these claims.

From a signed-out browser, verify the repository opens, source files and report are readable, and the README's prerequisites/setup/run commands are complete. Use the root reviewer's verified clean-source result and record the final public commit and archive hash. If the actual published payload differs, verify that payload before treating the earlier record as its evidence.

## Optional interactive demo

The verified existing static build permits free hosting and needs no Python service or hosted prediction API. After the public repository exists, enable GitHub Pages with **GitHub Actions** as its source and run the included **Optional static judge demo** workflow for the reviewed source.

Check the actual returned public URL while signed out. Test meshes, the three evidence-loop controls, every profile route, one editable input, outcome reveal, original-value restore, unlabelled inputs and source/provenance links. Confirm relative assets work under the repository path. Entered values remain in browser memory; the public development examples and labels are delivered with the static bundle. Paste only the returned verified URL into Devpost. A hosted demo is useful but does not replace the required source and YouTube links.

## YouTube upload

Upload the exact verified `lumen-demo.mp4` to the actual submitter's channel as **public or unlisted**. Private visibility fails the supplied guideline. Verify that it plays while signed out, lasts 4:40.46 and has audible English narration.

Suggested title:

**Lumen — Coronary Evidence Explorer | Multimodal AI Hackathon 2026 Track A**

Suggested description:

> Lumen compares one public development record across five independently fitted input profiles, connects coronary predictions to source-identified BodyParts3D reference anatomy, verifies grouped linear SHAP explanations and exposes recorded errors. This video shows the actual running application and its validation/reproducibility evidence. Educational research only; not clinically validated or patient-specific lesion mapping. OpenAI Codex assisted with research, code, experiments and presentation. English narration was generated locally with Kokoro's af_heart synthetic voice. Source: [PUBLIC_GITHUB_URL]. Six-page report: [PUBLIC_REPORT_URL]. Optional interactive demo: [PUBLIC_DEMO_URL, only after verification].

The existing video chapter boundaries are approximately 00:00 inspectable estimates; 00:42 validation procedure; 01:30 anatomy and SHAP; 02:16 input profiles; 03:03 errors; 03:52 reproducibility and new inputs. The short live judge route in this kit leads with the same-case matrix; it is not a claim that the frozen video was rerecorded with that route.

## Devpost final form

Use actual real full names and Devpost accounts for every actual member, with 1–4 humans. Confirm eligibility, declarations and permitted team membership. AI tools are not humans. Select **Track A — Cardiovascular Risk Visualization & Prediction** for Lumen.

Paste the reviewed `devpost-ready.md` sections, enter the Built With tags in `built-with.json`, and provide the actual public source, report and YouTube links. Include OpenAI Codex and Kokoro. Add ChatGPT or other tools only if separately used. The README already identifies the AI-assisted parts; human review should confirm that it reflects the tools actually used.

Review all field values, link visibility, media playback, the four-target final table and LCX/RCA errors. Submit through the real human account, then save the actual project URL, confirmation and submission time. Until Devpost confirms receipt, keep `devpost_submitted` false. This handoff does not execute publication or entry submission.
