# Complete development audit

Open the **Cohort audit** tab. It contains every one of the 242 locked development records, spanning all five outer folds. The eight original introductory examples remain available. The 61 final-test records are not included in the audit.

The audit deliberately uses recorded outcomes to find errors. It is descriptive development review, not a blinded, external or prospective evaluation. Each prediction uses the existing model that excluded the entire record's outer fold from preprocessing, fitting, calibration and threshold selection.

Choose a target, full-input outcome, agreement behavior and outer fold. The audit and case explorer share one decision rule: either each model's already fitted research threshold or fixed 50%. Changing it recomputes filters, flags and counts together. The counts always summarize all 242 records for that target; the matching roster reflects the selected filters. Search matches case IDs. `row_index` is the zero-based workbook data row; Excel row is `row_index + 2`.

Select a record to compare its recorded outcome, full-input flag and all five profile probabilities/cutoffs together. **Inspect** opens the same record in the 3D anatomy, exact score and profile matrix. Labels are revealed explicitly because the audit selection already used them. Editing inputs removes the recorded-outcome comparison: no edited-patient outcome was observed. Profile differences include separately fitted models and calibration; they are not causal test effects. Agreement is not confidence.

The LCX learned-threshold challenge finds nine recorded positives missed by all five profiles. Across the entire LCX development cohort, 172 records have agreeing flags and 60 of those flags are wrong. This is a failure of the confidence interpretation, not an improvement in accuracy obtained by filtering.

**Export this selection** saves exact filters/rule, selected record IDs, recorded labels, model IDs, probabilities, thresholds, flags and source hashes. This export contains public recorded development outcomes. Comparison exports from the case explorer retain their original outcome-free contract.

## Verification and reproduction

The compact [artifact](../artifacts/cohort-audit.json) is 841,853 bytes. Its 4,840 probabilities exactly match the saved development OOF predictions in Python. Full contributions are calculated lazily from existing portable model coefficients; no model is trained by an audit request.

The [actual-SHAP certificate](../public/assets/cohort-audit-verification.json) verifies all 4,840 outputs against `shap.LinearExplainer`, using complete excluding-fold `Independent` backgrounds and identity/log-odds links. All 100 models pass at tolerance 1e-12; maximum grouped-term error is 5.55e-17. [Complete receipt and commands](../training/cohort-audit-verification/README.md). The original 160-output certificate remains scoped to the eight-case roster. Independent masking breaks predictor correlations and does not establish causal or clinical explanation utility.

Run from the project root:

```sh
python3 -B scripts/build_cohort_audit.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_cohort_filters.mjs tests/test_cohort_static.mjs
npm ci
python3 -B scripts/build_static_demo.py
node --test tests/test_static_client.mjs
```

The Node cohort checks compare all 4,840 browser probabilities, scores, baselines and grouped terms with Python, check all 100 entire-fold/holdout exclusions and verify cached inference sends no network POST. Filter checks independently recompute every outcome/agreement/fold combination under both rules. The ordinary Python and browser runtime need no training libraries or cloud API. The actual SHAP verifier needs the separately pinned explanation environment documented in its guide.

Live-browser review also opened an uncurated record, changed profile, edited/restored inputs, filtered a new fold, synchronized fixed/learned rules and ran inference with subsequent network requests blocked. This is software verification, not a new clinical score. Saved images/receipt are under `output/cohort-browser-review/`.
