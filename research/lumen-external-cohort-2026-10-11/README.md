# Independent coronary cohort search, 11 October 2026

No cohort was admitted for external validation of the frozen 55-input, four-target Lumen model in this bounded search. This is a documented negative compatibility result, not proof that no suitable cohort exists anywhere. No model was fitted, adapted, calibrated, threshold-tuned or scored. The existing 61-record holdout was not opened or rescored.

The most relevant independently collected public source was **AngioCAD**. Its small clinical workbook was acquired and its column headers inspected. It lacks all 14 Lumen examination inputs and all seven ECG inputs. It therefore cannot validate the frozen full model without substituting or manufacturing entire input groups.

## AngioCAD: public and independent in origin, incompatible with this model

The [primary 2026 paper](https://doi.org/10.1016/j.cmpb.2026.109368) describes 413 patients, angiography sequences, artery labels, and clinical/laboratory information. Its ethics statement identifies retrospective collection at Shahid Chamran Heart Center in Isfahan. This differs from the original Z-Alizadeh source institution in Tehran. Institution-level provenance supports independent origin; collection dates and actual patient non-overlap have not been verified.

The [official dataset](https://zenodo.org/records/15826856) is Open and CC BY 4.0, verified in the browser. It exposes separate feature and label workbooks plus 16.4 GB of video archives. [Registered DOI metadata](https://api.datacite.org/dois/10.5281/zenodo.15826856) confirms the license and seven stenosis severity categories. Direct automated HTTP requests returned 403 here, but browser access succeeded. Those errors are not evidence of restricted access.

Only `AngioCAD_Features.xlsx` was acquired: 129,493 bytes, host MD5 `1617d242df42367787f445392729f35e`, SHA-256 `978f2415ab52f11724e1ef00bb63597b8497487afd84b97f7112fc7975a33295`. The host MD5 matches. Only worksheet metadata and first-row headers were decoded. This file also contains outcome-related columns, so it is quarantined research material rather than an app or training input. No participant-level cells were read. The separate label workbook and videos were not acquired.

| Lumen group | Required inputs | Same-name headers | Possible aliases, unapproved | No header candidate |
|---|---:|---:|---:|---:|
| History | 17 | 8 | 2 | 7 |
| Examination | 14 | 0 | 0 | 14 |
| ECG | 7 | 0 | 0 | 7 |
| Laboratory | 14 | 7 | 4 | 3 |
| Echocardiography | 3 | 0 | 1 | 2 |
| Total | 55 | 15 | 7 | 33 |

Same names do not establish matching units, categories or clinical definitions. The seven possible aliases are `Cr` to `CR`, `BUN ` to `BUN`, `Hgb` to `HB`, `leukocytes` to `WBC`, `LVEF` to `EF-TTE`, `Stroke` to `CVA`, and `Hyperlipidemia` to `DLP`. None was approved or used to map patient values.

The workbook declares `Main!A1:BH380`. This is a worksheet used range, not a verified patient count. Its difference from the paper's 413 patients remains unresolved. Segment headers alone do not establish how seven severity categories map to the original >=50% diameter-narrowing labels, how boundary values are handled, or how branch and left-main disease aggregate. No outcome values were inspected to resolve these questions.

The [machine-readable compatibility audit](angiocad-compatibility-audit.json) records all 55 feature decisions and every missing input. The [header-only inspection manifest](angiocad-features-schema.json) records exact cells and source hashes. Full-model scoring is rejected on the missing-group evidence alone.

## Other candidates examined

| Source | Access and provenance | Compatibility result |
|---|---|---|
| [UCI 411 extension](https://archive.ics.uci.edu/dataset/411), [UCI 412 base](https://archive.ics.uci.edu/dataset/412), and the authors' [Mendeley base](https://data.mendeley.com/datasets/vrymwyh2tg/1) and [extension](https://data.mendeley.com/datasets/9k56pwtvz9/1) | Public CC BY 4.0. The author descriptions identify the same 303 records; the extension adds vessel labels. | **Excluded for cohort reuse.** Separate hosts or added columns do not create independent patients. No new download or score. |
| [Near East University 475-patient cohort](https://doi.org/10.3390/math10030311) | Primary paper describes NEU Hospital, Nicosia, patient records from 2016-2020. Its data-availability statement points only to Z-Alizadeh, and no public NEU release was identified. | **Incompatible documented contract.** The paper uses 29 mutual variables, merging murmur and chest-pain indicators and reducing RWMA/VHD to presence. It does not provide a public all-55, four-target patient file. Table 1 reports units but contains a WBC summary inconsistency, so it cannot serve as a clean unit-conversion codebook. |
| [MultiD4CAD](https://www.nature.com/articles/s41597-025-05743-w), [current official dataset v2](https://zenodo.org/records/15148653) | Independent Palermo cohort of 118 suspected-CAD patients. Dataset files are restricted and require a signed DUA and authorization. | **Incompatible and unavailable within this scope.** Clinical fields are limited risk factors/demographics, and imaging/labels concern CCTA and adipose-tissue analysis. It does not supply the complete Lumen examination, ECG, laboratory and echo contract or establish four matching invasive-angiography endpoints. No DUA submitted or email sent. |
| [ARCADE primary paper](https://www.nature.com/articles/s41597-023-02871-z), [official dataset](https://zenodo.org/records/10390295) | Independent Kazakhstan angiography archive. Public project data use CC0. | **Image-task mismatch.** Released records comprise image and mask/box annotations for segment classification and stenosis detection. The release does not supply Lumen's 55 clinical inputs as a patient table. No image data downloaded. |
| [UCI Heart Disease](https://archive.ics.uci.edu/dataset/45) | Public historical hospital datasets, CC BY 4.0. | **Feature/endpoint mismatch.** Its common 13-input task and raw 76-attribute descriptions do not implement Lumen55. Binary `fbs` is not continuous FBS; exercise heart rate is not resting PR; radionuclide EF is not TTE EF. The vessel-count predictor does not establish Lumen's separate vessel outcomes. No cohort admitted, downloaded or scored. |

The public [CONFIRM raw-data listing](https://data.mendeley.com/datasets/compare/p77tpbrgyb), the [fQRS/ICD listing](https://data.mendeley.com/datasets/gx9v4v8xtp/1), and the [SYNTAX calculator](https://figshare.com/articles/dataset/Excel-Based_SYNTAX_Score_Calculator_500_cases/17148767) were also screened as secondary leads. Their accessible metadata did not establish the all-55 and four-target contract. The calculator is a data-entry tool, not evidence that 500 independent patient records are released. No patient files from these leads were acquired.

## Preserved protocol and honest next step

[admission-protocol.json](admission-protocol.json) was saved before any independent participant-level outcome inspection. It freezes the source/input/model hashes, admission criteria, required source-specific harmonization, outcome blinding, fixed models and thresholds, evaluation metrics, shared patient-bootstrap resampling, and the requirement to obtain parent authorization before scoring. It remains unchanged. Published aggregate descriptions were used only for eligibility screening.

The current full-model claim must remain a small, single-source internal evaluation. An external score cannot be added from AngioCAD, a mirror, a replacement endpoint, or full-group imputation. The practical follow-up is to obtain an independent angiography cohort that **actually measured** all required groups, with original clinical codebooks, units, measurement timing, sampling dates, patient overlap safeguards, and Cath/LAD/LCX/RCA outcomes using the same threshold. Fix the source-specific mapping before labels, then evaluate the existing frozen models without retuning. Acquiring data through a signed agreement or contacting investigators requires a separate authorized action.

A reduced-input or image model would be a new research task with a new protocol, not a validation result for the shipped Lumen55 model. Until a qualifying cohort exists, product delivery and usability evidence can improve; external clinical validity remains unestablished.

## Separate reduced experiment feasibility

The requested follow-up was also screened before participant rows. **AngioCAD is not ready for a reduced shared-feature experiment:** the workbook has no comments, custom XML or codebook sheet, and the accessible source descriptions do not document predictor units or category codes. Its 15 same-name columns and seven possible aliases remain unapproved. The primary-paper browser page presents a CAPTCHA, which was not solved. This is a documentation gap, not a reason to infer measurements from observed values.

A narrowly scoped historical alternative exists for **a new Age/Sex CAD model**, using the Hungarian, Switzerland and Long Beach VA datasets in [UCI Heart Disease](https://archive.ics.uci.edu/dataset/45). Their [official 1988 codebook](https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/heart-disease.names) explicitly documents age in years and sex as 1=male, 0=female. The original Z-Alizadeh authors' Table 1 documents age in years and male/female sex, enabling those two input mappings without imputing absent groups. The [1989 primary paper](https://doi.org/10.1016/0002-9149(89)90524-9) establishes those independently collected hospital cohorts. The candidate excludes Cleveland 303 and all Z-Alizadeh mirrors.

This option has a material endpoint difference: UCI describes angiographic disease as **>50%** in any major vessel and a binary presence mapping of `num=1,2,3,4`, whereas the Z-Alizadeh source uses **>=50%** and the three named vessels. The exact 50% boundary and vessel aggregation are not harmonized. A parent-approved new protocol could retain and disclose this difference as an **exploratory historical endpoint and population transport test**. It cannot honestly claim exact same-target external validation or contemporary clinical validity. Codebook counts (294 Hungarian, 123 Swiss, 200 VA) also differ from some counts in the primary publication; file coverage must be accounted for before results.

[reduced-experiment-feasibility.json](reduced-experiment-feasibility.json) records the two verified input mappings, endpoint definitions, source citations, and conditions. No historical cohort rows were acquired, no new model was trained, and no source-specific evaluation protocol was activated. The parent must decide whether this deliberately limited new research task improves the project before any further stage.

This research used primary papers and official repositories/registries. It was a targeted compatibility search, not a systematic review. The source-download manifest and local reference files preserve reproducible provenance. No GPU, private credential or paid API was used.


Release packaging note: the source package retains compatibility/admission metadata and this source-linked dossier. Downloaded participant workbooks and article/page archives remain quarantined in the local research workspace and are excluded from the distributable source. The download manifest records their local acquisition hashes; it does not imply their inclusion in the release.
