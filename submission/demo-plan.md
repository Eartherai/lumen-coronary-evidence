Complete-cohort opening: show all 242 records, filter LCX missed positives/all-five agreement, inspect uncurated UCI411-020 (22.2%, cutoff 33%, recorded positive), then open its exact artery/explanation. This is outcome-aware development review, not new validation. Actual SHAP covers 4,840 outputs/100 models. Original guided loop below remains illustrative.

# Lumen: six-minute English demonstration plan

The supplied guidelines require a three-to-ten-minute YouTube video showing the project running and explaining the approach. Use English audio or English subtitles. Public or unlisted is acceptable; private is not. This is a recording plan, not evidence that a video has been created or uploaded.

Target duration: about 6 minutes. Record the frozen final build with legible text and a real running backend. Use the verified final evidence below and keep model limitations visible. Human information and public publication URLs remain separate pending fields.

| Time | Screen action | Narration purpose |
|---|---|---|
| 0:00–0:35 | Show full running application and disclaimer | Explain the problem: a CAD number hides vessel differences and model reasoning. State educational scope and reference anatomy. |
| 0:35–1:20 | Choose a real unchanged development case; inspect inputs | Explain four targets and the exclusion of all angiography labels from predictors. State that this case was excluded from its displayed models' fitting. |
| 1:20–2:10 | Rotate/zoom the heart; select LAD, LCX and RCA | Demonstrate named, separately selectable meshes and synchronized vessel probability/explanation. Explain whole-vessel probability coloring without a lesion-location claim. |
| 2:10–2:55 | Expand score calculation; point to major contributions and measurements | Name grouped interventional linear SHAP in log-odds. Demonstrate its exact reconstruction; explain the Independent background, correlated inputs and noncausal interpretation. |
| 2:55–3:40 | Edit one supported measurement, run live prediction, then restore | Show backend recalculation, updated colors/measurements/explanation, and label-comparison disablement after edits. Explain that sensitivity exploration has no edited-patient outcome. |
| 3:40–4:20 | Load UCI411-288 or an equivalent predeclared failure case; reveal labels | Show all four recorded labels and a miss. Explain what a compelling visualization cannot guarantee. Do not hide errors or cherry-pick only correct cases. |
| 4:20–5:15 | Open Model evidence; show results and protocol | Report the once-scored 61-record final test, all four targets, fitted thresholds and false-positive cost. Show development comparisons separately. |
| 5:15–5:45 | Show repository architecture, clean setup and test evidence | Explain portable artifacts, CPU inference, anatomy provenance and reproducibility. Show real commands/output and final release commit. |
| 5:45–6:00 | Return to app; show public links and credits | State external validation and clinical review as future requirements. Credit data/anatomy and AI assistance. |

## Suggested opening

“Lumen connects a coronary prediction to the artery it describes and the measurements behind it. We built an educational explorer for overall CAD and three vessel targets. You can select the anatomy, inspect the model's reasoning, and reveal a recorded outcome—including cases where the model fails.”

## Recording checks

- Open the app through its HTTP URL, not `public/index.html` as a file.
- Verify the backend, meshes and final artifact version before recording.
- Show real mouse interactions, feature input and live inference; a slide-only or mockup-only video does not demonstrate the running system.
- Avoid stating that model probability is percentage narrowing or that colors identify plaque coordinates.
- Use the actual final explanation scale; a calibration change may alter the equation narrated.
- Show per-target weaknesses, data limits and the clear imaging disclaimer.
- Verify length, English audio/subtitles, readable text, working YouTube visibility and final link after upload.
- Match the video, report, repository commit and Devpost metrics; disclose Codex/ChatGPT use in the required submission fields.


## Verified results for narration

“The full-input model procedure was frozen before scoring a 61-record final holdout once. CAD and LAD AUC are 0.908 and 0.893. LCX and RCA AUC are 0.748 and 0.724. LCX recall is 0.852 with precision 0.535; RCA recall is 0.760 with precision 0.500. LCX has 20 false positives and four false negatives, while RCA has 19 false positives and six false negatives. This remains a small same-source evaluation, without external or prospective validation.”

“For explanation fidelity, actual SHAP LinearExplainer verification passed 160 case/profile/target outputs. The interface uses grouped interventional linear SHAP on the model log-odds. These contributions are model associations, not treatment effects or probability-point changes.”

Show profile switching on a development case, and distinguish that excluding-fold model from the full-input frozen model used for new entries. Do not present the five development profile comparisons as five final holdout tests. After scoring, no threshold or model is retuned using test outcomes.
