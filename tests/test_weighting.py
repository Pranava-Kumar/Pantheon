import pytest
from pantheon.mmci.scoring import compute_consensus_score
from pantheon.mmci.weights import WeightManager

def test_compute_consensus_score_weighted():
    weights = {
        "model_a": 0.8,
        "model_b": 0.2
    }
    signals = [
        {"model_id": "model_a", "direction": "BUY", "confidence": 1.0},
        {"model_id": "model_b", "direction": "SELL", "confidence": 1.0},
    ]
    # Weighted S = (0.8 * 1.0) + (0.2 * -1.0) = 0.8 - 0.2 = 0.6
    score = compute_consensus_score(signals, weights)
    assert score == 0.6

def test_weight_manager_update():
    wm = WeightManager({
        "model_a": 0.33,
        "model_b": 0.33,
        "model_c": 0.34
    })
    # model_a is correct, model_b is wrong, model_c is ignored
    signals = [
        {"model_id": "model_a", "direction": "BUY", "confidence": 1.0},
        {"model_id": "model_b", "direction": "SELL", "confidence": 1.0},
    ]
    new_weights = wm.update(signals, "BUY")
    
    assert new_weights["model_a"] > 0.33
    assert new_weights["model_b"] < 0.33
    assert round(sum(new_weights.values()), 6) == 1.0

def test_weight_manager_bounds():
    # Floor is 0.05, Ceiling is 0.40
    # Use 5 models to ensure bounds are possible
    wm = WeightManager({
        "model_a": 0.2,
        "model_b": 0.2,
        "model_c": 0.2,
        "model_d": 0.2,
        "model_e": 0.2
    })
    
    # model_a is consistently good
    signals = [{"model_id": "model_a", "direction": "BUY", "confidence": 1.0}]
    for _ in range(50):
        wm.update(signals, "BUY")
    
    weights = wm.get_weights()
    assert weights["model_a"] <= 0.40 + 1e-5
    assert all(w >= 0.05 - 1e-5 for w in weights.values())
