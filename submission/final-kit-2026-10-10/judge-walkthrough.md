# Lumen judge walkthrough

Use this short live route alongside the existing 4:40.46 English video. Rehearse it with the final delivered build. The root release reviewer is separately verifying browser behavior and performance; this document records intended actions and saved example values rather than claiming a fresh UI run.

## Opening, 20 seconds

“Lumen lets you trace and challenge a coronary prediction. The same recorded case can produce different estimates when different input groups are available. Each estimate stays connected to a named reference artery, its exact model calculation and a recorded outcome.”

Point to the visible educational disclaimer. State that the mesh is generic BodyParts3D anatomy and a probability colors the whole corresponding vessel, without locating a lesion.

## One record across five profiles, 55 seconds

Click **Compare available inputs** in the three-button evidence loop. It loads `UCI411-128`, history profile, LAD, with the training-selected decision rule. Open **Compare inputs** if needed.

Read the LAD row without changing the case. Every cell uses a separately fitted applicable profile model that excluded this record. The full profile reuses V2. Show 17, 31, 38, 52 and 55 inputs and each cell's own cutoff. Select the history and full-input LAD cells to demonstrate that inputs, anatomy and explanation update together.

| Profile | Saved LAD probability | Its fitted threshold | Research flag |
|---|---:|---:|---|
| History | 63.4% | 36.0% | Positive |
| + examination | 36.1% | 50.0% | Below |
| + ECG | 22.4% | 37.0% | Below |
| + laboratory | 20.9% | 35.0% | Below |
| + echo/full | 44.4% | 34.0% | Positive |

“This is a comparison of fitted models. The changes include refitting and calibration; they are not the effect of ordering a test or a confidence interval.”

Open **View exact comparison JSON** or use **Download comparison**. Point to case identity, model IDs, inputs and contributions. The exported comparison excludes recorded outcomes; recorded labels remain downloadable as part of the public development bundle and are hidden only by the application's reveal flow.

## Geometry to complete score, 45 seconds

Click **Trace a vessel** to load `UCI411-171`, full profile, LAD. Rotate/zoom, select a coronary artery on the mesh, then use the focus/isolation controls. Show the matching LAD/LCX/RCA key in the evidence panel and **Anatomy provenance**.

Open **Check the complete score**. Explain that baseline, six largest grouped terms and all remaining terms sum in log-odds; sigmoid is applied at the endpoint. Call the method “grouped interventional linear SHAP in log-odds.” Actual SHAP checked 160 displayed outputs at tolerance 1e-12. It is an association within a fitted model; independent masking does not preserve correlations.

## A real miss and the final tradeoff, 40 seconds

Click **Inspect a missed positive**. It loads `UCI411-288`, full profile, LCX and reveals recorded labels. The saved LCX probability is 25.3%, below that case model's 31.0% cutoff, while its recorded LCX label is positive. CAD and RCA are also missed at their own fitted thresholds. This is a development example, not a final-holdout row.

Open **Model evidence** and the distinct **Held-out evaluation**. State the final sample size, once-only evaluation after freeze and all four AUC values: CAD 0.908, LAD 0.893, LCX 0.748 and RCA 0.724. Include the false-positive tradeoff: final LCX 20 FP/4 FN; RCA 19 FP/6 FN. Do not substitute these final thresholds for the displayed case's fold-specific thresholds.

## Editing and release evidence, 20 seconds

Change one visible measurement and recalculate. Show that the original-record comparison pauses and **Reveal recorded labels** becomes unavailable. Restore values. Choose **Unlabelled input form** and state that defaults are illustrative, with no recorded outcome.

Close by showing the README, six-page report and source package. “Training uses CPU; inference uses portable JSON weights. The release records retain the source hashes, exact models and errors.” Add measured latency only after the root reviewer records an actual named-device/browser result.

## Four questions to prepare for

- **Why five profiles?** To inspect model behavior under defined input availability. Each reduced model was refitted; missing values within a profile still use its fitted imputer. Only the full profile has the frozen final evaluation.
- **Why logistic models?** The dataset is small, the runtime stays portable and the score has an exact additive decomposition. No claim of algorithmic novelty is needed.
- **Is a higher score a stenosis percentage?** It estimates a recorded binary label. It is not percentage narrowing, plaque location or a treatment effect.
- **Is it clinically validated?** The evidence is a small same-source holdout and development comparisons. No external or prospective clinical validation is claimed.
