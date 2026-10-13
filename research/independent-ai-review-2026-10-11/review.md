# Independent AI review of Lumen — 11 October 2026

This is an executed AI review, not a human usability session, clinical review, or clinical validation. Human usability and signoff remain unmeasured/pending. No human completion times, comprehension scores, or competition win probability are inferred.

The first file read was the public participant task sheet. T1–T6 were tried against the actual UI before the moderator guide, answer key, rubric, implementation, or previous review material was inspected. A dedicated, hidden Codex in-app browser tab opened `http://127.0.0.1:8770/`; it was closed after the task run. The default screenshot viewport was 1280 × 720. Browser version, device model, graphics renderer, frame rate, and human task timing were not measured. The participant sheet was available in full, and the agent read the six prompts together. No neutral human moderator participated.

Root subsequently identified the served app as the unchanged Oct 10 static baseline at `coronary-evidence/dist/current-review-browser-2026-10-10/lumen-browser`. This build binding is retrospective: the starting build hash and precise task start UTC were not captured before interaction. All 23 files listed by its static manifest now match their recorded hashes. The manifest SHA-256 is `85473965f569433aec400fc4db876528ada061c55bc8963ca20c7ba4b0b74463`. The protocol SHA-256 is `8ba0a8b84661e5a2a43157fff47272a227a2cd7c2329eba372597693e5fa1d39`. Root's later edits to current source were not served during this task run. Findings below concern the baseline before those fixes.

## Findings

### [P2] A prior audit notice describes the wrong selected case

**Evidence:** browser observed and source verified. In T3, open audit UCI411-057 in the explorer. Then choose UCI411-128 from Development case. The selected case and explanation correctly become UCI411-128, but the hero notice still says: “UCI411-057 was chosen using recorded development outcomes. Its fold-excluded predictions and actual labels are shown together.” This survives later ordinary case switches. The screenshot shows UCI411-128 selected beside the previous case's notice.

**Consequence:** the interface gives conflicting record identity and selection provenance. A reviewer can misattribute the visible score and recorded-label state to the previous record. The model calculation itself follows the newly selected record; this is a presentation/state defect, not observed inference leakage.

**Expected behavior and bounded fix:** clear or recompute the contextual notice when a new case/profile load commits. Show a notice only for its actual current case and state; preserve appropriate outcome-aware disclosure when an audit case is current. Inspect the served baseline `app.js:99` (`loadCase`), `app.js:218` (case selector), and `app.js:241` (`openAuditCase` sets `tour-note`). Retest audit → curated case, audit → unlabelled form, ordinary profile changes, and tours.

Evidence: [stale-audit-provenance.jpg](/Users/earther/Desktop/IIT mandi/coronary-evidence/research/independent-ai-review-2026-10-11/stale-audit-provenance.jpg).

### [P2] False alarms are labelled “prediction missed” in the outcome comparison

**Evidence:** browser observed and source verified. Choose UCI411-128, full inputs, training-selected rule, then reveal recorded labels. LCX has a 42.2% probability and a positive flag at a 35.0% cutoff, against a negative recorded label. The outcome row reads “Negative label · prediction missed.” The same wording was visible again after restoring T5's edited record. The baseline `app.js:150` assigns the same string to every mismatching flag, regardless of the recorded label.

**Consequence:** the explorer collapses false alarms and missed positives into wording that suggests a missed positive. This is inconsistent with the audit, which distinguishes the two, and can confuse the intended threshold tradeoff explanation.

**Expected behavior and bounded fix:** derive the displayed outcome from flag and truth. Use “false alarm” for a positive flag against a negative label, and “missed positive” for a negative flag against a positive label; retain “agrees” for matching flags. Exercise both disagreement directions under both decision rules and after restore/reveal.

Evidence: [negative-label-mismatch.jpg](/Users/earther/Desktop/IIT mandi/coronary-evidence/research/independent-ai-review-2026-10-11/negative-label-mismatch.jpg), [visible outcome text](/Users/earther/Desktop/IIT mandi/coronary-evidence/research/independent-ai-review-2026-10-11/negative-label-mismatch-visible.md).

No P1 defect was established in the inspected scope. Root is implementing the two fixes separately; this review does not claim their post-fix browser verification.

## Actual task results

