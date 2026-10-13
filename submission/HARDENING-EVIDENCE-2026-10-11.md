# Lumen UI hardening evidence - 11 October 2026

The follow-up hardens case/profile transitions and keyboard selection. It does not change the clinical models, selected thresholds, explanations, data partition or frozen scientific results. No new training or final-holdout score was performed.

## Actual failure recovery and keyboard checks

An AI operator used the actual local Python API application through CUA. Temporary blocking of exact case/profile endpoints exercised failure behavior; all blocking was cleared after the checks. The receipt binds the tested source hashes after the browser actions and retains the limited scope of those observations.

| Check | Observed result |
|---|---|
| History profile request failed | Prior UCI411-171 full profile restored with all 55 visible inputs and a visible fetch error |
| UCI411-128 case request failed | Prior UCI411-171 full case restored, including LAD 94.4%; healthy retry loaded UCI411-128 |
| Enter on LAD prediction button | Matching target remained selected, `aria-pressed=true`, and button focus retained |
| Enter on LAD/history-plus-examination matrix cell | Matching profile/target selected, 31-input profile and LAD 36.1% observed; button focus retained |
| Second case failure and retry | UCI411-050 failure restored UCI411-128; healthy retry loaded UCI411-050 and cleared the displayed error |

The [source-bound browser verification](../research/runtime-hardening-2026-10-11/browser-verification.json) records these five checks. Its [saved failure-state screenshot](../research/runtime-hardening-2026-10-11/failed-load-restored-case.png) documents the restored loaded state. Thirteen focused asynchronous regression tests additionally cover delayed/stale transition cases with synthetic promises; these tests do not measure human timing or clinical behavior.

This follows the separate fresh-agent review that found stale prior-case context and false alarms described as misses. Those two defects were corrected and browser-checked before this follow-up. [Earlier review and corrections](../docs/review-hardening-2026-10-11.md) retain the fresh-review task outcomes and distinguish AI observations from human evidence.

## Frozen evidence preserved

The primary full-input procedure remains the one frozen before the 61-record final holdout was evaluated once on 5 October. No holdout fitting, calibration, threshold selection, profile selection or rescoring follows from the UI update. Final ROC-AUC remains CAD 0.908, LAD 0.893, LCX 0.748 and RCA 0.724. The existing false-positive costs and conditional-interval limitations remain unchanged.

The complete 242-record development audit still uses excluding-fold models, recorded outcomes are separate from inference, and edited inputs have no matching observed edited outcome. The 4,840 probability/actual-SHAP verification remains engineering evidence for the specified export and attribution convention, not clinical utility or external validation.

The new [six-page hardening report](../output/pdf/lumen-report-hardening-2026-10-11.pdf) incorporates the actual failed-load and keyboard checks. Its adjacent provenance records exact source bindings and unchanged frozen evaluation/model/protocol artifacts during authoring. Its QA receipt records individual visual inspection of all six rendered pages. The earlier report editions and review packages remain preserved.

## Remaining limits and delivery gaps

These were AI-operated checks on one physical Mac. Human usability, comprehension, accessibility evaluation and final human signoff remain unmeasured. The earlier Chromium runtime samples retain their original pre-watchdog software-timing scope; they do not measure GPU completion, physical display latency, hosted performance or a second device. Safari rendering remains unpassed. This note claims no new video validation.

No full-55-input, four-target external cohort was admitted by the bounded compatibility search. The independent AngioCAD source lacks the examination and ECG groups and has unresolved mappings; it was not scored as validation of the existing model. Lumen remains a small, single-source educational prototype. Generic anatomy cannot locate patient-specific plaque, and model associations do not establish causal treatment effects.

Public GitHub/YouTube links, real human account/eligibility information, human release signoff and final Devpost submission remain outstanding. AI assistance must remain disclosed, and the human submitter must understand and explain the implementation and evidence. Neither UI hardening nor a verified artifact guarantees a prize. The current one-track rule limits this person/team to one of the local alternatives.

## Final independent review and stale prediction repair

The subsequent read-only agent review reproduced a stale prediction rejection showing an error after a newer case loaded. The repaired recalculation and its click handler now apply results, errors and control changes only to the owning case version. Four additional meaningful regression checks bring transition tests to 17; the complete Node suite has 52 tests, and the 64 original journey paths also pass. This leaves scientific results unchanged.

Two actual browser checks used a separate test-only HTTP harness to hold requests, return synthetic delayed errors and control a later case load. An old failed prediction left the newer loaded case untouched; an old failure during a pending newer load did not enable the prediction button or clear its loading notice. The later case then loaded successfully. The harness was stopped, and the ordinary application server was unchanged. [Current source-bound browser receipt](../research/runtime-hardening-r2-2026-10-11/browser-verification.json) and [independent repair verification](../research/runtime-hardening-r2-2026-10-11/fix-verification.json). The five earlier case/profile/keyboard checks above retain their historical pre-R2 source hashes rather than being relabelled as this new check. These remain AI software observations on one Mac, not a human usability study.
