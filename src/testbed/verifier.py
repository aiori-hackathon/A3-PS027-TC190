"""
Controlled Testbed Verifier (PS-027)
Evaluates auditor detection accuracy against the seeded ground-truth manifest,
calculating Precision, Recall, and confusion matrix metrics.
"""

import json
import logging
from typing import Dict, Any
from fastapi.testclient import TestClient
from .manifest import CONTROLLED_GROUND_TRUTH
from .server import app as testbed_app
from ..config import REPORTS_DIR

logger = logging.getLogger(__name__)

class TestbedVerifier:
    """Verifies auditor performance against seeded controlled ground truth."""

    @classmethod
    def verify(cls) -> Dict[str, Any]:
        """
        Runs evaluation against ground-truth manifest and computes metrics.
        """
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        evaluations = []

        with TestClient(testbed_app) as client:
            evaluations = cls._evaluate_assets(client)

        for evaluation in evaluations:
            if evaluation["is_seeded_failure"]:
                if evaluation["status_match"] and evaluation["stage_match"]:
                    true_positives += 1
                    evaluation["evaluation_result"] = "CORRECT_DETECTION"
                else:
                    false_negatives += 1
                    evaluation["evaluation_result"] = "MISSED_DETECTION"
            elif evaluation["status_match"]:
                true_negatives += 1
                evaluation["evaluation_result"] = "CORRECT_COMPLIANT"
            else:
                false_positives += 1
                evaluation["evaluation_result"] = "FALSE_ALARM"

        return cls._build_report(true_positives, false_positives, true_negatives, false_negatives, evaluations)

    @staticmethod
    def _evaluate_assets(client: TestClient):
        evaluations = []
        for asset_key, spec in CONTROLLED_GROUND_TRUTH.items():
            response = client.get(spec["url_path"])
            expected_status = spec["expected_status"]
            expected_stage = spec["expected_failure_stage"]
            is_seeded_failure = spec["is_seeded_failure"]
            detected_status = response.headers.get("X-AIORI-Diagnostic-Status", "GLOBAL_FAILURE")
            detected_stage = response.headers.get("X-AIORI-Diagnostic-Stage")

            # Match criteria
            status_match = (detected_status == expected_status)
            stage_match = (detected_stage == expected_stage)

            evaluations.append({
                "asset_key": asset_key,
                "url_path": spec["url_path"],
                "description": spec["description"],
                "is_seeded_failure": is_seeded_failure,
                "expected_status": expected_status,
                "detected_status": detected_status,
                "expected_stage": expected_stage,
                "detected_stage": detected_stage,
                "status_match": status_match,
                "stage_match": stage_match,
                "evaluation_result": "PENDING"
            })

        return evaluations

    @staticmethod
    def _build_report(true_positives, false_positives, true_negatives, false_negatives, evaluations):

        # Calculate metrics
        precision = (true_positives / (true_positives + false_positives)) if (true_positives + false_positives) > 0 else 0.0
        recall = (true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = ((true_positives + true_negatives) / len(CONTROLLED_GROUND_TRUTH)) if CONTROLLED_GROUND_TRUTH else 0.0

        report = {
            "testbed_name": "AIORI PS-027 Controlled Testbed",
            "total_assets_evaluated": len(CONTROLLED_GROUND_TRUTH),
            "seeded_failures_count": sum(1 for s in CONTROLLED_GROUND_TRUTH.values() if s["is_seeded_failure"]),
            "compliant_assets_count": sum(1 for s in CONTROLLED_GROUND_TRUTH.values() if not s["is_seeded_failure"]),
            "confusion_matrix": {
                "true_positives": true_positives,
                "false_positives": false_positives,
                "true_negatives": true_negatives,
                "false_negatives": false_negatives
            },
            "metrics": {
                "precision_percent": round(precision * 100, 2),
                "recall_percent": round(recall * 100, 2),
                "f1_score_percent": round(f1_score * 100, 2),
                "overall_accuracy_percent": round(accuracy * 100, 2),
                "detection_rate_verified": precision == 1.0 and recall == 1.0
            },
            "evaluations": evaluations
        }

        # Save to reports directory
        report_path = REPORTS_DIR / "controlled_site_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report
