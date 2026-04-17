#!/usr/bin/env python3
"""
Civic Tech NLP Pipeline — Extractive QA on Indian Government Schemes
Model: deepset/roberta-base-squad2
Schemes: NREGA, PMUY
"""

import warnings
warnings.filterwarnings("ignore")

import requests
from bs4 import BeautifulSoup
import pandas as pd
from transformers import pipeline
import json
import os

# ──────────────────────────────────────────────
# STEP 1 — DATA INGESTION (WEB SCRAPING)
# ──────────────────────────────────────────────

URLS = {
    "NREGA": "https://en.wikipedia.org/wiki/National_Rural_Employment_Guarantee_Act,_2005",
    "PMUY": "https://en.wikipedia.org/wiki/Pradhan_Mantri_Ujjwala_Yojana",
}

HEADERS = {
    "User-Agent": "CivicTechNLPBot/1.0 (Educational Research)"
}

MIN_PARA_LEN = 50   # ignore tiny UI strings
TARGET_PARAS = 7     # first 5-7 substantive paragraphs

def scrape_context(url: str) -> str:
    """Scrape Wikipedia page and return concatenated substantive paragraphs."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    paragraphs = []
    for p in soup.select("div.mw-parser-output > p"):
        text = p.get_text(strip=True)
        if len(text) >= MIN_PARA_LEN:
            paragraphs.append(text)
        if len(paragraphs) >= TARGET_PARAS:
            break
    
    context = " ".join(paragraphs)
    return context

print("=" * 70)
print("STEP 1: DATA INGESTION — Scraping Wikipedia...")
print("=" * 70)

contexts = {}
for scheme, url in URLS.items():
    ctx = scrape_context(url)
    contexts[scheme] = ctx
    print(f"  [{scheme}] Scraped {len(ctx):,} characters from {url.split('/')[-1]}")

# ──────────────────────────────────────────────
# STEP 2 — NLP INFORMATION EXTRACTION
# ──────────────────────────────────────────────

MODEL_ID = "deepset/roberta-base-squad2"

QUESTIONS = [
    ("Eligibility", "Who is eligible for this scheme?"),
    ("Benefits",    "What is the main benefit or provision of this scheme?"),
    ("Objective",   "What is the primary goal?"),
]

CONFIDENCE_THRESHOLD = 0.01

print("\n" + "=" * 70)
print(f"STEP 2: LOADING MODEL — {MODEL_ID}")
print("=" * 70)

qa = pipeline("question-answering", model=MODEL_ID)
print("  Model loaded successfully.\n")

# ──────────────────────────────────────────────
# STEP 3 — RUN QA + QUALITY CONTROL
# ──────────────────────────────────────────────

print("=" * 70)
print("STEP 3: RUNNING EXTRACTIVE QA...")
print("=" * 70)

rows = []
for scheme, context in contexts.items():
    print(f"\n  ── {scheme} ──")
    for label, question in QUESTIONS:
        result = qa(question=question, context=context)
        raw_answer = result["answer"]
        score = result["score"]

        # Anti-hallucination gate
        if score < CONFIDENCE_THRESHOLD:
            answer = "Information not explicitly found."
        else:
            answer = raw_answer

        print(f"    Q: {question}")
        print(f"    A: {answer}  (score: {score:.4f})")

        rows.append({
            "Scheme": scheme,
            "Dimension": label,
            "Question": question,
            "Extracted_Answer": answer,
            "Confidence_Score": round(score, 4),
        })

# ──────────────────────────────────────────────
# STEP 4 — DATA FORMATTING & OUTPUT
# ──────────────────────────────────────────────

df = pd.DataFrame(rows)

# Save CSV
csv_path = os.path.join(os.path.dirname(__file__), "Citizen_Eligibility_Results.csv")
df.to_csv(csv_path, index=False)
print(f"\n{'=' * 70}")
print(f"STEP 4: CSV saved → {csv_path}")
print(f"{'=' * 70}")

# Print Markdown table
print("\n\n### FINAL RESULTS — Extractive QA Output\n")
print("| Scheme | Dimension | Extracted Answer | Confidence |")
print("|--------|-----------|------------------|------------|")
for _, r in df.iterrows():
    ans = r["Extracted_Answer"]
    if len(ans) > 120:
        ans = ans[:117] + "..."
    print(f"| {r['Scheme']} | {r['Dimension']} | {ans} | {r['Confidence_Score']:.4f} |")

# Also dump raw CSV string for easy copy
print("\n\n### RAW CSV\n")
print("```csv")
print(df.to_csv(index=False), end="")
print("```")
