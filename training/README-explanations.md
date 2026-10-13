# Actual SHAP verification of the exported explanations

The exported grouped centered log-odds contributions have now been checked against the actual SHAP library for all 160 case/profile/target predictions. The accurate display name is **Grouped interventional linear SHAP (log-odds)**. This verification changes no fitted coefficient, calibration parameter, operating threshold or outcome score.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with-requirements requirements-explanation.txt python verify_shap.py
```

The run used SHAP 0.52.0 on CPU, with Python 3.12.13 and pinned explanation dependencies. Complete package versions, platform, runtime and SHA-256 identities of the script, source data, model and case artifacts are in `results-availability/explanation-version-manifest.json`. The full verification record is `results-availability/shap-verification.json`.

For each model, the verifier reconstructs its exported imputation/scaling/one-hot preprocessing without refitting it. The Independent masker contains every row from that model's original training fold, explicitly setting `max_samples` to the background row count. It excludes the explained case, its entire outer validation fold and all frozen holdout records. Every encoded background mean exactly matches the exported reference. No final holdout was predicted or scored.

The SHAP call uses the model's exported coefficient/intercept pair. For sigmoid-calibrated models these already contain the composed calibration slope and offset, so the model output remains linear log-odds. The identity link preserves those additive score units. SHAP values for indicator columns are summed back to their original raw categorical feature. Numeric features each have one encoded column.

The check covered 160 predictions, 60 distinct fold models, 8,960 encoded feature values and 120 sigmoid-calibrated predictions. At tolerance 1e-12:

- Maximum difference between grouped SHAP and exported contributions: 6.94e-18.
- Maximum expected-value baseline difference: 4.44e-16.
- Maximum reconstructed log-odds difference: 1.55e-15.
- Maximum reconstructed probability difference: 3.33e-16.

The [SHAP LinearExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html) distinguishes independent-feature interventional values from correlation-aware conditional values. The [Independent masker documentation](https://shap.readthedocs.io/en/latest/generated/shap.maskers.Independent.html) explains background integration and its default subsampling behavior. Our test uses the independent convention and the complete fitted training reference.

Interpret these values carefully: independent masking breaks predictor dependencies. Correlated clinical features can receive different attribution with a conditional explainer. Individual masked one-hot columns need not form valid categorical states; displayed raw-feature values are sums of the encoded-column SHAP values. Values describe the model's score associations, not causal effects or medical test utility. They are additive log-odds effects rather than percentage-point probability changes. The sigmoid of expected background log-odds is not mean background probability. This check establishes implementation equivalence to the specified SHAP convention, not explanation uncertainty or clinical validity.
