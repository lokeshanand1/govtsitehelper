#!/usr/bin/env python3
"""
GovScheme Advisor — Recommendation Engine Metrics (Precision@5 & MRR)

Generates 20 diverse mock user profiles, defines ground-truth expected schemes,
passes each through the NLP recommendation engine, and computes:
  - Precision@5  (fraction of top-5 results that are relevant)
  - Mean Reciprocal Rank (MRR)

Results are saved to backend/metrics_recsys_results.txt
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from nlp.engine import NLPEngine
from nlp.trainer import load_model
from seed_data import SCHEMES


# ──────────────────────────────────────────────
# 20 DIVERSE MOCK USER PROFILES + GROUND TRUTH
# ──────────────────────────────────────────────

MOCK_PROFILES = [
    {
        "profile": {
            "gender": "male", "age": 35, "caste_category": "obc",
            "is_farmer": True, "annual_family_income": 80000,
            "state": "Uttar Pradesh", "area_type": "rural", "bpl_status": True
        },
        "expected": ["pm-kisan", "pmfby", "nrega", "ayushman-bharat", "free-ration"]
    },
    {
        "profile": {
            "gender": "female", "age": 20, "caste_category": "sc",
            "is_student": True, "annual_family_income": 150000,
            "state": "Bihar", "area_type": "urban", "bpl_status": False
        },
        "expected": ["nsp-post-matric", "skill-india", "beti-bachao", "pmjdy", "sukanya-samriddhi"]
    },
    {
        "profile": {
            "gender": "female", "age": 55, "caste_category": "general",
            "is_widow": True, "annual_family_income": 60000,
            "state": "Rajasthan", "area_type": "rural", "bpl_status": True
        },
        "expected": ["widow-pension", "ayushman-bharat", "free-ration", "ujjwala", "nrega"]
    },
    {
        "profile": {
            "gender": "male", "age": 65, "caste_category": "st",
            "annual_family_income": 50000, "bpl_status": True,
            "state": "Jharkhand", "area_type": "rural", "is_senior_citizen": True
        },
        "expected": ["old-age-pension", "ayushman-bharat", "free-ration", "nrega", "pmjdy"]
    },
    {
        "profile": {
            "gender": "female", "age": 22, "caste_category": "st",
            "is_student": True, "annual_family_income": 120000,
            "state": "Odisha", "area_type": "rural"
        },
        "expected": ["nsp-st-scholarship", "skill-india", "beti-bachao", "pmjdy", "ujjwala"]
    },
    {
        "profile": {
            "gender": "male", "age": 28, "caste_category": "general",
            "employment_status": "unemployed", "annual_family_income": 200000,
            "state": "Maharashtra", "area_type": "urban"
        },
        "expected": ["mudra-loan", "pmegp", "skill-india", "pmjdy", "pmsby"]
    },
    {
        "profile": {
            "gender": "female", "age": 25, "caste_category": "obc",
            "is_student": True, "annual_family_income": 90000,
            "state": "Tamil Nadu", "area_type": "urban", "bpl_status": True
        },
        "expected": ["obc-scholarship", "skill-india", "ujjwala", "ayushman-bharat", "free-ration"]
    },
    {
        "profile": {
            "gender": "male", "age": 45, "caste_category": "sc",
            "is_farmer": True, "annual_family_income": 70000,
            "state": "Madhya Pradesh", "area_type": "rural", "bpl_status": True
        },
        "expected": ["pm-kisan", "pmfby", "nrega", "ayushman-bharat", "free-ration"]
    },
    {
        "profile": {
            "gender": "female", "age": 30, "caste_category": "sc",
            "annual_family_income": 150000, "state": "Karnataka",
            "area_type": "urban", "employment_status": "self_employed"
        },
        "expected": ["standup-india", "mudra-loan", "pmegp", "maternity-benefit", "pmjdy"]
    },
    {
        "profile": {
            "gender": "male", "age": 19, "caste_category": "ews",
            "is_student": True, "annual_family_income": 200000,
            "state": "Delhi", "area_type": "urban"
        },
        "expected": ["skill-india", "pmjdy", "pmsby", "atal-pension", "mudra-loan"]
    },
    {
        "profile": {
            "gender": "female", "age": 26, "caste_category": "general",
            "annual_family_income": 400000, "state": "Gujarat",
            "area_type": "urban", "employment_status": "employed"
        },
        "expected": ["maternity-benefit", "pmjjby", "pmsby", "atal-pension", "sukanya-samriddhi"]
    },
    {
        "profile": {
            "gender": "male", "age": 40, "caste_category": "obc",
            "is_farmer": True, "annual_family_income": 100000,
            "state": "West Bengal", "area_type": "rural", "bpl_status": False
        },
        "expected": ["pm-kisan", "pmfby", "nrega", "pmsby", "atal-pension"]
    },
    {
        "profile": {
            "gender": "female", "age": 70, "caste_category": "sc",
            "is_widow": True, "bpl_status": True,
            "annual_family_income": 40000, "state": "Chhattisgarh", "area_type": "rural"
        },
        "expected": ["widow-pension", "old-age-pension", "ayushman-bharat", "free-ration", "ujjwala"]
    },
    {
        "profile": {
            "gender": "male", "age": 50, "caste_category": "general",
            "disability_status": True, "bpl_status": True,
            "annual_family_income": 55000, "state": "Bihar", "area_type": "rural"
        },
        "expected": ["disability-pension", "ayushman-bharat", "free-ration", "nrega", "pmjdy"]
    },
    {
        "profile": {
            "gender": "female", "age": 18, "caste_category": "st",
            "is_student": True, "annual_family_income": 180000,
            "state": "Assam", "area_type": "rural", "minority_status": True
        },
        "expected": ["nsp-st-scholarship", "minority-scholarship", "skill-india", "beti-bachao", "pmjdy"]
    },
    {
        "profile": {
            "gender": "male", "age": 30, "caste_category": "sc",
            "annual_family_income": 250000, "state": "Punjab",
            "area_type": "urban", "employment_status": "self_employed"
        },
        "expected": ["standup-india", "mudra-loan", "pmegp", "pmsby", "pmjjby"]
    },
    {
        "profile": {
            "gender": "female", "age": 35, "caste_category": "obc",
            "is_farmer": True, "annual_family_income": 95000,
            "state": "Rajasthan", "area_type": "rural", "bpl_status": True
        },
        "expected": ["pm-kisan", "pmfby", "ujjwala", "ayushman-bharat", "free-ration"]
    },
    {
        "profile": {
            "gender": "male", "age": 22, "caste_category": "general",
            "is_student": False, "annual_family_income": 350000,
            "state": "Haryana", "area_type": "urban"
        },
        "expected": ["skill-india", "mudra-loan", "pmegp", "pmjdy", "pmsby"]
    },
    {
        "profile": {
            "gender": "female", "age": 28, "caste_category": "sc",
            "annual_family_income": 80000, "bpl_status": True,
            "state": "Uttar Pradesh", "area_type": "rural"
        },
        "expected": ["ujjwala", "ayushman-bharat", "free-ration", "nrega", "standup-india"]
    },
    {
        "profile": {
            "gender": "male", "age": 55, "caste_category": "obc",
            "is_farmer": True, "annual_family_income": 120000,
            "state": "Madhya Pradesh", "area_type": "rural"
        },
        "expected": ["pm-kisan", "pmfby", "pmsby", "atal-pension", "nrega"]
    },
]


def precision_at_k(recommended_ids, relevant_ids, k=5):
    """Compute Precision@K."""
    top_k = recommended_ids[:k]
    hits = sum(1 for sid in top_k if sid in relevant_ids)
    return hits / k


def reciprocal_rank(recommended_ids, relevant_ids):
    """Compute Reciprocal Rank (1/rank of first relevant result)."""
    for i, sid in enumerate(recommended_ids):
        if sid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def main():
    print("=" * 70)
    print("RECOMMENDATION ENGINE METRICS — Precision@5 & MRR")
    print("=" * 70)

    # Initialize engine (standalone, no DB needed)
    engine = NLPEngine()
    engine.load_schemes(SCHEMES)

    total_p5 = 0.0
    total_rr = 0.0
    n = len(MOCK_PROFILES)

    details = []

    for idx, entry in enumerate(MOCK_PROFILES):
        profile = entry["profile"]
        expected = set(entry["expected"])

        results = engine.recommend(profile, top_k=20)
        rec_ids = [r["scheme_id"] for r in results]

        p5 = precision_at_k(rec_ids, expected, k=5)
        rr = reciprocal_rank(rec_ids, expected)
        total_p5 += p5
        total_rr += rr

        top5_names = [r["name"] for r in results[:5]]
        detail_line = (
            f"  Profile {idx+1:2d}: P@5={p5:.2f}  RR={rr:.4f}  "
            f"| gender={profile.get('gender','?')}, age={profile.get('age','?')}, "
            f"caste={profile.get('caste_category','?')}"
        )
        details.append(detail_line)
        print(detail_line)
        print(f"             Top-5: {', '.join(r['scheme_id'] for r in results[:5])}")
        print(f"             Expected: {', '.join(expected)}")
        print()

    avg_p5 = total_p5 / n
    mrr = total_rr / n

    print("  " + "─" * 60)
    print(f"  Average Precision@5:      {avg_p5:.4f}")
    print(f"  Mean Reciprocal Rank:     {mrr:.4f}")
    print(f"  Profiles Evaluated:       {n}")
    print("  " + "─" * 60)

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "metrics_recsys_results.txt")
    with open(out_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("RECOMMENDATION ENGINE METRICS — GovScheme Advisor\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Average Precision@5:    {avg_p5:.4f}\n")
        f.write(f"Mean Reciprocal Rank:   {mrr:.4f}\n")
        f.write(f"Profiles Evaluated:     {n}\n\n")
        f.write("Per-Profile Breakdown:\n")
        for line in details:
            f.write(line + "\n")
        f.write("\n")

    print(f"\n  ✅ RecSys metrics saved to: {out_path}")


if __name__ == "__main__":
    main()