| Task | Observed result | Scope/status |
|---|---|---|
| T1 | Used Browse every record, selected LAD, searched UCI411-276, then opened it in the explorer. Full probability 22.5%; cutoff 39.0%; negative recorded label; negative flag agrees. Searched all 242 development records, excluding the 61 final-test records. | Completed in the actual UI. |
| T2 | Used the app's shared-LCX-miss challenge. Nine records matched. Selected/default inspector UCI411-020: positive recorded LCX label and five negative flags. The cohort summary was 60 errors among 172 records with five agreeing flags, not nine errors total. Agreement does not establish confidence or correctness; separately fitted profiles can share an error. | Completed in the actual UI. T2 retained prior task state, rather than a fresh-page reset; the challenge reset its filters. |
| T3 | Self-prepared UCI411-057 from the audit, full LCX. Training-selected: 43.9%, cutoff 31.0%, positive. Fixed rule: 43.9%, cutoff 50.0%, negative. Whole-cohort LCX counts changed from 17 missed positives/82 false alarms to 63/18. | Completed in the actual UI. Only the decision rule and derived flags/counts change; the probability is unchanged. Source additionally confirms unchanged weights, contributions and probability-based colors. This is no medical operating-point validation or improved probability ranking. |
| T4 | UCI411-128 LAD profile flags, in 17/31/38/52/55-input order: positive, below, below, below, positive. History + examination cell: 36.1%, 50.0% cutoff. Full cell: 44.4%, 34.0% cutoff. Explorer input count, LAD selection, probability and explanation followed both cells. | Completed in the actual UI. These are separately fitted models and preprocessing/calibration choices; differences do not identify causal test benefit, a confidence interval or recommended acquisition order. |
| T5 | Changed only Age 62 → 63 and recalculated. LAD moved 44.4% → 45.4% at the same 34.0% cutoff. UI showed one edited input, hid original truth, disabled reveal (“Restore inputs to compare labels”), and paused original-record five-profile comparison. Restore returned Age 62, probability 44.4%, profile comparison and label reveal; reveal was used again. | Completed in the actual UI. This is model sensitivity. No observed outcome exists for the hypothetical edited measurements and no treatment effect is established. |
| T6 | Self-prepared UCI411-171 with CAD selected, then selected LAD using its anatomy label. Drag and wheel produced a visibly rotated, enlarged reference heart. Focus and isolate controls were invoked, then Overview restored the overview/status. Complete score: baseline 0.569 + all 55 contribution sum 2.248 = final log-odds 2.817, logistic probability 94.4%. | Core task completed with evidence limits. Label selection, rotation/zoom, overview status and score were observed. Focus/isolate commands completed before a later score-selector error discarded that call's screenshot output; the isolated rendering was not independently retained/visually judged. Its hide/show and bounds logic were source verified. Mesh ray picking was not tested. |

For T6, LDL 213 contributes +0.676 log-odds relative to the model's training reference; this is a model association, not a causal effect or a percentage-point increase. The probability estimates the source target label. Vessel color encodes probability on the whole generic named vessel. Neither is the percent narrowing, patient-specific anatomy, plaque location, or a lesion map. The source code maps LAD/LCX/RCA geometry and anatomy-label buttons to the corresponding target keys.

The agent encountered automation locator recoveries: native accessibility text represented pressed prediction buttons as checkboxes, while the DOM snapshot correctly represented buttons; a label locator for an audit filter needed a combobox-role locator; the score disclosure needed its visible text locator. These were tool-path issues and are not counted as human obstacles, task failures, or elapsed usability time. T4's participant wording “All measurements” differs from the exact full-profile UI label “All recorded inputs (+ echo)”; the full 55-input option was identifiable, but future protocols should use the displayed name.

## Source and evidence checks after tasks

Read-only serialized model/schema/hash inspection found all 100 outer models exclude the complete corresponding validation fold and all final holdout records. Their numeric/categorical fields match their declared availability profile. All five profile feature sets exclude CAD/Cath/LAD/LCX/RCA target fields. Four final models use exactly the 242 development training identities and 55 predictors. The audit contains exactly those 242 development identities and no holdout identity. All protocol-bound artifact hashes match. The served static bundle's cohort, availability models, full final models and profile feature orders match those source artifacts.

The baseline static inference rejects target/extra/missing input keys and nonfinite numeric values. It reports null imputation and unknown categorical encoder behavior. Label reveal is separate from inference, and edited-record comparison is guarded in both the frontend and profile display. Request/version checks protect case/reveal/recalculation from late responses. These are source-verified protections; malformed-input and race scenarios were not exercised through the browser.

The saved actual-SHAP certificate binds the same model/cohort/profile artifacts and reports 4,840 explanations across 100 models, with grouped error below its 1e-12 tolerance. The UI's exact score reconstruction and source formula agree with the displayed additive log-odds convention. The certificate was inspected, not rerun. Independent masking, correlated predictors, one-hot aggregation and noncausal interpretation are disclosed. No fitting, threshold search, dataset download, final-test metric rescore or outcome-evaluation script was executed for this review; the holdout prediction CSV was not opened.

The frozen primary scope remains four full 55-input models evaluated on 61 final held-out records. The browser's outcome-aware development audit and reduced profiles are exploratory development views; they do not add a second final evaluation or establish external validity. The retained held-out LCX/RCA precision (0.535/0.500 at their frozen research thresholds) and small sample remain material predictive limitations despite an effective visual interface.

## Official Track A fit

The official supplied Track A extract requires overall CAD plus LAD/LCX/RCA predictions, exclusion of the four source target columns, classification metrics, probability-based vessel coloring, rotate/zoom/select interaction, physiological attribution, a visible educational/imaging disclaimer, and reproducible model/dashboard integration. Its weights are predictive performance 30%, 3D visualization 25%, interpretability 20%, integration 15%, and technical implementation 10%.

The reviewed core workflow supplies these software behaviors in the observed/source-verified scope. Vessel selection synchronizes the explanation; threshold and profile changes update the related evidence; actual grouped log-odds attribution has a bound verification receipt. The two P2 findings weaken provenance clarity and error interpretation within the interpretability/integration criteria. Generic whole-vessel coloring is appropriately disclosed; the rubric's spatial visualization language does not turn the source clinical features into patient lesion coordinates. No official score, competitive ranking, or win probability follows from this AI review. Document/video length, public deployment, submission acceptance and dedicated-GPU-free responsive rendering were not verified here.

The task observations support technical/UI behavior review and the two bounded fixes. A new release needs its own build binding and post-fix checks. Human review and human signoff remain pending.
