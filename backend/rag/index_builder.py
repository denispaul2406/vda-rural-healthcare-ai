import os
import re
import math
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def parse_protocol_file(filepath: str) -> List[Dict[str, str]]:
    """
    Parses structured protocol text into chunks with metadata tags.
    """
    if not os.path.exists(filepath):
        logger.error(f"Protocol file not found: {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_chunks = content.split("[PROTOCOL:")
    chunks = []

    for idx, raw_chunk in enumerate(raw_chunks):
        if not raw_chunk.strip():
            continue
        lines = raw_chunk.strip().split("\n")
        header = lines[0].replace("]", "").strip()
        body = "\n".join(lines[1:]).strip()

        chunk_record = {
            "chunk_id": f"uc1_chunk_{idx}",
            "header": header,
            "text": body,
            "use_case": "UC1"
        }
        chunks.append(chunk_record)

    logger.info(f"[IndexBuilder] Parsed {len(chunks)} protocol chunks for UC1 RAG index.")
    return chunks

class SimpleTFIDFIndex:
    """
    Lightweight, self-contained Vector Index for UC1 Protocol Retrieval.
    No heavy external C dependencies needed; guarantees 100% reliable local execution on any machine.
    """

    def __init__(self, chunks: List[Dict[str, str]]):
        self.chunks = chunks
        self.vocab = {}
        self.idf = {}
        self.doc_vectors = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\w+", text.lower())
        return [w for w in words if len(w) > 2]

    def _build_index(self):
        doc_freqs = {}
        num_docs = len(self.chunks)

        for doc in self.chunks:
            tokens = set(self._tokenize(doc["text"] + " " + doc["header"]))
            for token in tokens:
                doc_freqs[token] = doc_freqs.get(token, 0) + 1

        for token, df in doc_freqs.items():
            self.idf[token] = math.log((num_docs + 1) / (df + 1)) + 1.0

        for doc in self.chunks:
            tokens = self._tokenize(doc["text"] + " " + doc["header"])
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            
            vec = {t: count * self.idf.get(t, 0) for t, count in tf.items()}
            # Normalize vector
            norm = math.sqrt(sum(v**2 for v in vec.values())) or 1.0
            norm_vec = {t: v / norm for t, v in vec.items()}
            self.doc_vectors.append(norm_vec)

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        tokens = self._tokenize(query)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        q_vec = {t: count * self.idf.get(t, 0) for t, count in tf.items()}
        norm = math.sqrt(sum(v**2 for v in q_vec.values())) or 1.0
        q_norm_vec = {t: v / norm for t, v in q_vec.items()}

        results = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            score = sum(q_norm_vec.get(t, 0) * doc_vec.get(t, 0) for t in q_norm_vec)
            results.append((score, self.chunks[idx]))

        results.sort(key=lambda x: x[0], reverse=True)
        return [{"score": score, "chunk": chunk} for score, chunk in results[:top_k]]
