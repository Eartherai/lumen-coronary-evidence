"""Standard-library inference for the exported fold-specific logistic JSON.

No target labels are accepted. This is a model sensitivity tool, not treatment advice.
"""
import math


FORBIDDEN = {"CAD", "Cath", "LAD", "LCX", "RCA", "truth", "target", "targets"}


def sigmoid(value):
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def predict_json(model_dict, raw_inputs):
    """Return probability and exact grouped log-odds contributions.

    ``model_dict`` is ``models.json['models'][model_id]``. Inputs are the complete
    raw feature dictionary from a case. ``None`` uses this fold's training imputer.
    Unknown fields and nonfinite numeric inputs are rejected. Categories absent
    from this fold use the training encoder's all-zero behavior and are reported.
    Training reference means define explanations; they are not causal effects.
    """
    expected = {f["feature"] for f in model_dict["numeric"] + model_dict["categorical"]}
    actual = set(raw_inputs)
    if actual & FORBIDDEN:
        raise ValueError("Target labels must never enter model inputs")
    if actual != expected:
        raise ValueError(f"Input feature mismatch: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    raw_log_odds = float(model_dict["intercept"])
    contributions = []
    imputed = []
    unknown_categories = []
    for field in model_dict["numeric"]:
        name, raw = field["feature"], raw_inputs[field["feature"]]
        value = float(field["impute"] if raw is None else raw)
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number or null")
        if raw is None:
            imputed.append(name)
        encoded = (value - field["mean"]) / field["scale"]
        raw_log_odds += encoded * field["coefficient"]
        contributions.append({"feature": name, "value": raw,
            "log_odds_contribution": (encoded - field["reference_encoded_mean"]) * field["coefficient"]})
    for field in model_dict["categorical"]:
        name, raw = field["feature"], raw_inputs[field["feature"]]
        value = str(field["impute"] if raw is None else raw)
        if value not in field["categories"]:
            unknown_categories.append({"feature": name, "value": value})
        if raw is None:
            imputed.append(name)
        indicators = [float(value == category) for category in field["categories"]]
        raw_log_odds += sum(x * c for x, c in zip(indicators, field["coefficients"]))
        contribution = sum((x - ref) * c for x, ref, c in zip(indicators, field["reference_encoded_means"], field["coefficients"]))
        contributions.append({"feature": name, "value": raw, "log_odds_contribution": contribution})
    if not math.isfinite(raw_log_odds) or not all(math.isfinite(c["log_odds_contribution"]) for c in contributions):
        raise ValueError("Numeric inputs exceed the finite arithmetic range of this model")
    reconstructed = model_dict["baseline_log_odds"] + sum(c["log_odds_contribution"] for c in contributions)
    if not math.isclose(raw_log_odds, reconstructed, abs_tol=1e-10):
        raise ArithmeticError("Attribution reconstruction failed")
    probability = sigmoid(raw_log_odds)
    threshold = float(model_dict.get("operating_threshold", 0.5))
    return {"probability": probability, "log_odds": raw_log_odds,
            "baseline_log_odds": model_dict["baseline_log_odds"],
            "baseline_probability": sigmoid(model_dict["baseline_log_odds"]),
            "contributions": sorted(contributions, key=lambda c: abs(c["log_odds_contribution"]), reverse=True),
            "model_id": model_dict["model_id"], "imputed_features": imputed,
            "unknown_categories": unknown_categories,
            "operating_threshold": threshold, "predicted_label": int(probability >= threshold),
            "model_family": model_dict.get("family", "unweighted"),
            "calibration": model_dict.get("calibration", {}).get("method", "none"),
            "explanation_method": "Exact linear log-odds decomposition centered on this training fold's encoded feature means; not causal."}
