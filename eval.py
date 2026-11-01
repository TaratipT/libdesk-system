import json
import os
import sys
from typing import List, Dict, Any, Set
from app.rag.vector_store import VectorStore

# ฟังก์ชันคำนวณ metric ตาม Lecture 8
def recall_at_k(ranked: List[str], relevant: Set[str], k: int) -> float:
    if not relevant:
        return 0.0
    topk = set(ranked[:k])
    return len(topk & relevant) / len(relevant)

def precision_at_k(ranked: List[str], relevant: Set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    topk = ranked[:k]
    hits = sum(1 for d in topk if d in relevant)
    return hits / k

def reciprocal_rank(ranked: List[str], relevant: Set[str]) -> float:
    for i, doc in enumerate(ranked, start=1):
        if doc in relevant:
            return 1.0 / i
    return 0.0

def evaluate(store: VectorStore, test_set: List[Dict[str, Any]], top_k: int, min_score: float) -> Dict[str, Any]:
    recalls = []
    precisions = []
    rrs = []
    
    out_of_scope_total = 0
    out_of_scope_rejected = 0

    for item in test_set:
        query = item["query"]
        expected = set(item.get("expected_rule_ids", []))
        category = item.get("category", "in-domain")

        hits = store.search(query=query, top_k=top_k, min_score=min_score)
        ranked = [doc["id"] for doc in hits]

        if category == "in-domain":
            r = recall_at_k(ranked, expected, top_k)
            p = precision_at_k(ranked, expected, top_k)
            rr = reciprocal_rank(ranked, expected)
            recalls.append(r)
            precisions.append(p)
            rrs.append(rr)
        else:
            out_of_scope_total += 1
            if len(ranked) == 0:
                out_of_scope_rejected += 1

    n_in = len(recalls)
    mean_recall = (sum(recalls) / n_in) if n_in else 0.0
    mean_precision = (sum(precisions) / n_in) if n_in else 0.0
    mrr = (sum(rrs) / n_in) if n_in else 0.0
    rejection_rate = (out_of_scope_rejected / out_of_scope_total) if out_of_scope_total else 0.0

    return {
        "top_k": top_k,
        "min_score": min_score,
        "recall_at_k": round(mean_recall * 100, 2),
        "precision_at_k": round(mean_precision * 100, 2),
        "mrr": round(mrr, 4),
        "rejection_rate": round(rejection_rate * 100, 2),
    }

def main():
    test_file = "data/eval_set.json"
    if not os.path.exists(test_file):
        print(f"Error: ไม่พบ {test_file}")
        sys.exit(1)

    with open(test_file, "r", encoding="utf-8") as f:
        test_set = json.load(f)

    store = VectorStore(data_path="data/library_rules.json")

    # Baseline: ไม่ตัด min_score floor (min_score=0.0)
    baseline = evaluate(store, test_set, top_k=3, min_score=0.0)

    # Tuned: ใช้ min_score=0.18 ตัด noise
    tuned = evaluate(store, test_set, top_k=3, min_score=0.18)

    print("=" * 60)
    print("   Retrieval Benchmark (Baseline vs. Tuned)")
    print(f"   จำนวนชุดทดสอบ: {len(test_set)} ข้อ")
    print("=" * 60)
    print(f"{'Metric':<25} | {'Baseline (score=0)':<18} | {'Tuned (score=0.18)':<18}")
    print("-" * 60)
    print(f"{'Recall @ 3 (%)':<25} | {baseline['recall_at_k']:<18.2f} | {tuned['recall_at_k']:<18.2f}")
    print(f"{'Precision @ 3 (%)':<25} | {baseline['precision_at_k']:<18.2f} | {tuned['precision_at_k']:<18.2f}")
    print(f"{'MRR':<25} | {baseline['mrr']:<18.4f} | {tuned['mrr']:<18.4f}")
    print(f"{'Rejection Rate (%)':<25} | {baseline['rejection_rate']:<18.2f} | {tuned['rejection_rate']:<18.2f}")
    print("-" * 60)
    print(f"สรุป: การตั้ง min_score=0.18 ช่วยตัดคำถามนอก scope ได้ {tuned['rejection_rate']}% (จากเดิม {baseline['rejection_rate']}%)")

    # บันทึกผลไว้ใช้อ้างอิงในรายงาน
    with open("data/eval_results.json", "w", encoding="utf-8") as f:
        json.dump({"baseline": baseline, "tuned": tuned}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

