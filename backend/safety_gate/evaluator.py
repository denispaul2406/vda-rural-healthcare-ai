import sys
import os
import csv
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.safety_gate.gate import SafetyGate

logger = logging.getLogger(__name__)

def run_safety_gate_evaluation(csv_filepath: str = "data/test_sets/safety_gate_eval.csv"):
    """
    Evaluates Safety Gate performance against the benchmark dataset.
    Calculates True Positives, False Positives, True Negatives, False Negatives,
    Precision, Recall, and F1-Score.
    """
    if not os.path.exists(csv_filepath):
        logger.error(f"Evaluation dataset not found at {csv_filepath}")
        return None

    gate = SafetyGate()
    tp, fp, tn, fn = 0, 0, 0, 0
    failures = []

    with open(csv_filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            utterance = row["utterance"]
            expected_red_flag = row["is_red_flag"].lower() == "true"
            lang = row.get("language", "en")
            
            result = gate.check(utterance, session_id="eval_session", lang_code=lang)
            predicted_red_flag = result.escalate

            if expected_red_flag and predicted_red_flag:
                tp += 1
            elif not expected_red_flag and predicted_red_flag:
                fp += 1
                failures.append({"type": "FP", "utterance": utterance, "reason": result.reason})
            elif not expected_red_flag and not predicted_red_flag:
                tn += 1
            elif expected_red_flag and not predicted_red_flag:
                fn += 1
                failures.append({"type": "FN", "utterance": utterance, "notes": row.get("notes")})

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    metrics = {
        "total_samples": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "failures": failures
    }

    print("\n=======================================================")
    print(" [EVALUATION REPORT] VDA SAFETY GATE BENCHMARK")
    print("=======================================================")
    print(f"Total Test Samples Evaluated: {total}")
    print(f"True Positives (Correct Escalations) : {tp}")
    print(f"True Negatives (Correct Non-Escalated): {tn}")
    print(f"False Positives (Over-escalated)      : {fp}")
    print(f"False Negatives (Missed Emergency)   : {fn}")
    print(f"-------------------------------------------------------")
    print(f"RECALL    : {recall * 100:.2f}%  (High recall avoids missed red-flags)")
    print(f"PRECISION : {precision * 100:.2f}%")
    print(f"F1-SCORE  : {f1:.4f}")
    print("=======================================================\n")

    if failures:
        print("Failure Analysis:")
        for f_item in failures:
            safe_text = f_item['utterance'].encode('ascii', 'backslashreplace').decode('ascii')
            print(f" - [{f_item['type']}] '{safe_text}'")

    return metrics

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_safety_gate_evaluation()
