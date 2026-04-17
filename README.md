# 🏛️ Government Scheme NLP Extractor

An end-to-end NLP pipeline that scrapes Indian government policy documents from Wikipedia and uses **extractive Question-Answering** (via `deepset/roberta-base-squad2`) to extract citizen-centric insights — eligibility criteria, benefits, and objectives.

## Schemes Analyzed

| Scheme | Full Name |
|--------|-----------|
| **NREGA** | National Rural Employment Guarantee Act, 2005 |
| **PMUY** | Pradhan Mantri Ujjwala Yojana |

## Pipeline Stages

1. **Data Ingestion** — Scrapes Wikipedia pages using `BeautifulSoup`, extracts substantive `<p>` tags
2. **NLP Extraction** — Runs 3 targeted questions per scheme through RoBERTa-based extractive QA
3. **Quality Control** — Anti-hallucination gate filters answers below 0.01 confidence
4. **Output** — Structured Markdown table + CSV export

## Quick Start

```bash
# Install dependencies
pip install requests beautifulsoup4 pandas transformers torch

# Run the pipeline
python3 nlp_pipeline.py
```

## Output

Results are saved to `Citizen_Eligibility_Results.csv` and printed as a Markdown table.

## Model

- **Model:** [`deepset/roberta-base-squad2`](https://huggingface.co/deepset/roberta-base-squad2)
- **Task:** Extractive Question-Answering
- **Framework:** HuggingFace Transformers

## License

MIT
