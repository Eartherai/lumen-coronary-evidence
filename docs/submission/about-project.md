## Inspiration

Five models can agree and still be wrong. A compelling 3D heart can make their output look more convincing without making it more reliable.

That question shaped Lumen: **can we make a coronary prediction something people can investigate, rather than simply accept?** We wanted the anatomy, measurements, explanation and recorded outcome to stay connected, including when the model fails.

## What it does

Lumen is an educational coronary prediction and evidence explorer. It predicts the dataset's overall coronary artery disease label and stenosis status for the LAD, LCX and RCA, using demographic, clinical examination, ECG, laboratory and echocardiographic measurements.

Users can:

- Rotate, zoom, select, focus and isolate named coronary arteries in an interactive 3D heart.
- Trace a probability through its exact feature contributions and complete log-odds calculation.
- Compare the same record across five separately fitted input profiles, from 17 history features to all 55 measurements.
- Edit inputs and recalculate locally, with outcome comparison disabled when the original measurements change.
- Investigate every one of the 242 development records through an error audit and export the supporting evidence.

Our favorite demonstration is **UCI411-020**. Its full-input LCX estimate is **22.2%**, below its **33.0%** research cutoff, but the recorded LCX label is positive. All five profiles miss it. Across the complete development cohort, five LCX flags agree on 172 records and are wrong on 60. Lumen makes those shared mistakes visible and traceable. These examples are selected using development outcomes; they are error investigations, not additional blinded tests.

## How we built it

We used the public Extension of Z-Alizadeh Sani dataset from the UCI Machine Learning Repository: 303 records, split into 242 development records and a separate 61-record final test. Cath, LAD, LCX and RCA are excluded from every input feature set.

Regularized logistic procedures use five outer development folds and three inner folds for selection. Each displayed development record's fold is excluded from preprocessing, fitting, calibration, cutoff selection and the explanation reference. The full-input procedure was frozen before the final test was scored once.

Python exports portable model weights. A standard-library Python backend and a JavaScript browser implementation evaluate the same models locally. Three.js renders source-identified BodyParts3D meshes, with whole-vessel colors tied to the corresponding predictions. Training and inference need no cloud GPU or paid model API; rendering uses ordinary WebGL.

The explanations are grouped interventional linear SHAP in log-odds. Actual SHAP LinearExplainer checks verified **4,840 explanations across 100 excluding-fold models**, with a maximum grouped-contribution discrepancy of **5.55e-17** at a tolerance of 1e-12.

## Results and what they mean

These results use the separate **61-record frozen test** and development-selected cutoffs:

| Target | ROC-AUC | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Overall CAD | 0.908 | 0.836 | 0.851 | 0.930 | 0.889 |
| LAD | 0.893 | 0.852 | 0.814 | 0.972 | 0.886 |
| LCX | 0.748 | 0.607 | 0.535 | 0.852 | 0.657 |
| RCA | 0.724 | 0.590 | 0.500 | 0.760 | 0.603 |

LCX produced 20 false positives and four false negatives; RCA produced 19 and six. Those costs remain visible alongside favorable metrics. The small same-source test does not establish external or clinical validity.

## Challenges we faced

The hardest work was keeping model identity, anatomy, explanation and outcome consistent through profile changes, edited measurements and failed requests. We also had to prevent target leakage, preserve exact artery correspondence and separate baseline probabilities from research cutoffs.

A real Safari rendering failure led us to draw completed anatomy frames immediately and after control changes, rather than depend entirely on animation callbacks. The current source passed clean-extraction verification with **20 Python tests, 59 Node tests and 64 journey assertions**. Actual Safari and Chromium checks used the same Mac; these are software checks, not human usability evidence.

## Accomplishments and what we learned

We built a complete loop from a cohort error to its artery, exact score, input-profile comparison and recorded outcome. We learned that model agreement is not confidence, feature attribution is not causality, and reproducibility needs checks at the interfaces between components.

Our contribution is this integrated investigation workflow. The underlying classification and explanation methods are established.

## What's next

We want endpoint-compatible independent validation, better LCX/RCA discrimination and false-positive tradeoffs, and real first-time user feedback. Any new modeling experiment needs untouched evaluation data; the already scored final test will stay frozen.

## Responsible scope and credits

**Lumen is an educational research prototype, not validated for clinical use and not a substitute for diagnostic imaging.** The anatomy is generic reference geometry. Colors do not locate patient lesions, show percentage narrowing, or recommend treatment. SHAP describes model associations rather than causal effects.

Dataset: UCI Machine Learning Repository, Extension of Z-Alizadeh Sani. Anatomy: BodyParts3D, The Database Center for Life Science, CC BY 4.0. Original project code uses MIT; upstream resources keep their own terms.

**AI assistance:** OpenAI Codex assisted research, implementation, experiments, verification and presentation. Kokoro supplied synthetic English narration; HyperFrames and GSAP assembled the demo. The human submitter is responsible for the work and its explanation. AI tools are disclosed and are not human teammates.
