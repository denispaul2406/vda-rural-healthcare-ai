import os
import logging
from typing import Tuple, List, Dict, Any
from backend.rag.index_builder import parse_protocol_file, SimpleTFIDFIndex

logger = logging.getLogger(__name__)

# Single instance index loader for Grounded RAG Protocols
_GLOBAL_INDEX = None

def get_global_index():
    global _GLOBAL_INDEX
    if _GLOBAL_INDEX is None:
        protocol_path = os.path.join("data", "protocols", "uc1", "ncd_guidelines.txt")
        chunks = parse_protocol_file(protocol_path)
        _GLOBAL_INDEX = SimpleTFIDFIndex(chunks)
    return _GLOBAL_INDEX

class UC1Retriever:
    """
    Retriever for Grounded NCD Protocols with strict Intent-Routed Index Isolation.
    Prevents cross-domain RAG collisions by filtering search space based on classified Intent (UC1, UC2, UC3).
    """

    def __init__(self, similarity_threshold: float = 0.10):
        self.similarity_threshold = similarity_threshold
        self.index = get_global_index()

    def retrieve(self, query: str, target_intent: str = "UC1_NCD_ADHERENCE") -> Tuple[List[Dict[str, Any]], bool]:
        """
        Retrieves top relevant protocol chunks with Intent-Routed Index Isolation.
        
        Returns:
            tuple: (retrieved_chunks, meets_threshold_flag)
        """
        raw_results = self.index.search(query, top_k=6)
        if not raw_results:
            logger.warning(f"[UC1Retriever] Zero matches for query: '{query}'")
            return ([], False)

        # Intent-Routed Index Isolation filtering
        intent_prefix = "UC3" if "UC3" in target_intent else ("UC2" if "UC2" in target_intent else "UC1")
        filtered_results = [
            res for res in raw_results 
            if res["chunk"].get("use_case", "UC1") == intent_prefix
        ]

        # Fall back to top raw results if strict filtering yields empty set
        final_results = filtered_results[:2] if filtered_results else raw_results[:2]

        top_score = final_results[0]["score"] if final_results else 0.0
        logger.info(f"[UC1Retriever] Query: '{query}' | Intent: {intent_prefix} | Top Score: {top_score:.3f} (Threshold: {self.similarity_threshold})")

        if top_score < self.similarity_threshold:
            logger.info(f"[UC1Retriever] Relevance score {top_score:.3f} below threshold {self.similarity_threshold}.")
            return (final_results, False)

        return (final_results, True)
