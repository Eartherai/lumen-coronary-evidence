# Five-profile agreement: fixed development-only probe

**Recommendation: preserve this as a research supplement; do not incorporate it as clinical confidence or a decision-withholding product feature in the submission.** The rule reduces coverage and retained-subset error, but agreement still retains many incorrect predictions, especially for LCX and RCA. All source/frozen final results, app, report and video are unchanged.

The protocol was saved before calculation. One rule was applied once to the existing 242 development out-of-fold rows: retain a target flag only when all five separately fitted cumulative input profiles agree, each at its own already selected training-fold threshold; otherwise withhold. No model fitting, probability aggregation, new threshold, rule search, external testing or heldout scoring was performed.

## Coverage and errors

| Target | Retained / 242 | Overall coverage | True-positive class coverage | True-negative class coverage | Withheld positive / negative | Stable wrong FP / FN |
|---|---:|---:|---:|---:|---:|---:|
| CAD | 182 | 75.21% | 86.71% | 46.38% | 23 / 37 | 10 / 2 |
| LAD | 161 | 66.53% | 76.60% | 52.48% | 33 / 48 | 32 / 1 |
| LCX | 172 | 71.07% | 75.00% | 68.67% | 23 / 47 | 51 / 9 |
| RCA | 164 | 67.77% | 67.42% | 67.97% | 29 / 49 | 56 / 2 |

These class-coverage denominators are all development rows of the relevant true class, not model-positive and model-negative counts. For CAD, the rule retains 86.71% of positive rows but only 46.38% of negative rows. For LAD the corresponding values are 76.60% and 52.48%. Coverage therefore changes the observed case mix.

## Retained flags and the original full-input baseline

| Target and cohort | N | TP | TN | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CAD: agreement retained | 182 | 148 | 22 | 10 | 2 | 0.9341 | 0.9367 | 0.9867 | 0.9610 |
| CAD: full original, same retained rows | 182 | 148 | 22 | 10 | 2 | 0.9341 | 0.9367 | 0.9867 | 0.9610 |
| CAD: full original, all development rows | 242 | 163 | 47 | 22 | 10 | 0.8678 | 0.8811 | 0.9422 | 0.9106 |
| LAD: agreement retained | 161 | 107 | 21 | 32 | 1 | 0.7950 | 0.7698 | 0.9907 | 0.8664 |
| LAD: full original, same retained rows | 161 | 107 | 21 | 32 | 1 | 0.7950 | 0.7698 | 0.9907 | 0.8664 |
| LAD: full original, all development rows | 242 | 125 | 52 | 49 | 16 | 0.7314 | 0.7184 | 0.8865 | 0.7937 |
| LCX: agreement retained | 172 | 60 | 52 | 51 | 9 | 0.6512 | 0.5405 | 0.8696 | 0.6667 |
| LCX: full original, same retained rows | 172 | 60 | 52 | 51 | 9 | 0.6512 | 0.5405 | 0.8696 | 0.6667 |
| LCX: full original, all development rows | 242 | 75 | 68 | 82 | 17 | 0.5909 | 0.4777 | 0.8152 | 0.6024 |
| RCA: agreement retained | 164 | 58 | 48 | 56 | 2 | 0.6463 | 0.5088 | 0.9667 | 0.6667 |
| RCA: full original, same retained rows | 164 | 58 | 48 | 56 | 2 | 0.6463 | 0.5088 | 0.9667 | 0.6667 |
| RCA: full original, all development rows | 242 | 72 | 76 | 77 | 17 | 0.6116 | 0.4832 | 0.8090 | 0.6050 |

The same-subset comparison is exactly equal because the full-input profile is one of the five profiles in the agreement rule. This rule does not improve any retained prediction. Its apparent conditional accuracy improvement against the all-row baseline comes from selecting a subset. The discarded cases still require a decision, and this experiment supplies no alternative decision for them.

Retained recall in the table is TP/(TP+FN) **among retained positive cases**. It excludes withheld positives and must not be presented as full-cohort sensitivity. Retained true-positive yield across all development positives is:
- CAD: 85.55% (148/173), compared with original all-row recall 94.22%.
- LAD: 75.89% (107/141), compared with original all-row recall 88.65%.
- LCX: 65.22% (60/92), compared with original all-row recall 81.52%.
- RCA: 65.17% (58/89), compared with original all-row recall 80.90%.

## Outer folds: descriptive only

