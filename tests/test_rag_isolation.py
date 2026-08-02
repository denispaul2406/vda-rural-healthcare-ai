import unittest
from backend.rag import UC1Retriever, Answerer

class TestRAGIsolation(unittest.TestCase):

    def test_rag_retrieval_uc1_medicine(self):
        retriever = UC1Retriever()
        chunks, meets_thresh = retriever.retrieve("blood pressure medicine schedule timing")
        self.assertTrue(meets_thresh)
        self.assertGreater(len(chunks), 0)
        self.assertTrue("MEDICATION" in chunks[0]["chunk"]["header"] or "HYPERTENSION" in chunks[0]["chunk"]["header"])

    def test_rag_retrieval_low_relevance(self):
        retriever = UC1Retriever()
        chunks, meets_thresh = retriever.retrieve("quantum physics string theory equations")
        self.assertFalse(meets_thresh)

    def test_rag_answerer_attribution(self):
        retriever = UC1Retriever()
        answerer = Answerer()
        chunks, meets_thresh = retriever.retrieve("How much salt should I eat with high blood pressure?")
        ans, sources = answerer.generate_answer("How much salt should I eat with high blood pressure?", chunks, lang_code="en-IN")
        self.assertGreater(len(sources), 0)
        self.assertTrue("salt" in ans.lower() or "5" in ans or "teaspoon" in ans.lower())

if __name__ == "__main__":
    unittest.main()
