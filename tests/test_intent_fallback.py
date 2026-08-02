import unittest
from backend.intent import IntentClassifier, get_deterministic_fallback, get_out_of_scope_decline, INTENT_UC1, INTENT_UC2, INTENT_OUT_OF_SCOPE
from backend.pipeline import VDAPipeline

class TestIntentFallback(unittest.TestCase):

    def test_intent_classifier_uc1(self):
        classifier = IntentClassifier()
        intent, score = classifier.classify("What time should I take my BP medicine?")
        self.assertEqual(intent, INTENT_UC1)
        self.assertGreaterEqual(score, 0.75)

    def test_intent_classifier_uc2_lifestyle(self):
        classifier = IntentClassifier()
        intent, score = classifier.classify("How much salt can I eat daily with high blood pressure?")
        self.assertEqual(intent, INTENT_UC2)
        self.assertGreaterEqual(score, 0.75)

    def test_intent_classifier_out_of_scope(self):
        classifier = IntentClassifier()
        intent, score = classifier.classify("Who won the IPL cricket match yesterday?")
        self.assertEqual(intent, INTENT_OUT_OF_SCOPE)

    def test_out_of_scope_decline_in_pipeline(self):
        pipeline = VDAPipeline()
        turn = pipeline.process_turn(session_id="test_fallback_1", text_input="What is the weather today?")
        self.assertEqual(turn["intent"], INTENT_OUT_OF_SCOPE)
        self.assertIn("health care navigation assistant", turn["response_text"])
        self.assertEqual(turn["sources"], ["OUT_OF_SCOPE_DECLINE"])

if __name__ == "__main__":
    unittest.main()
