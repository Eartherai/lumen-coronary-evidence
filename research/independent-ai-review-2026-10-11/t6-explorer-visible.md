01
Choose a case
Development case
UCI411-171
UCI411-050
UCI411-148
UCI411-168
UCI411-205
UCI411-128
UCI411-051
UCI411-288
Unlabelled input form
Audit record UCI411-057
Available input groups
History · 17 inputs
History + examination · 31 inputs
History + examination + ECG · 38 inputs
History + examination + ECG + laboratory · 52 inputs
All recorded inputs (+ echo) · 55 inputs

55 model inputs. Each availability profile was independently fitted and validated.

UCI411-171 · validation fold 3. This entire fold was excluded from fitting, calibration and threshold selection.

50
Age in years
F
Recorded sex
Recorded measurements
Edit inputs
Weight
73
BMI
28.52
Blood pressure
180
Pulse rate
100
Ejection fraction
55
LDL
213
Typical Chest Pain
1
Hypertension
1
Diabetes
0
All model inputs
All four angiography labels are excluded from the model inputs.
02
Inspect the anatomy
Compare inputs
Reset view
Overview
Opposite view
Focus artery
Isolate artery
Overview of all reference vessels.
BODYParts3D REFERENCE ANATOMY
Probability colors the vessel, not a lesion location.
LAD
LCX
RCA
Drag to rotate · Scroll to zoom · Select a vessel
Heart surface
Lower model probability
Higher
Research decision rule
Training-selected F1 threshold
Fixed 50% threshold
OVERALL CAD
99.7%
Positive research flag
LAD
94.4%
Positive research flag
LCX
43.8%
Positive research flag
RCA
46.1%
Positive research flag

Generic reference anatomy. No patient-specific geometry or predicted plaque location.

03
Follow the evidence
LAD

Left anterior descending artery

94.4%
Model probability
Validation fold 3

Positive research flag at 39.0%. Threshold selected from training-fold predictions. This is a research operating point.

What moved this estimate?

Grouped interventional linear SHAP · log-odds

Contributions relative to this model's training-data reference. Positive increases model log-odds; negative decreases them.

LDL
213
Increases model estimate
+0.68
Family history
1
Increases model estimate
+0.64
Typical Chest Pain
1
Increases model estimate
+0.59
Pulse rate
100
Increases model estimate
+0.46
T-wave inversion
1
Increases model estimate
+0.44
Ejection fraction
55
Decreases model estimate
-0.43
Check the complete score
Training baseline
0.569
LDL
+0.676
Family history
+0.637
Typical Chest Pain
+0.594
Pulse rate
+0.460
T-wave inversion
+0.439
Ejection fraction
-0.426
Other 49 inputs
-0.132
Final log-odds
2.817
Additive units: log-odds
Logistic(2.817) = 94.4%

Baseline log-odds 0.569 + sum of all 55 feature contributions 2.248 = 2.817. Applying the logistic function gives 94.4%. Six largest contributions are shown above; all are included in the sum.

These grouped linear SHAP values use an independent-feature background from this model's training records. One-hot terms are summed to their raw feature. Correlations are not modeled; values do not imply causal effects. The portable formula was checked against the actual SHAP library on all 160 curated development case/profile/target outputs.

PREDICTION IS NOT THE ANSWER KEY

Reveal recorded labels

Compare all four estimates with this case’s recorded angiography labels.