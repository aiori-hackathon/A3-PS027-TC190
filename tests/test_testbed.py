"""
Unit Tests for Controlled Testbed Ground-Truth Verification (PS-027)
"""

import pytest
from src.testbed.verifier import TestbedVerifier
from src.testbed.manifest import CONTROLLED_GROUND_TRUTH

def test_testbed_ground_truth_metrics():
    """Verify that testbed verification delivers 100% precision and 100% recall."""
    report = TestbedVerifier.verify()
    metrics = report["metrics"]
    
    assert metrics["precision_percent"] == 100.0
    assert metrics["recall_percent"] == 100.0
    assert metrics["f1_score_percent"] == 100.0
    assert metrics["overall_accuracy_percent"] == 100.0
    assert metrics["detection_rate_verified"] is True

def test_testbed_seeded_failures_detected():
    """Verify that every single seeded failure is correctly identified."""
    report = TestbedVerifier.verify()
    evaluations = report["evaluations"]
    
    for ev in evaluations:
        assert ev["status_match"] is True
        assert ev["stage_match"] is True
        if ev["is_seeded_failure"]:
            assert ev["evaluation_result"] == "CORRECT_DETECTION"
        else:
            assert ev["evaluation_result"] == "CORRECT_COMPLIANT"
