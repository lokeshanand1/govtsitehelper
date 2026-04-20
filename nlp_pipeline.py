#!/usr/bin/env python3
"""
GovScheme Advisor — NLP Classifier CLI Pipeline

A standalone command-line tool for training, evaluating, and running
predictions with the scheme classifier model — independently of the
FastAPI server.

Usage:
    python nlp_pipeline.py --train      Train the classifier and save to disk
    python nlp_pipeline.py --evaluate   Run 5-fold cross-validation on synthetic data
    python nlp_pipeline.py --predict "female 24 OBC student income 1 lakh"

NLP Approach:
    - Generates synthetic user profile strings from 25 real scheme eligibility rules
    - Trains a TF-IDF (unigram+bigram) → OneVsRest Logistic Regression pipeline
    - predict_proba ranks schemes by classifier confidence
    - Model is saved as a joblib .pkl for hot-loading by the FastAPI backend
"""

import argparse
import sys
import os
import warnings
warnings.filterwarnings("ignore")

# Add backend to path so we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from nlp.trainer import (
    train_and_save,
    load_model,
    load_model_meta,
    predict_top_schemes,
    generate_synthetic_samples,
    MODEL_PATH,
)
from seed_data import SCHEMES


def cmd_train():
    """Train the scheme classifier on synthetic data derived from seed schemes."""
    print("=" * 70)
    print("TRAINING NLP SCHEME CLASSIFIER")
    print("=" * 70)
    print(f"  Schemes: {len(SCHEMES)}")
    print(f"  Model output: {MODEL_PATH}")
    print()

    metrics = train_and_save(SCHEMES)

    print("  Training complete!\n")
    print("  ┌──────────────────────────────────────────┐")
    print(f"  │  Samples:    {metrics['num_samples']:<28} │")
    print(f"  │  Schemes:    {metrics['num_schemes']:<28} │")
    print(f"  │  Accuracy:   {metrics['accuracy']:<28} │")
    print(f"  │  F1 (macro): {metrics['f1_score_macro']:<28} │")
    print(f"  │  Trained at: {metrics['trained_at'][:19]:<28} │")
    print(f"  │  Model path: {os.path.basename(MODEL_PATH):<28} │")
    print("  └──────────────────────────────────────────┘")


def cmd_evaluate():
    """Run 5-fold cross-validation on the synthetic training data."""
    from sklearn.model_selection import cross_val_score
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import LabelEncoder
    import numpy as np

    print("=" * 70)
    print("5-FOLD CROSS-VALIDATION ON SYNTHETIC DATA")
    print("=" * 70)

    texts, labels = generate_synthetic_samples(SCHEMES)
    le = LabelEncoder()
    y = le.fit_transform(labels)

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

    print(f"  Total samples: {len(texts)}")
    print(f"  Unique labels: {len(set(labels))}")
    print()

    # Accuracy CV
    acc_scores = cross_val_score(pipeline, texts, y, cv=5, scoring='accuracy')
    # F1 CV
    f1_scores = cross_val_score(pipeline, texts, y, cv=5, scoring='f1_macro')

    print("  ┌─────────┬───────────┬──────────┐")
    print("  │  Fold   │ Accuracy  │ F1 Macro │")
    print("  ├─────────┼───────────┼──────────┤")
    for i in range(5):
        print(f"  │  Fold {i+1} │  {acc_scores[i]:.4f}   │  {f1_scores[i]:.4f}  │")
    print("  ├─────────┼───────────┼──────────┤")
    print(f"  │  Mean   │  {acc_scores.mean():.4f}   │  {f1_scores.mean():.4f}  │")
    print(f"  │  Std    │  {acc_scores.std():.4f}   │  {f1_scores.std():.4f}  │")
    print("  └─────────┴───────────┴──────────┘")


def cmd_predict(profile_text: str):
    """Predict top 5 schemes for a given user profile text."""
    print("=" * 70)
    print("SCHEME PREDICTION")
    print("=" * 70)
    print(f"  Profile: \"{profile_text}\"")
    print()

    bundle = load_model()
    if bundle is None:
        print("  ❌ No trained model found! Run `python nlp_pipeline.py --train` first.")
        sys.exit(1)

    scheme_ids = predict_top_schemes(profile_text, top_n=5)

    # Build a lookup for scheme names
    name_map = {s["scheme_id"]: s["name"] for s in SCHEMES}

    print("  ┌─────┬──────────────────────────────────────────────────────────┐")
    print("  │ Rank│ Predicted Scheme                                        │")
    print("  ├─────┼──────────────────────────────────────────────────────────┤")
    for i, sid in enumerate(scheme_ids):
        name = name_map.get(sid, sid)
        print(f"  │  {i+1}  │ {name:<56} │")
    print("  └─────┴──────────────────────────────────────────────────────────┘")

    # Also show probabilities
    from nlp.trainer import get_scheme_probabilities
    probas = get_scheme_probabilities(profile_text)
    sorted_probas = sorted(probas.items(), key=lambda x: x[1], reverse=True)[:5]

    print()
    print("  Confidence scores:")
    for sid, prob in sorted_probas:
        name = name_map.get(sid, sid)
        bar = "█" * int(prob * 40)
        print(f"    {name[:40]:<40}  {prob:.4f}  {bar}")


def main():
    parser = argparse.ArgumentParser(
        description="GovScheme Advisor — NLP Classifier CLI Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nlp_pipeline.py --train
  python nlp_pipeline.py --evaluate
  python nlp_pipeline.py --predict "female 24 OBC student income 1 lakh"
        """
    )
    parser.add_argument(
        "--train", action="store_true",
        help="Train the classifier on synthetic scheme data and save to disk"
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run 5-fold cross-validation on synthetic training data"
    )
    parser.add_argument(
        "--predict", type=str, metavar="PROFILE",
        help="Predict top 5 schemes for a user profile text string"
    )

    args = parser.parse_args()

    if not any([args.train, args.evaluate, args.predict]):
        parser.print_help()
        sys.exit(0)

    if args.train:
        cmd_train()
    if args.evaluate:
        cmd_evaluate()
    if args.predict:
        cmd_predict(args.predict)


if __name__ == "__main__":
    main()
