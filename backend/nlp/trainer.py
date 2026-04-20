"""
GovScheme Advisor — Trainable NLP Classifier (trainer.py)

This module adds a REAL, PERSISTENT, trainable ML model alongside the existing
TF-IDF cosine-similarity engine. It works as follows:

1. **Synthetic Data Generation**: Since we have 25 government schemes but no real
   user history, we generate 15-20 synthetic user profile strings per scheme by
   permuting eligible demographic parameters (age, gender, income, caste, tags)
   within each scheme's eligibility constraints. This yields ~375-500 labeled
   training samples.

2. **Model Architecture**: A scikit-learn Pipeline with:
   - TfidfVectorizer (unigram + bigram, sublinear TF) — converts profile text
     to sparse TF-IDF feature vectors.
   - OneVsRestClassifier(LogisticRegression) — multi-label classifier that
     learns per-scheme probability boundaries in TF-IDF space.

3. **Persistence**: The trained pipeline is saved to disk as a .pkl file using
   joblib, so it survives server restarts without retraining.

4. **Inference**: predict_top_schemes() loads the model and returns the top-N
   scheme IDs ranked by predict_proba confidence.

NLP Approach:
- This is NOT a large language model. It's a lightweight, deterministic
  classifier that maps user demographic text → scheme label probabilities.
- The TF-IDF layer captures token/bigram importance across the training corpus.
- The logistic regression layer learns decision boundaries for each scheme class.
- predict_proba gives calibrated confidence scores usable as ranking boosts.
"""

import os
import json
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score
import joblib


# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "scheme_classifier.pkl")
META_PATH = os.path.join(MODEL_DIR, "model_meta.json")


# ──────────────────────────────────────────────
# SYNTHETIC DATA GENERATION
# ──────────────────────────────────────────────

# Fixed seed for reproducibility
RNG = np.random.RandomState(42)

# Demographic pools for permutation
_GENDERS = ["male", "female"]
_CASTES = ["sc", "st", "obc", "general", "ews"]
_STATES = [
    "uttar pradesh", "bihar", "rajasthan", "madhya pradesh",
    "maharashtra", "karnataka", "tamil nadu", "west bengal",
    "gujarat", "odisha", "jharkhand", "chhattisgarh", "delhi"
]
_AREA_TYPES = ["rural", "urban"]
_QUALIFICATIONS = [
    "10th pass", "12th pass", "graduate", "post graduate", "diploma"
]
_OCCUPATIONS = [
    "daily wage labourer", "farmer", "shop owner", "unemployed",
    "student", "homemaker", "auto driver", "construction worker"
]


def _profile_text(
    gender: str, age: int, caste: str, income: int,
    is_student: bool = False, is_farmer: bool = False,
    is_bpl: bool = False, is_widow: bool = False,
    is_senior: bool = False, is_disabled: bool = False,
    is_minority: bool = False, area: str = "rural",
    state: str = "uttar pradesh", qualification: str = "10th pass",
    occupation: str = "unemployed"
) -> str:
    """Build a natural-language user profile string from demographic parameters.

    This mirrors the NLPEngine.build_user_text() format so the classifier
    learns representations compatible with the existing TF-IDF space.
    """
    parts = [gender, f"{age} years old"]
    if age < 30:
        parts.append("youth")
    elif age >= 60:
        parts.append("senior citizen elderly")
    parts.append(caste)
    if is_bpl:
        parts.append("BPL below poverty line poor")
    if is_student:
        parts.append("student education scholarship")
    parts.append(qualification)
    if is_farmer:
        parts.append("farmer agriculture land crop")
    parts.append(occupation)
    parts.append(state)
    parts.append(area)
    if is_widow:
        parts.append("widow pension")
    if is_senior:
        parts.append("senior citizen pension old age")
    if is_disabled:
        parts.append("disability disabled handicapped")
    if is_minority:
        parts.append("minority")
    if income < 100000:
        parts.append("low income poor")
    elif income < 300000:
        parts.append("lower income")
    elif income < 800000:
        parts.append("middle income")
    return " ".join(parts).lower()


