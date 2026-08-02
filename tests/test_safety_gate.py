import unittest
from backend.safety_gate import SafetyGate, get_alert_history
from backend.pipeline import VDAPipeline

class TestSafetyGate(unittest.TestCase):

    def test_safety_gate_triggers_on_chest_pain(self):
        gate = SafetyGate()
        result = gate.check("I am having severe chest pain spreading to my left arm", session_id="test_s1")
        self.assertTrue(result.escalate)
        self.assertEqual(result.reason, "cardiac_emergency")
        self.assertIn("EMERGENCY ALERT", result.response_text)

    def test_safety_gate_triggers_on_hindi_emergency(self):
        gate = SafetyGate()
        result = gate.check("Mujhe seene mein tez dard ho raha hai", session_id="test_s2")
        self.assertTrue(result.escalate)
        self.assertEqual(result.reason, "cardiac_emergency")

    def test_safety_gate_bypasses_llm_in_pipeline(self):
        pipeline = VDAPipeline()
        turn = pipeline.process_turn(session_id="test_s3", text_input="Subah se saans lene mein bahut dikkat ho rahi hai")
        self.assertTrue(turn["safety_escalated"])
        self.assertEqual(turn["safety_reason"], "respiratory_emergency")
        self.assertTrue("EMERGENCY ALERT" in turn["response_text"] or "आपातकालीन" in turn["response_text"])
        self.assertIn("SAFETY_RULE_ENGINE", turn["sources"])

    def test_safety_gate_alert_hook(self):
        pipeline = VDAPipeline()
        initial_alerts = len(get_alert_history())
        pipeline.process_turn(session_id="test_s4", text_input="Mera ek taraf ka haath sunn ho gaya hai")
        updated_alerts = len(get_alert_history())
        self.assertEqual(updated_alerts, initial_alerts + 1)

if __name__ == "__main__":
    unittest.main()
