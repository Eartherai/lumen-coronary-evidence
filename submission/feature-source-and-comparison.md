# Feature semantics and availability comparison

Research and experiment update: 6 October 2026. The source-backed operational grouping informed an executed five-profile development comparison. It was defined without final holdout access; reduced profiles remain development evidence and do not replace the frozen full-input final procedure.

## Primary source evidence

- [UCI dataset 411](https://archive.ics.uci.edu/dataset/411/extention+of+z+alizadeh+sani+dataset) identifies demographic, symptom/examination, ECG, and laboratory/echo groups. Its current variable table has empty descriptions and units, so it cannot verify every unit label.
- Alizadehsani et al., *Diagnosing Coronary Artery Disease via Data Mining Algorithms by Considering Laboratory and Echocardiography Features*, 2013, [doi:10.5812/cardiovascmed.10888](https://doi.org/10.5812/cardiovascmed.10888), [primary article PMC4253773](https://pmc.ncbi.nlm.nih.gov/articles/PMC4253773/). Tables 1 and 2 explicitly show age in years, weight in kg, BMI in kg/m² and EF in %. Table footnotes expand demographic and lab/echo abbreviations. The full article was inspected through its [Europe PMC full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4253773/fullTextXML), a repository copy of the primary paper.
- Alizadehsani et al., *Diagnosis of Coronary Arteries Stenosis Using Data Mining*, 2012, [primary article PMC3660711](https://pmc.ncbi.nlm.nih.gov/articles/PMC3660711/). Tables 1–3 identify demographic, symptom/examination and ECG categories. Its accessible full-text XML stores those tables as images, rather than transcribed unit data. It corroborates the overall grouping, but an unseen table image should not be cited as verifying a specific unit.

The papers' reported model scores are not comparable claims of superiority for Lumen: cohorts, targets, feature sets, selection and evaluation methods can differ. The publicly downloaded extension has 55 inputs after removing all four targets, while the original article describes 54 features. Use the actual release schema and source hash when stating the implemented feature count.

## Verified labels and uncertainty

| Raw feature | Source-backed interpretation or unit | Display recommendation |
|---|---|---|
| Age | Years, explicit in source Table 1 | Age (years) |
| Weight | kg, explicit in Table 1 | Weight (kg) |
| BMI | Body mass index, kg/m², explicit in Table 1 | BMI (kg/m²) |
| EF-TTE | Source table gives EF, ejection fraction, %; mapping to supplied column is consistent with name and group | Ejection fraction (%) with a source note; do not describe a novel imaging measurement |
| DM / HTN / FH | Diabetes mellitus / hypertension / family history in primary table footnote | Expand with the source labels; preserve raw input encoding |
| CRF / CVA / CHF / DLP | Chronic renal failure / cerebrovascular accident / congestive heart failure / dyslipidemia in primary footnote | Explain as recorded indicators, not newly diagnosed findings |
| FBS / TG / LDL / HDL / BUN | Fasting blood sugar / triglyceride / low-density lipoprotein / high-density lipoprotein / blood urea nitrogen in primary footnote | Names may be expanded; source Table 2 does not itself verify mg/dL |
| ESR / HB / K / Na / WBC | Erythrocyte sedimentation rate / hemoglobin / potassium / sodium / white blood cell in primary footnote | Do not guess measurement units from typical clinical use |
| Lymph / Neut / PLT | Lymphocyte / neutrophil / platelet in primary footnote | Do not assume percent/count scaling without source verification |
| Region RWMA | Regional wall motion abnormality; source echo feature | Recorded category/code, not a lesion coordinate, segment geometry or verified abnormal-region count |
| VHD | Valvular heart disease with severity categories in source Table 2 | Recorded severity category; preserve original categories |
| Obesity | Original paper uses a BMI-derived indicator with its own threshold | Preserve recorded source label; do not relabel it as a modern clinical definition or independently recompute it |
| CR | Original primary paper inconsistently prints “Creatine” in footnotes | Retain CR pending a stronger source; do not silently correct to creatinine or add mg/dL |
| Length, BP, PR, LowTH Ang and detailed ECG labels | Specific unit/code semantics not fully verified by the readable source portions in this audit | Preserve source field names and values; avoid invented units, severity or timing |

Observed min/max values in a schema describe development records. They are neither clinical reference intervals nor evidence that values outside the range are impossible. The source spells the sex category `Fmale`; an interface may explain the display spelling while preserving the trained encoder's original value. Binary encodings, ordinal codes and categorical levels must match the exported schema.

## Practical operational grouping

The five groups below cover the actual 55 inputs exactly once. This is our availability experiment definition, informed by the source's four categories. Splitting laboratory and echo is an explicit operational choice, and demographic/history includes medical history indicators. It is not a claim that the source published this exact five-stage workflow.

```python
groups = {
    'history': [
        'Age', 'Weight', 'Length', 'Sex', 'BMI', 'DM', 'HTN',
        'Current Smoker', 'EX-Smoker', 'FH', 'Obesity', 'CRF', 'CVA',
        'Airway disease', 'Thyroid Disease', 'CHF', 'DLP',
    ],
    'examination': [
        'BP', 'PR', 'Edema', 'Weak Peripheral Pulse', 'Lung rales',
        'Systolic Murmur', 'Diastolic Murmur', 'Typical Chest Pain',
        'Dyspnea', 'Function Class', 'Atypical', 'Nonanginal',
        'Exertional CP', 'LowTH Ang',
    ],
    'ecg': [
        'Q Wave', 'St Elevation', 'St Depression', 'Tinversion',
        'LVH', 'Poor R Progression', 'BBB',
    ],
    'laboratory': [
        'FBS', 'CR', 'TG', 'LDL', 'HDL', 'BUN', 'ESR', 'HB',
        'K', 'Na', 'WBC', 'Lymph', 'Neut', 'PLT',
    ],
    'echo': ['EF-TTE', 'Region RWMA', 'VHD'],
}
```

Counts: history 17, examination 14, ECG 7, laboratory 14, echo 3. Assert exact coverage against the release schema and exclusion of Cath/LAD/LCX/RCA in every experiment.

## Executed comparison

The five cumulative feature sets use the same frozen development row identities and outer folds:

1. History only: 17 inputs.
2. History + examination: 31 inputs.
3. History + examination + ECG: 38 inputs.
4. History + examination + ECG + laboratory: 52 inputs.
5. All groups, including echo: 55 inputs.

Imputation, scaling, encoding, hyperparameter selection and calibration/threshold selection are separately fitted inside the corresponding training partitions for each reduced feature set. The full-input profile reuses V2. Keep the model search bounded and matched across stages. Report all four targets' ROC-AUC, recall/precision/F1 at the prespecified fitted operating rule, and Brier score. Show paired differences from identical outer validation records, along with actual input counts. Describe intervals as conditional if fixed OOF predictions are bootstrapped.

Optional bounded complements are all-minus-ECG, all-minus-laboratory and all-minus-echo. These isolate availability groups more directly than cumulative stages; they still require separate fitting. Do not optimize which group to remove on final holdout labels.

This comparison can answer: **How much predictive evidence survives when an input group is unavailable?** It does not estimate the clinical value of ordering a test, test cost, treatment effect, or a validated sequence of care. The original dataset does not establish temporal acquisition order. Names such as “history only” describe available model inputs, not an endorsed diagnostic pathway.

The integrated app provides a selector for these separately fitted profiles and routes development cases to the corresponding excluding-fold model. It shows required groups and measured development evidence, and updates vessel probabilities through the selected profile's model. Never simulate genuine missing-group robustness merely by nulling an entire group in the existing full-input model. If that simpler nulling behavior is retained for exploration, label it as imputation sensitivity without a validated outcome claim.

## Acceptance for reporting

- Save feature-set membership and model/artifact IDs with every result.
- Preserve the identical outer folds and report all targets, including deterioration.
- Choose the final model family/profile/calibration/threshold before final holdout scoring.
- Actual profile comparison and live switching now work; preserve the development-only qualification for reduced profiles.
- Use primary-source verified units; keep unresolved fields transparent rather than adding plausible medical labels.


## Measured development profile results

| Profile | Inputs | CAD AUC | LAD AUC | LCX AUC | RCA AUC |
|---|---:|---:|---:|---:|---:|
| History | 17 | 0.828 | 0.713 | 0.736 | 0.682 |
| History + examination | 31 | 0.921 | 0.776 | 0.732 | 0.708 |
| History + examination + ECG | 38 | 0.937 | 0.798 | 0.714 | 0.726 |
| History + examination + ECG + laboratory | 52 | 0.922 | 0.791 | 0.706 | 0.724 |
| All recorded inputs (+ echo) | 55 | 0.926 | 0.814 | 0.701 | 0.722 |

Saved evidence: `training/results-availability/benchmark.json`. The run elapsed 121.1 seconds on local CPU. Export checks covered 4840 OOF outputs at tolerance 1e-12. Additional groups do not uniformly improve every target; these measurements do not establish clinical test benefit or a care sequence. No reduced-profile final holdout comparison was used to select the submitted model.