def generate_synthetic_samples(schemes: List[Dict]) -> Tuple[List[str], List[str]]:
    """Generate 15-20 synthetic user profile strings per scheme.

    For each scheme, we read its eligibility constraints and create profiles
    that WOULD be eligible — permuting age, income, gender, caste, tags etc.
    within the scheme's valid ranges.

    Returns:
        texts: List of profile strings
        labels: List of scheme_id strings (one per text)
    """
    texts = []
    labels = []

    for scheme in schemes:
        sid = scheme.get("scheme_id", scheme.get("name", "unknown"))
        elig = scheme.get("eligibility", {})
        if isinstance(elig, str):
            elig = {}

        # Determine valid parameter ranges from eligibility rules
        min_age = elig.get("min_age", 18)
        max_age = elig.get("max_age", 65)
        if max_age < min_age:
            max_age = min_age + 10

        genders = elig.get("gender") or _GENDERS
        castes = elig.get("caste_categories") or _CASTES
        max_income = elig.get("max_annual_income", 800000)
        bpl_required = elig.get("bpl_required", False)
        is_student_req = elig.get("is_student", False)
        is_farmer_req = elig.get("is_farmer", False)
        is_widow_req = elig.get("is_widow", False)
        is_senior_req = elig.get("is_senior_citizen", False)
        is_disabled_req = elig.get("is_disabled", False)
        is_minority_req = elig.get("is_minority", False)
        area_type = elig.get("area_type", "both")

        n_samples = RNG.randint(15, 21)  # 15-20 samples per scheme

        for _ in range(n_samples):
            age = int(RNG.randint(min_age, max(max_age, min_age + 1) + 1))
            gender = RNG.choice(genders).lower()
            caste = RNG.choice(castes).lower()

            # Income: random value below limit (or reasonable range)
            if max_income:
                income = int(RNG.randint(30000, min(max_income, 800000) + 1))
            else:
                income = int(RNG.randint(50000, 500001))

            area = area_type if area_type != "both" else RNG.choice(_AREA_TYPES)
            state = RNG.choice(_STATES)
            qualification = RNG.choice(_QUALIFICATIONS)
            occupation = RNG.choice(_OCCUPATIONS)

            # Override occupation for specific scheme types
            if is_farmer_req:
                occupation = "farmer"
            if is_student_req:
                occupation = "student"
                qualification = RNG.choice(["12th pass", "graduate", "post graduate", "diploma"])

            text = _profile_text(
                gender=gender,
                age=age,
                caste=caste,
                income=income,
                is_student=is_student_req,
                is_farmer=is_farmer_req,
                is_bpl=bpl_required or (income < 100000),
                is_widow=is_widow_req,
                is_senior=is_senior_req or (age >= 60),
                is_disabled=is_disabled_req,
                is_minority=is_minority_req,
                area=area,
                state=state,
                qualification=qualification,
                occupation=occupation,
            )
            texts.append(text)
            labels.append(sid)

    return texts, labels


# ──────────────────────────────────────────────
# TRAINING
# ──────────────────────────────────────────────

def train_and_save(schemes: List[Dict]) -> Dict:
    """Train the scheme classifier on synthetic data and save to disk.

    Pipeline architecture:
    1. TfidfVectorizer — extracts unigram/bigram TF-IDF features from profile text
    2. OneVsRestClassifier(LogisticRegression) — learns per-scheme boundaries

    Args:
        schemes: List of scheme dicts (from seed_data or MongoDB)

    Returns:
        Dict with training metrics: accuracy, f1_score, num_samples, trained_at
    """
    # Generate synthetic training data
    texts, labels = generate_synthetic_samples(schemes)

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    # Build pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000,
            stop_words="english"
        )),
        ('clf', OneVsRestClassifier(LogisticRegression(
            max_iter=1000,
            solver='lbfgs',
            C=1.0
        )))
    ])

    # Train
    pipeline.fit(texts, y)

    # Evaluate on training data (synthetic, so this is a sanity check)
    y_pred = pipeline.predict(texts)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, average='macro', zero_division=0)

    trained_at = datetime.now(timezone.utc).isoformat()

    # Save model + label encoder + metadata
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_bundle = {
        'pipeline': pipeline,
        'label_encoder': label_encoder,
        'scheme_ids': list(label_encoder.classes_),
    }
    joblib.dump(model_bundle, MODEL_PATH)

    meta = {
        'trained_at': trained_at,
        'num_samples': len(texts),
        'num_schemes': len(set(labels)),
        'accuracy': round(acc, 4),
        'f1_score_macro': round(f1, 4),
        'model_path': MODEL_PATH,
    }
    with open(META_PATH, 'w') as f:
        json.dump(meta, f, indent=2)

    return meta


# ──────────────────────────────────────────────
# LOADING
# ──────────────────────────────────────────────

def load_model() -> Optional[Dict]:
    """Load the trained classifier bundle from disk.

    Returns:
        Dict with keys 'pipeline', 'label_encoder', 'scheme_ids'
        or None if the pkl file doesn't exist.
    """
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        bundle = joblib.load(MODEL_PATH)
        return bundle
    except Exception as e:
        print(f"  ⚠️  Failed to load classifier model: {e}")
        return None


def load_model_meta() -> Optional[Dict]:
    """Load the model metadata (training metrics, timestamps).

    Returns:
        Dict with trained_at, num_samples, f1_score, etc.
        or None if metadata file doesn't exist.
    """
    if not os.path.exists(META_PATH):
        return None
    try:
        with open(META_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return None


# ──────────────────────────────────────────────
# PREDICTION
# ──────────────────────────────────────────────

def predict_top_schemes(profile_text: str, top_n: int = 5) -> List[str]:
    """Predict the top-N most relevant scheme IDs for a user profile text.

    Uses predict_proba to rank schemes by classifier confidence.

    Args:
        profile_text: Natural-language user profile string
        top_n: Number of top schemes to return

    Returns:
        List of scheme_id strings, ranked by descending probability
    """
    bundle = load_model()
    if bundle is None:
        return []

    pipeline = bundle['pipeline']
    label_encoder = bundle['label_encoder']

    try:
        probas = pipeline.predict_proba([profile_text.lower()])[0]
    except Exception:
        return []

    top_indices = np.argsort(probas)[::-1][:top_n]
    scheme_ids = label_encoder.inverse_transform(top_indices)
    return list(scheme_ids)


def get_scheme_probabilities(profile_text: str) -> Dict[str, float]:
    """Get classifier probability for ALL schemes given a profile text.

    Returns:
        Dict mapping scheme_id -> probability score [0, 1]
    """
    bundle = load_model()
    if bundle is None:
        return {}

    pipeline = bundle['pipeline']
    label_encoder = bundle['label_encoder']

    try:
        probas = pipeline.predict_proba([profile_text.lower()])[0]
    except Exception:
        return {}

    result = {}
    for idx, sid in enumerate(label_encoder.classes_):
        result[sid] = float(probas[idx])
    return result
