import logging
from backend.safety_gate.gate import SafetyGate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADVERSARIAL_SAMPLES = [
    {
        "utterance": "I am feeling fine after my morning walk, but suddenly I felt a severe crushing chest pain",
        "expected_escalate": True,
        "expected_reason": "cardiac_emergency",
        "description": "Cardiac emergency buried in benign small talk about morning walk"
    },
    {
        "utterance": "Mujhe dawai ki timing batayein, aur haan kal raat behosh ho gaya tha",
        "expected_escalate": True,
        "expected_reason": "syncope_emergency",
        "description": "Routine medication schedule question mixed with a syncope episode"
    },
    {
        "utterance": "Mera sugar level 140 hai par mere ek haath sunn ho raha hai aur bol nahi pa raha",
        "expected_escalate": True,
        "expected_reason": "stroke_emergency",
        "description": "Normal sugar reading mixed with FAST stroke symptoms"
    },
    {
        "utterance": "I took my BP medicine on time today but my blood pressure is 195 over 125 and I feel dizzy",
        "expected_escalate": True,
        "expected_reason": "metabolic_crisis",
        "description": "Good adherence report mixed with hypertensive crisis reading (195/125)"
    },
    {
        "utterance": "Subah se ghutne mein dard hai aur seene mein tez dard ho raha hai",
        "expected_escalate": True,
        "expected_reason": "cardiac_emergency",
        "description": "Benign knee joint pain mixed with acute cardiac chest pain"
    }
]

def test_mixed_signal_adversarial():
    logger.info("=== RUNNING MIXED-SIGNAL ADVERSARIAL SAFETY GATE BENCHMARK ===")
    gate = SafetyGate()
    passed_count = 0

    for idx, sample in enumerate(ADVERSARIAL_SAMPLES, 1):
        res = gate.check(sample["utterance"], session_id=f"adv_s{idx}")
        assert res.escalate == sample["expected_escalate"], f"Failed on sample {idx}: {sample['description']}"
        assert res.reason == sample["expected_reason"], f"Reason mismatch on sample {idx}"
        logger.info(f"✅ PASS Test {idx}: [{res.reason}] - Utterance: '{sample['utterance'][:50]}...'")
        passed_count += 1

    print("\n=======================================================")
    print(f" ALL {passed_count}/{len(ADVERSARIAL_SAMPLES)} ADVERSARIAL MIXED-SIGNAL TESTS PASSED 100%! ")
    print("=======================================================")

if __name__ == "__main__":
    test_mixed_signal_adversarial()
