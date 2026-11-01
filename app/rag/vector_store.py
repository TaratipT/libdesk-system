import json
import math
import os
import re
from typing import List, Dict, Any, Optional
import numpy as np

# คำหยุดทั่วไป
STOP_WORDS = {
    "ห้องสมุด", "หรือ", "และ", "ใน", "การ", "ที่", "มี", "เป็น", 
    "ไป", "ได้", "ให้", "กับ", "ของ", "ได้ไหม", "หรือไม่", "ไหม",
    "บ้าง", "เท่าไร", "กี่", "อะไร", "ตรงไหน", "อยู่"
}

def tokenize_thai(text: str) -> List[str]:
    cleaned = re.sub(r"[^\w\s\.\-]", " ", text.lower())
    for sw in STOP_WORDS:
        cleaned = cleaned.replace(sw, " ")

    tokens: List[str] = []
    words = [w.strip() for w in cleaned.split() if len(w.strip()) > 0]
    tokens.extend(words)

    # ดึง 3-gram และ 4-gram สำหรับภาษาไทย
    for word in words:
        if len(word) >= 3:
            for i in range(len(word) - 2):
                tokens.append(word[i:i+3])
        if len(word) >= 4:
            for i in range(len(word) - 3):
                tokens.append(word[i:i+4])

    return tokens

class VectorStore:
    def __init__(self, data_path: str = "data/library_rules.json"):
        self.data_path = data_path
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: Optional[np.ndarray] = None
        self.load_and_index()

    def load_and_index(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"ไม่พบไฟล์: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        doc_tokens_list: List[List[str]] = []
        doc_freq: Dict[str, int] = {}

        for doc in self.documents:
            full_text = f"{doc['chapter']} {doc['title']} {doc['content']}"
            tokens = tokenize_thai(full_text)
            doc_tokens_list.append(tokens)
            
            for t in set(tokens):
                doc_freq[t] = doc_freq.get(t, 0) + 1

        sorted_vocab = sorted(doc_freq.keys())
        self.vocabulary = {term: idx for idx, term in enumerate(sorted_vocab)}
        num_docs = len(self.documents)

        # คำนวณ idf
        self.idf = {
            term: math.log((num_docs + 1) / (freq + 1)) + 1.0
            for term, freq in doc_freq.items()
        }

        # แปลงเป็น matrix เวกเตอร์แล้ว normalize
        vocab_size = len(self.vocabulary)
        vectors = np.zeros((num_docs, vocab_size), dtype=np.float32)

        for i, tokens in enumerate(doc_tokens_list):
            for t in tokens:
                if t in self.vocabulary:
                    col = self.vocabulary[t]
                    vectors[i, col] += 1.0
            for col, term in enumerate(sorted_vocab):
                vectors[i, col] *= self.idf[term]

            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm

        self.doc_vectors = vectors

    def _vectorize_query(self, query: str) -> np.ndarray:
        vocab_size = len(self.vocabulary)
        q_vec = np.zeros((vocab_size,), dtype=np.float32)
        tokens = tokenize_thai(query)

        for t in tokens:
            if t in self.vocabulary:
                col = self.vocabulary[t]
                q_vec[col] += 1.0

        for term, col in self.vocabulary.items():
            q_vec[col] *= self.idf[term]

        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec /= norm
        return q_vec

    def search(
        self, 
        query: str, 
        top_k: int = 3, 
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        if self.doc_vectors is None or len(self.documents) == 0:
            return []

        q_vec = self._vectorize_query(query)
        if np.linalg.norm(q_vec) == 0:
            return []

        # คำนวณ cosine similarity
        scores = np.dot(self.doc_vectors, q_vec)
        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < min_score:
                break

            doc = dict(self.documents[idx])
            doc["score"] = round(score, 4)
            results.append(doc)

            if len(results) >= top_k:
                break

        return results

    def format_for_prompt(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "ไม่พบข้อมูลระเบียบที่เกี่ยวข้อง"

        context_blocks = []
        for doc in results:
            block = (
                f"[{doc['citation']}]\n"
                f"หัวข้อ: {doc['title']}\n"
                f"เนื้อหา: {doc['content']}"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

