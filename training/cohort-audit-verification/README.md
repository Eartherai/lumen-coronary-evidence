# Complete development cohort export and explanation verification

These new artifacts support Lumen's development audit laboratory. They do not retrain, recalibrate, select thresholds, evaluate another clinical cohort or rescore the 61-record final holdout. Existing eight-case artifacts and their original 160-explanation certificate are preserved unchanged.

## Reproduce

From the repository root:

```sh
python3 scripts/build_cohort_audit.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --python 3.12 --with-requirements training/requirements-explanation.txt python training/verify_cohort_audit.py
```

The exporter uses Python's standard library. The actual-SHAP verifier uses the pinned explanation dependencies, on CPU. `--offline` requires those dependencies and Python 3.12 to be cached locally; on a clean machine install the pinned requirements first. Each attempt writes a new timestamped receipt in this directory. A failed verification does not publish a new successful public certificate. Running the exporter again replaces the derived cohort JSON; running a successful verifier again replaces the compact public certificate while preserving old run receipts. Source/frozen scientific artifacts are not overwritten.

## Verified export

`artifacts/cohort-audit.json` contains all 242 original public development records, five input profiles and four targets. Each record has its original zero-based workbook `row_index`, zero-based outer `fold`, 55 allowed primitive-valued inputs, separately stored recorded outcomes, and compact probability/threshold/flag/model-ID summaries. No contribution arrays are stored for all records; the runtime computes them on demand from existing coefficients.

The exporter skips non-development worksheet rows and all outcome columns before decoding selected worksheet cell values. It joins the existing availability OOF CSV by original `row_index`. Every one of the 100 model training sets exactly equals the development set excluding the entire relevant outer validation fold and excludes the holdout. All 4,840 Python portable probabilities equal their existing OOF values exactly in this export run (maximum difference 0.0); all thresholds and flags match. The original eight examples match on inputs, identities, folds, recorded outcomes and saved probabilities/thresholds/flags/model IDs.

Successful run: `export-20261009T200523.016582Z.json`. Measured standard-library export runtime 0.179943 seconds. Export size **841,853 bytes**; SHA-256 `1f2f388bdb071523d79164962a1c562813810dd28768cd8de8062d7bd1155432`.

## Actual-SHAP verification

Successful complete receipt: `shap-20261009T200701.871364Z/verification.json`. Compact public summary: `public/assets/cohort-audit-verification.json`, which includes the full-receipt relative path and SHA-256.

All **4,840 explanations from 100 model specifications** were checked with actual SHAP 0.52.0 `LinearExplainer`, using `Independent` maskers containing every encoded row of each model's own training fold (`max_samples = len(training_rows)`). The identity link preserves the composed calibrated linear log-odds score. Encoded categorical indicator values are summed to the original raw feature. Both the explained record and its entire outer fold are excluded from the background. No holdout row inputs, labels or prediction CSV were consumed.

The check covered 269,312 encoded feature values and 3,049 sigmoid-calibrated explanations. At tolerance `1e-12`:

| Comparison | Maximum absolute difference |
|---|---:|
| Grouped actual SHAP versus Python portable contributions | 5.55e-17 |
| Actual SHAP baseline versus exported baseline | 4.44e-16 |
| Reconstructed log-odds versus Python portable score | 5.33e-15 |
| Sigmoid of reconstruction versus Python portable probability | 3.33e-16 |
| Complete training-background encoded means versus exported means | 0.0 |
| Python portable probability versus saved OOF probability | 0.0 |

Measured verifier runtime was 0.721435 CPU seconds after module imports. Python/uv process startup and import time are additional. Python 3.12.13, macOS arm64; complete environment/dependency versions and source hashes are in the receipt. Original final models, final evaluation, final protocol freeze, eight-case artifact and both old actual-SHAP certificate files retain their pre-run hashes.

This certificate verifies the Python decomposition against the stated SHAP convention. JavaScript runtime parity and the actual browser workflow require their separate checks. Independent masking breaks predictor dependencies; encoded masks need not preserve valid one-hot states. SHAP values are additive model associations in log-odds units, not causal effects or percentage-point probability changes. This verification does not measure clinical explanation utility or uncertainty.

## Interpretation

The audit uses recorded development outcomes to filter correct flags, false positives, false negatives and stable incorrect flags. Outcome-dependent filters are descriptive review, not blind prospective testing. Five agreeing profiles are correlated models with overlapping inputs; agreement is not confidence. The frozen profile-agreement supplement already shows 12 CAD, 33 LAD, 60 LCX and 58 RCA stable incorrect development flags at the research thresholds. Reduced-profile comparisons do not establish causal benefit of a test or a recommended order of care.

`UCI411-288` means original workbook data row index 288, excluding the Excel header; it is not a clinical subject identifier. Its documented LCX error is an existing development example, not a selected final-holdout result. Case/journey/predict responses should exclude recorded truth; the explicit label-reveal and outcome-aware audit routes have separate meanings. Edited inputs and unlabelled new inputs have no matching recorded outcome.
