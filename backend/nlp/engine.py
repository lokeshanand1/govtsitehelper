"""
GovScheme Advisor — NLP Recommendation Engine
Uses rule-based filtering + semantic similarity for scheme matching.
Lightweight: uses sklearn TF-IDF instead of heavy transformer models for speed.
"""

import re
import math
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# ──────────────────────────────────────────────
# HINDI TRANSLATIONS (basic)
# ──────────────────────────────────────────────

HINDI_EXPLANATIONS = {
    "age": "आयु सीमा के अनुसार पात्र",
    "gender": "लिंग के आधार पर पात्र",
    "caste": "जाति वर्ग के आधार पर पात्र",
    "income": "आय सीमा के अनुसार पात्र",
    "bpl": "बीपीएल परिवार के लिए",
    "student": "छात्र/छात्रा के लिए",
    "farmer": "किसान के लिए",
    "state": "आपके राज्य में उपलब्ध",
    "disability": "विकलांगता के आधार पर पात्र",
    "widow": "विधवा महिला के लिए",
    "senior": "वरिष्ठ नागरिक के लिए",
}


class NLPEngine:
    """NLP-based scheme recommendation engine."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.scheme_vectors = None
        self.schemes = []
        self.scheme_texts = []

    def load_schemes(self, schemes: List[Dict]):
        """Index schemes for NLP search."""
        self.schemes = schemes
        self.scheme_texts = []
        for s in schemes:
            text = f"{s.get('name', '')} {s.get('description', '')} {s.get('eligibility_text', '')} {s.get('benefits', '')} {' '.join(s.get('tags', []))}"
            self.scheme_texts.append(text.lower())
        if self.scheme_texts:
            self.scheme_vectors = self.vectorizer.fit_transform(self.scheme_texts)

    # ──────────────────────────────────────────
    # RULE-BASED ELIGIBILITY CHECK
    # ──────────────────────────────────────────

    def check_eligibility(self, user_profile: Dict, scheme: Dict) -> tuple:
        """
        Check rule-based eligibility. Returns (score 0-100, reasons list).
        """
        elig = scheme.get("eligibility", {})
        if isinstance(elig, str):
            return 50, ["Cannot parse eligibility rules"]

        score = 0
        max_score = 0
        reasons = []
        reasons_hi = []

        # Age check
        if elig.get("min_age") or elig.get("max_age"):
            max_score += 20
            age = user_profile.get("age", 0)
            min_a = elig.get("min_age", 0)
            max_a = elig.get("max_age", 200)
            if age and min_a <= age <= max_a:
                score += 20
                reasons.append(f"Age {age} is within {min_a}-{max_a} years")
                reasons_hi.append(HINDI_EXPLANATIONS["age"])
            elif age:
                return 0, ["Age requirement not met"]

        # Gender check
        if elig.get("gender"):
            max_score += 15
            gender = user_profile.get("gender", "").lower()
            if gender in [g.lower() for g in elig["gender"]]:
                score += 15
                reasons.append(f"Gender ({gender}) matches requirement")
                reasons_hi.append(HINDI_EXPLANATIONS["gender"])
            elif gender:
                return 0, ["Gender requirement not met"]

        # Caste check
        if elig.get("caste_categories"):
            max_score += 15
            caste = user_profile.get("caste_category", "").lower()
            if caste in [c.lower() for c in elig["caste_categories"]]:
                score += 15
                reasons.append(f"Caste category ({caste.upper()}) is eligible")
                reasons_hi.append(HINDI_EXPLANATIONS["caste"])
            elif caste:
                return 0, ["Caste category not eligible"]

        # BPL check
        if elig.get("bpl_required") is True:
            max_score += 15
            if user_profile.get("bpl_status"):
                score += 15
                reasons.append("BPL status confirmed")
                reasons_hi.append(HINDI_EXPLANATIONS["bpl"])
            else:
                return 0, ["BPL status required"]

        # Income check
        if elig.get("max_annual_income"):
            max_score += 15
            income = user_profile.get("annual_family_income", 0)
            if income and income <= elig["max_annual_income"]:
                score += 15
                reasons.append(f"Income ₹{income:,} within limit of ₹{elig['max_annual_income']:,}")
                reasons_hi.append(HINDI_EXPLANATIONS["income"])
            elif income and income > elig["max_annual_income"]:
                return 0, ["Income exceeds maximum limit"]

        # State check
        if elig.get("states"):
            max_score += 10
            state = user_profile.get("state", "").lower()
            if state in [s.lower() for s in elig["states"]]:
                score += 10
                reasons.append(f"Available in {state.title()}")
                reasons_hi.append(HINDI_EXPLANATIONS["state"])
            elif state:
                return 0, ["Not available in your state"]

        # Area type
        if elig.get("area_type") and elig["area_type"] != "both":
            max_score += 10
            area = user_profile.get("area_type", "").lower()
            if area == elig["area_type"].lower():
                score += 10
                reasons.append(f"Available in {area} areas")
            elif area:
                return 0, [f"Only available in {elig['area_type']} areas"]

        # Student check
        if elig.get("is_student") is True:
            max_score += 10
            if user_profile.get("is_student"):
                score += 10
                reasons.append("Student status confirmed")
                reasons_hi.append(HINDI_EXPLANATIONS["student"])
            else:
                return 0, ["Must be a student"]

        # Farmer check
        if elig.get("is_farmer") is True:
            max_score += 10
            if user_profile.get("is_farmer"):
                score += 10
                reasons.append("Farmer status confirmed")
                reasons_hi.append(HINDI_EXPLANATIONS["farmer"])
            else:
                return 0, ["Must be a farmer"]

        # Disability check
        if elig.get("is_disabled") is True:
            max_score += 10
            if user_profile.get("disability_status"):
                score += 10
                reasons.append("Disability status confirmed")
                reasons_hi.append(HINDI_EXPLANATIONS["disability"])
            else:
                return 0, ["Disability required"]

        # Widow check
        if elig.get("is_widow") is True:
            max_score += 10
            if user_profile.get("is_widow"):
                score += 10
                reasons.append("Widow status confirmed")
                reasons_hi.append(HINDI_EXPLANATIONS["widow"])
            else:
                return 0, ["Must be a widow"]

        # Senior citizen check
        if elig.get("is_senior_citizen") is True:
            max_score += 10
            if user_profile.get("is_senior_citizen") or (user_profile.get("age", 0) >= 60):
                score += 10
                reasons.append("Senior citizen status confirmed")
                reasons_hi.append(HINDI_EXPLANATIONS["senior"])
            else:
                return 0, ["Must be a senior citizen"]

        # Minority check
        if elig.get("is_minority") is True:
            max_score += 10
            if user_profile.get("minority_status"):
                score += 10
                reasons.append("Minority status confirmed")
            else:
                return 0, ["Must belong to minority community"]

        # Calculate percentage
        if max_score == 0:
            return 70, ["Generally eligible — no specific restrictions"]

        pct = int((score / max_score) * 100)
        if not reasons:
            reasons = ["Eligible based on profile match"]

        return pct, reasons

    # ──────────────────────────────────────────
    # NLP SEMANTIC MATCHING
    # ──────────────────────────────────────────

    def build_user_text(self, profile: Dict) -> str:
        """Convert user profile to natural language for NLP matching."""
        parts = []
        if profile.get("gender"):
            parts.append(profile["gender"])
        if profile.get("age"):
            parts.append(f"{profile['age']} years old")
            if profile["age"] < 30:
                parts.append("youth")
            elif profile["age"] >= 60:
                parts.append("senior citizen elderly")
        if profile.get("caste_category"):
            parts.append(profile["caste_category"])
        if profile.get("bpl_status"):
            parts.append("BPL below poverty line poor")
        if profile.get("is_student"):
            parts.append("student education scholarship")
        if profile.get("highest_qualification"):
            parts.append(profile["highest_qualification"])
        if profile.get("is_farmer"):
            parts.append("farmer agriculture land crop")
        if profile.get("employment_status"):
            parts.append(profile["employment_status"])
        if profile.get("occupation"):
            parts.append(profile["occupation"])
        if profile.get("state"):
            parts.append(profile["state"])
        if profile.get("area_type"):
            parts.append(profile["area_type"])
        if profile.get("is_widow"):
            parts.append("widow pension")
        if profile.get("is_senior_citizen"):
            parts.append("senior citizen pension old age")
        if profile.get("disability_status"):
            parts.append("disability disabled handicapped")
        if profile.get("is_single_mother"):
            parts.append("single mother women")
        if profile.get("is_orphan"):
            parts.append("orphan")
        if profile.get("minority_status"):
            parts.append("minority")
        if profile.get("annual_family_income"):
            inc = profile["annual_family_income"]
            if inc < 100000:
                parts.append("low income poor")
            elif inc < 300000:
                parts.append("lower income")
            elif inc < 800000:
                parts.append("middle income")
        return " ".join(parts).lower()

    def semantic_search(self, query: str, top_k: int = 10) -> List[tuple]:
        """Search schemes by text query using TF-IDF similarity."""
        if self.scheme_vectors is None or not self.scheme_texts:
            return []
        query_vec = self.vectorizer.transform([query.lower()])
        scores = cosine_similarity(query_vec, self.scheme_vectors).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0.01:
                results.append((self.schemes[idx], float(scores[idx])))
        return results

    # ──────────────────────────────────────────
    # FULL RECOMMENDATION PIPELINE
    # ──────────────────────────────────────────

    def recommend(self, user_profile: Dict, top_k: int = 20) -> List[Dict]:
        """
        Full recommendation: rule-based filter + NLP ranking.
        Returns sorted list of recommendations.
        """
        user_text = self.build_user_text(user_profile)

        # Get NLP similarity scores
        nlp_scores = {}
        if self.scheme_vectors is not None:
            query_vec = self.vectorizer.transform([user_text])
            sims = cosine_similarity(query_vec, self.scheme_vectors).flatten()
            for i, scheme in enumerate(self.schemes):
                sid = scheme.get("scheme_id", str(i))
                nlp_scores[sid] = float(sims[i])

        results = []
        for scheme in self.schemes:
            sid = scheme.get("scheme_id", "")
            elig_score, reasons = self.check_eligibility(user_profile, scheme)

            if elig_score <= 0:
                continue

            nlp_score = nlp_scores.get(sid, 0.0)

            # Priority boost for special categories
            priority = 0
            cat = scheme.get("category", "")
            if user_profile.get("is_student") and cat == "scholarship":
                priority = 10
            if user_profile.get("is_farmer") and cat == "farmer":
                priority = 10
            if user_profile.get("is_widow") and cat in ["pension", "women"]:
                priority = 10
            if user_profile.get("is_senior_citizen") and cat == "pension":
                priority = 10

            total = (elig_score * 0.5) + (nlp_score * 100 * 0.35) + (priority * 0.15)

            results.append({
                "scheme_id": sid,
                "name": scheme.get("name", ""),
                "name_hindi": scheme.get("name_hindi", ""),
                "category": cat,
                "description": scheme.get("description", ""),
                "eligibility_score": round(elig_score, 1),
                "nlp_relevance_score": round(nlp_score * 100, 1),
                "total_score": round(total, 1),
                "why_eligible": "; ".join(reasons),
                "benefits": scheme.get("benefits", ""),
                "how_to_apply": scheme.get("how_to_apply", ""),
                "documents_required": scheme.get("documents_required", []),
                "apply_link": scheme.get("apply_link", ""),
                "official_website": scheme.get("official_website", ""),
                "state": scheme.get("state", "All India"),
                "eligibility_text": scheme.get("eligibility_text", ""),
            })

        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results[:top_k]

    # ──────────────────────────────────────────
    # SIMPLIFY TEXT (Auto Explanation)
    # ──────────────────────────────────────────

    def simplify_text(self, text: str) -> str:
        """Convert government/legal language to simple language."""
        replacements = {
            r"\bbeneficiary\b": "person who gets the benefit",
            r"\bdomicile\b": "permanent resident",
            r"\bper annum\b": "per year",
            r"\bsanctioned\b": "approved",
            r"\bdisbursement\b": "payment",
            r"\bsubsidy\b": "financial help from government",
            r"\bstipend\b": "monthly payment",
            r"\breimbursement\b": "money given back",
            r"\bcollateral\b": "security/guarantee",
            r"\bmoratorium\b": "grace period before repayment starts",
            r"\bempaneled\b": "registered/approved",
            r"\bnotified\b": "officially listed",
            r"\bSECC\b": "Socio Economic Caste Census",
            r"\bAAY\b": "Antyodaya Anna Yojana (poorest of poor)",
            r"\bPDS\b": "Public Distribution System (ration shop)",
            r"\bBPL\b": "Below Poverty Line",
            r"\bAPL\b": "Above Poverty Line",
            r"\bCSC\b": "Common Service Centre",
            r"\bLPG\b": "cooking gas",
            r"\bNBFC\b": "Non-Banking Financial Company",
            r"\bMFI\b": "Micro Finance Institution",
        }
        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result


# Singleton instance
nlp_engine = NLPEngine()