| Target | Outer fold (zero-based) | N | Retained N | Coverage | Stable wrong N | Stable wrong FP / FN |
|---|---:|---:|---:|---:|---:|---:|
| CAD | 0 | 49 | 38 | 77.55% | 3 | 3 / 0 |
| CAD | 1 | 49 | 36 | 73.47% | 4 | 2 / 2 |
| CAD | 2 | 48 | 37 | 77.08% | 2 | 2 / 0 |
| CAD | 3 | 48 | 36 | 75.00% | 2 | 2 / 0 |
| CAD | 4 | 48 | 35 | 72.92% | 1 | 1 / 0 |
| LAD | 0 | 49 | 34 | 69.39% | 8 | 8 / 0 |
| LAD | 1 | 49 | 34 | 69.39% | 8 | 8 / 0 |
| LAD | 2 | 48 | 30 | 62.50% | 6 | 6 / 0 |
| LAD | 3 | 48 | 30 | 62.50% | 6 | 5 / 1 |
| LAD | 4 | 48 | 33 | 68.75% | 5 | 5 / 0 |
| LCX | 0 | 49 | 37 | 75.51% | 16 | 16 / 0 |
| LCX | 1 | 49 | 39 | 79.59% | 14 | 12 / 2 |
| LCX | 2 | 48 | 29 | 60.42% | 7 | 6 / 1 |
| LCX | 3 | 48 | 38 | 79.17% | 12 | 7 / 5 |
| LCX | 4 | 48 | 29 | 60.42% | 11 | 10 / 1 |
| RCA | 0 | 49 | 34 | 69.39% | 15 | 15 / 0 |
| RCA | 1 | 49 | 36 | 73.47% | 12 | 11 / 1 |
| RCA | 2 | 48 | 31 | 64.58% | 12 | 11 / 1 |
| RCA | 3 | 48 | 31 | 64.58% | 9 | 9 / 0 |
| RCA | 4 | 48 | 32 | 66.67% | 10 | 10 / 0 |

The folds share training data across iterations; target flags from the same person and profiles with overlapping features are dependent. No confidence intervals or independent-fold significance claims are made.

## Stable incorrect flags are preserved

All retained incorrect row indices are listed in `results.json`, and all 968 target-row decisions—including discarded rows—are in `row-decisions.csv`. Indices follow the original zero-based workbook indexing, excluding the header. These are public development records, not heldout records.
- CAD: 12 stable wrong flags (10 false positives and 2 false negatives).
- LAD: 33 stable wrong flags (32 false positives and 1 false negatives).
- LCX: 60 stable wrong flags (51 false positives and 9 false negatives).
- RCA: 58 stable wrong flags (56 false positives and 2 false negatives).

## Reproducibility and limits

The standard-library-only calculation took 0.0214 seconds. The process enforced a file-read allowlist and restricted writes to this new probe directory. Both OOF identity sets exactly equal the 242 split development IDs. Fold IDs and target labels align; all recorded decisions match finite probabilities at their frozen thresholds. Every one of the 100 profile/target/fold model specifications uses exactly the development IDs outside that entire outer fold, with the correct profile feature list and threshold. No heldout CSV was opened and no final evaluator was called.

The maximum full-profile/v2 selected-probability difference was 3.3306690738754696e-16; all corresponding flags and thresholds are equal. Source hashes were checked before and after the calculation. The existing verification files state that the availability experiment did not score the heldout rows.

The protocol is fixed for this single probe, but the project and its development results already existed. This is post-development exploratory analysis, not prospective preregistration or an independent validation cohort. Models/profile predictions are correlated. Agreement is not calibrated uncertainty, a probability confidence interval or evidence of clinical reliability. LCX and RCA still have 60/172 and 58/164 incorrect retained flags (34.88% and 35.37%). This does not repair the existing single-cohort or clinical-validation limitations.

The app's already documented LCX error demonstration, UCI411-288, is a concrete illustration: all five profile flags are negative even though the recorded label is positive. This existing demonstration was supplied by the parent review; no new case or heldout data were opened for that illustration.

The educational input-profile comparison already in Lumen can explain sensitivity to available inputs. This supplementary result is useful precisely because it shows why stable agreement must not be used to claim a trustworthy individual diagnosis. Adding such a claim would weaken the submission.

Artifacts:

- `protocol.json`: one fixed rule, source identities and reporting contract.
- `probe.py`: reproducible calculation and file-read/write guards; running against existing outputs deliberately refuses overwrite.
- `results.json`: complete target and fold results.
- `row-decisions.csv`: every target-row flag, retained status and stable error.
- `verification-receipt.json`: input/exclusion checks, runtime and calculation artifact hashes.
- `artifact-manifest.json`: hashes of the complete supplement excluding the manifest itself.
