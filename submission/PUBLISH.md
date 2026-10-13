# Publish the prepared submission

The local build is a reviewable Track A entry. Winning is determined by the judges. Do not submit invented results, human teammates, eligibility information or URLs.

## Files to review

- `README.md`: quickstart, final scores, limitations and AI disclosure.
- `output/pdf/lumen-report.pdf`: verified six-page report.
- `output/video/lumen-demo.mp4`: English narrated demonstration, 5 minutes 42.83 seconds.
- `submission/devpost-draft.md`: complete project copy with only human/account and publication fields unresolved.
- `submission/release-status.json`: exact completion state.
- `dist/lumen-submission-source.zip`: portable app, trained JSON weights, training sources/data, report and video.

## Public GitHub repository

Sign in to the actual human's GitHub account with `gh auth login`. Do not paste credentials or tokens into this chat. After authentication, create a public repository such as `lumen-coronary-evidence` from this folder and publish the reviewed source. Keep the model JSON files, fixed split, original workbook, source attribution, final evaluation and report in the repository. Installed dependencies, scratch captures, caches, credentials and Python environments are excluded.

The repository must open without authentication. Test the README commands from a fresh clone. Retain AI assistance in the README and Devpost Built With fields. The source release verifier already tests a clean extraction; its in-package record identifies the verified payload, and `dist/release-verification.json` identifies the exact tested ZIP.

## Free interactive demo

The optional static site is already verified locally. Its browser predictor matches the Python reference, accepts edited and unlabelled inputs, and requires no hosted model API. Public development examples and recorded labels are downloaded; entered form values remain in browser memory. No final holdout input rows are included.

After the repository exists, choose **Settings → Pages → Build and deployment → Source: GitHub Actions**. Run the included **Optional static judge demo** workflow or push the reviewed main branch. It installs the pinned renderer, runs the Python and browser parity checks, builds `dist/site`, and deploys that directory. Check the actual returned Pages URL while signed out: meshes, three entry points, profile cells, edits, outcome reveal and source/provenance links must work. Add only the confirmed URL to Devpost and `public_demo_url` in the release status. The generated site uses relative paths and was tested under a repository prefix.

## YouTube demonstration

Upload `output/video/lumen-demo.mp4` to the submitter's channel with public or unlisted visibility. Use this title:

**Lumen — Coronary Evidence Explorer | Multimodal AI Hackathon 2026 Track A**

Suggested description:

> Lumen connects clinical measurements to overall CAD and three vessel-label predictions, selectable BodyParts3D reference anatomy and verified grouped linear SHAP explanations. This demonstration shows the actual local application, validation procedure, independently fitted input profiles, observed mistakes and reproducibility. Educational research only; not clinically validated. OpenAI Codex assisted with research, code, experiments and documentation. Narration was generated locally with Kokoro. Source and six-page report: [insert actual public repository link].

Check that the uploaded video plays from a signed-out browser and contains English audio. Paste its actual watch URL into the submission draft.

## Devpost

Use the actual human submitter's full name and account. The AI assistant is not a human teammate. Add other people only if they actually participated. Confirm eligibility and membership in only this submitting team. Select Track A, Cardiovascular Risk Visualization & Prediction. Use the prepared project description, public repository link, report link and actual YouTube URL. Include OpenAI Codex and Kokoro in Built With, together with the actual software stack.

Review the final form before submitting. Any declarations and competition terms must reflect the human submitter's real status. After the site confirms receipt, save the actual project URL and confirmation, then mark `devpost_submitted` in the release status.

The official deadline recorded in the source guidelines is 15 October 2026 at 00:15 IST. Finish publication before 14 October evening and recheck the live event deadline at submission time.
