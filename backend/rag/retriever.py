import os
import logging
from typing import Tuple, List, Dict, Any
from backend.rag.index_builder import parse_protocol_file, SimpleTFIDFIndex

logger = logging.getLogger(__name__)

# Single instance index loader for UC1
_UC1_INDEX = None

def get_uc1_index():
    global _UC1_INDEX
    if _UC1_INDEX is None:
        protocol_path = os.path.join("data", "protocols", "uc1", "ncd_guidelines.txt")
        chunks = parse_protocol_file(protocol_path)
        _UC1_INDEX = SimpleTFIDFIndex(chunks)
    return _UC1_INDEX

class UC1Retriever:
    """
    Retriever for UC1 (NCD Care Adherence Protocols).
    Enforces strict index isolation and similarity thresholding across 33 citable ICMR/WHO protocol chunks.
    """

    def __init__(self, similarity_threshold: float = 0.12):
        self.similarity_threshold = similarity_threshold
        self.index = get_uc1_index()

    def retrieve(self, query: str) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Retrieves top relevant protocol chunks.
        
        Returns:
            tuple: (retrieved_chunks, meets_threshold_flag)
        """
        results = self.index.search(query, top_k=2)
        if not results:
            logger.warning(f"[UC1Retriever] Zero matches for query: '{query}'")
            return ([], False)

        top_score = results[0]["score"]
        logger.info(f"[UC1Retriever] Query: '{query}' | Top Score: {top_score:.3f} (Threshold: {self.similarity_threshold})")

        if top_score < self.similarity_threshold:
            logger.info(f"[UC1Retriever] Relevance score {top_score:.3f} below threshold {self.similarity_threshold}.")
            return (results, False)

        return (results, True)
