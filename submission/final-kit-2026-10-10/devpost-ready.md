# Lumen — Coronary Evidence Explorer

Copy below is prepared for Track A: Cardiovascular Risk Visualization & Prediction. Replace the link and human fields in `handoff-fields.json` before final submission.

## Tagline

One record. Five input profiles. Trace coronary predictions through reference anatomy, verified explanations and visible errors.

## Inspiration

An overall coronary score can hide three different vessel estimates, the measurements behind them and the cases a model gets wrong. Lumen turns those pieces into one inspectable loop. A user can compare the same recorded inputs across fitted models, select the artery behind an estimate, follow the score calculation and check it against a recorded outcome.

## What it does

Lumen predicts overall coronary artery disease (CAD) and separate LAD, LCX and RCA stenosis labels from public clinical measurements. Source-identified BodyParts3D reference meshes make each coronary artery selectable. Its probability, measurements and explanation stay connected to the selected vessel.

The central comparison shows one development record across five cumulative input profiles: history (17 inputs), plus examination (31), ECG (38), laboratory (52) and echocardiography (55). Each reduced profile was fitted separately inside the same development folds; the full profile reuses the original V2 artifacts. All 20 probabilities and each model's actual research threshold appear together. Select a cell to synchronize the anatomy, required inputs and exact explanation. A downloadable comparison records the inputs, model identities and contributions; it excludes recorded outcomes.

Rotate, zoom, focus or isolate a vessel, then open the complete baseline-to-score waterfall. Change a measurement and recalculate. Recorded labels can be revealed for unchanged development cases, including mistakes. Editing a case pauses its original-record comparison and disables outcome reveal because no outcome was observed for the edited inputs. A separate unlabelled form uses the four frozen full-input models fitted on all 242 development records.

Five-profile differences include refitting and calibration. Their range is not an uncertainty interval, the benefit of ordering a test or a recommended clinical sequence. The geometry is generic reference anatomy. Vessel colors neither locate plaque nor represent patient-specific imaging, and model probability is not percentage arterial narrowing. The visible UI states that this is educational decision support and does not replace formal diagnostic imaging.

## How it was built

The UCI extension of Z-Alizadeh Sani contains 303 records. Cath, LAD, LCX and RCA are excluded from every predictor set, leaving 55 inputs for the primary profile. A fixed split reserves 61 records for final evaluation and uses 242 for development.

Five outer development folds evaluate a regularized logistic procedure. Three inner folds select regularization, weighting and optional cross-fitted sigmoid calibration by out-of-fold log loss; inner predictions also select an F1 threshold. Fitting, preprocessing, calibration and threshold selection exclude the displayed case. The full-input V2 procedure was frozen before the final holdout was scored once. Reduced profiles and tree probes remain development comparisons.

Preprocessing, coefficients and thresholds are exported to JSON. Python's standard library performs reference inference; Three.js renders the anatomy in the browser. An optional static build computes the same portable models in browser memory without a hosted prediction service. It includes eight public development examples and their labels; typed values are not transmitted by the prediction client. The hosted URL is pending publication.

The displayed explanation is grouped interventional linear SHAP in log-odds. Actual `shap.LinearExplainer` with an `Independent` masker verified all 160 displayed case/profile/target outputs against the portable formula. Maximum grouped-term error was 6.94e-18 at tolerance 1e-12. The background uses all encoded training-fold rows; categorical one-hot terms are summed into their original feature. Baseline plus every contribution reconstructs log-odds, and sigmoid reconstructs the probability. Independent masking breaks dependencies, so these are model associations rather than treatment effects.

BodyParts3D FMA memberships identify the heart, LAD, LCX and RCA. The source package records part memberships, mesh modifications, attribution and hashes. HyperFrames and GSAP build the 4-minute-40-second demonstration from actual application captures; Kokoro supplies locally generated English narration.

## Results

The frozen full-input final evaluation used 61 held-out records and was opened once after protocol freeze. Classification metrics use development-selected research thresholds.

| Target | ROC-AUC (conditional 95% interval) | Accuracy | Precision | Recall | F1 | Brier | Threshold |
|---|---|---:|---:|---:|---:|---:|---:|
| CAD | 0.908 (0.815–0.972) | 0.836 | 0.851 | 0.930 | 0.889 | 0.110 | 0.21 |
| LAD | 0.893 (0.804–0.966) | 0.852 | 0.814 | 0.972 | 0.886 | 0.126 | 0.36 |
| LCX | 0.748 (0.621–0.859) | 0.607 | 0.535 | 0.852 | 0.657 | 0.216 | 0.30 |
| RCA | 0.724 (0.579–0.844) | 0.590 | 0.500 | 0.760 | 0.603 | 0.209 | 0.25 |

LCX produced 20 false positives and 4 false negatives; RCA produced 19 false positives and 6 false negatives. Higher vessel recall carries a substantial false-positive cost. The 1,000-resample patient-bootstrap intervals condition on fixed fitted models and omit retraining and protocol-selection uncertainty. This small, single-dataset test does not establish external or prospective clinical validation.

The five-profile development comparison also exposes nonuniform behavior. CAD AUC is 0.828 with history, 0.921 with examination, 0.937 with ECG, 0.922 with laboratory and 0.926 with all inputs. More recorded inputs did not improve every target. These exploratory results did not replace the frozen primary profile.

## Challenges

Vessel predictions are weaker than overall CAD prediction. Correlated measurements complicate attribution, and a compelling 3D scene can make a fallible score look more certain than it is. Lumen keeps thresholds, per-target metrics, source identities and real failures visible. The four models are independent estimators and do not impose a coherent joint CAD/vessel distribution. Several source measurement units remain unverified and are not invented.

## Accomplishments

The complete working loop connects the same public development case to an excluding-fold model, source-identified anatomy, an exact explanation and a separate outcome reveal. Its five input profiles are real fitted procedures rather than missing-group defaults. The released software includes portable weights, training sources, the fixed split, anatomical provenance, a six-page technical report and a verified narrated demonstration.

Recorded clean-extraction checks cover model routing, label separation, portable predictions, static/Python parity and actual SHAP agreement. These establish software consistency; they add no patients or new clinical evaluation. One visible example, UCI411-288, misses positive CAD, LCX and RCA labels and remains in the demonstration.

## Next steps

External-cohort and prospective evaluation, clinical review and evidence for an intended medical use would be needed before medical deployment. The present project remains an educational research prototype.

## AI assistance disclosure

OpenAI Codex assisted with research, implementation, experiments, verification, documentation, report and video preparation. Kokoro generated the English narration locally with the `af_heart` synthetic voice; it is not a recording of the human submitter. Human review and responsibility are required. AI tools are not human teammates. OpenAI Codex and Kokoro are included in Built With; add other AI tools only if actually used.

## Credits

Data: Alizadehsani, R., Roshanzamir, M. and Sani, Z., *extention of Z-Alizadeh sani dataset*, UCI Machine Learning Repository, [DOI 10.24432/C5461K](https://doi.org/10.24432/C5461K), CC BY 4.0.

Anatomy: BodyParts3D, © The Database Center for Life Science, licensed under CC Attribution 4.0 International. [Official license](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html). Code is MIT; source data, meshes and third-party tools retain their own terms.

## Link fields to complete

- Public GitHub repository: [PUBLIC_GITHUB_URL]
- Six-page report in that repository: [PUBLIC_REPORT_URL]
- YouTube demo, public or unlisted: [YOUTUBE_WATCH_URL]
- Optional interactive demo, after deployment and verification: [PUBLIC_DEMO_URL]
- Actual human full names and Devpost accounts: [REAL_TEAM_MEMBERS]
- Actual eligibility and permitted team/track: [CONFIRMED_ELIGIBILITY_AND_TRACK]
