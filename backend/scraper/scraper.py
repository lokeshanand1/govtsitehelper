"""
GovScheme Advisor — Enhanced Web Scraper
Scrapes government schemes from Wikipedia, individual scheme pages, and
uses NLP-based classification to auto-categorize and structure schemes
for the recommendation engine.

Sources:
  1. Wikipedia "List of government schemes in India" → 200+ scheme names & links
  2. Individual Wikipedia scheme pages → descriptions, eligibility, benefits
  3. Auto-classification via keyword analysis → category, tags, eligibility rules
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import time
import hashlib
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# ──────────────────────────────────────────────
# CATEGORY CLASSIFICATION KEYWORDS
# ──────────────────────────────────────────────

CATEGORY_KEYWORDS = {
    "scholarship": ["scholarship", "fellowship", "stipend", "education grant",
                     "tuition", "post matric", "pre matric", "merit"],
    "pension": ["pension", "old age", "social security pension", "widow pension",
                "disability pension", "retirement"],
    "women": ["women", "girl child", "maternity", "pregnant", "lactating",
              "beti", "mahila", "nari", "sukanya", "ujjwala"],
    "farmer": ["farmer", "agriculture", "kisan", "crop", "irrigation",
               "farming", "krishi", "fasal", "land holding", "mgnrega rural"],
    "employment": ["employment", "job", "skill", "training", "rozgar",
                   "kaushal", "apprentice", "placement", "nrega", "mgnrega"],
    "health": ["health", "medical", "hospital", "ayushman", "insurance cover",
               "treatment", "disease", "aarogya", "swasthya", "janani"],
    "housing": ["housing", "awas", "home loan", "shelter", "pucca house",
                "affordable housing", "pradhan mantri awas"],
    "startup": ["startup", "entrepreneur", "mudra", "loan", "msme",
                "business", "enterprise", "stand up", "self employment"],
    "social_security": ["ration", "food", "pds", "public distribution",
                        "jan dhan", "financial inclusion", "bank account",
                        "direct benefit", "anna"],
    "insurance": ["insurance", "bima", "suraksha", "jeevan jyoti",
                  "life cover", "accident cover", "premium"],
    "skill_development": ["skill", "vocational", "training program",
                          "certification", "kaushal vikas", "apprenticeship"],
}

# Keywords that help infer eligibility rules from text
ELIGIBILITY_KEYWORDS = {
    "is_farmer": ["farmer", "agriculture", "cultivator", "land holding", "kisan"],
    "is_student": ["student", "studying", "enrolled", "scholarship",
                   "post matric", "education"],
    "is_disabled": ["disabled", "disability", "handicapped", "divyang",
                    "physical disability", "mental disability"],
    "is_widow": ["widow", "widowed"],
    "is_senior_citizen": ["senior citizen", "old age", "elderly",
                          "above 60", "aged 60"],
    "bpl_required": ["bpl", "below poverty line", "poor families",
                     "economically weaker", "ews"],
    "is_minority": ["minority", "minority community"],
}

GENDER_KEYWORDS = {
    "female": ["women", "girl", "female", "mahila", "beti", "mother",
               "pregnant", "lactating", "widow"],
    "male": ["male only"],
}


# ──────────────────────────────────────────────
# WIKIPEDIA SCRAPER
# ──────────────────────────────────────────────

def scrape_wikipedia_scheme_list() -> List[Dict]:
    """Scrape the Wikipedia 'List of government schemes in India' page.
    Returns a list of dicts with scheme name and Wikipedia URL.
    """
    url = "https://en.wikipedia.org/wiki/List_of_government_schemes_in_India"
    schemes = []
    seen_slugs = set()

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the main content area
        content = soup.select_one("#mw-content-text .mw-parser-output")
        if not content:
            print("  ⚠️  Could not find content on Wikipedia list page")
            return schemes

        # Extract all linked schemes from lists and tables
        for link in content.select("a[href^='/wiki/']"):
            href = link.get("href", "")
            name = link.get_text(strip=True)
            slug = href.replace("/wiki/", "")

            # Skip non-scheme pages
            skip_prefixes = ["Category:", "File:", "Template:", "Help:",
                             "Wikipedia:", "Special:", "Portal:", "Talk:",
                             "List_of", "Index_of"]
            if any(slug.startswith(p) for p in skip_prefixes):
                continue

            # Skip very short names, citations, and generic terms
            if len(name) < 4 or name.startswith("[") or name.isdigit():
                continue

            # Skip generic Wikipedia terms
            generic = {"India", "Government", "Ministry", "Department",
                       "State", "Central", "National", "Rural", "Urban",
                       "Agriculture", "Education", "Health", "Finance",
                       "Electrification", "Irrigation", "Infrastructure"}
            if name in generic:
                continue

            # Deduplicate by slug
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            schemes.append({
                "name": name,
                "wiki_slug": slug,
                "wiki_url": f"https://en.wikipedia.org/wiki/{slug}",
            })

        print(f"  📋 Found {len(schemes)} scheme links on Wikipedia list page")

    except Exception as e:
        print(f"  ⚠️  Error scraping Wikipedia list: {e}")

    return schemes


def scrape_wikipedia_scheme_detail(wiki_url: str, scheme_name: str) -> Dict:
    """Scrape a single Wikipedia scheme page for description and details."""
    try:
        resp = requests.get(wiki_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        content = soup.select_one("#mw-content-text .mw-parser-output")
        if not content:
            return {}

        # Extract paragraphs (skip very short ones and citation-only lines)
        paragraphs = []
        for p in content.select(":scope > p"):
            text = p.get_text(strip=True)
            # Remove citation brackets like [1], [2]
            text = re.sub(r"\[\d+\]", "", text).strip()
            if len(text) >= 40:
                paragraphs.append(text)
            if len(paragraphs) >= 8:
                break

        if not paragraphs:
            return {}

        description = paragraphs[0][:500]
        full_text = " ".join(paragraphs)

        # Try to extract eligibility from text
        eligibility_text = ""
        benefits_text = ""
        for p in paragraphs:
            lower = p.lower()
            if any(kw in lower for kw in ["eligible", "eligibility",
                                           "beneficiar", "target group",
                                           "who can", "applicable to"]):
                eligibility_text = p[:500]
            if any(kw in lower for kw in ["benefit", "provides", "offers",
                                           "financial assistance", "subsidy",
                                           "grant", "coverage"]):
                if not benefits_text:
                    benefits_text = p[:500]

        if not eligibility_text and len(paragraphs) > 1:
            eligibility_text = paragraphs[1][:500]
        if not benefits_text and len(paragraphs) > 2:
            benefits_text = paragraphs[2][:400]

        # Extract infobox data if available
        ministry = ""
        state = "All India"
        infobox = content.select_one("table.infobox, table.vcard")
        if infobox:
            for row in infobox.select("tr"):
                header = row.select_one("th")
                cell = row.select_one("td")
                if header and cell:
                    h_text = header.get_text(strip=True).lower()
                    c_text = cell.get_text(strip=True)
                    if "ministr" in h_text or "department" in h_text:
                        ministry = c_text[:100]
                    if "state" in h_text or "region" in h_text:
                        state = c_text[:100]

        return {
            "name": scheme_name,
            "description": description,
            "eligibility_text": eligibility_text,
            "benefits": benefits_text,
            "ministry": ministry,
            "state": state,
            "full_text": full_text,
            "source_url": wiki_url,
            "source": "wikipedia",
        }

    except Exception as e:
        return {}


# ──────────────────────────────────────────────
# NLP AUTO-CLASSIFICATION
# ──────────────────────────────────────────────

def classify_category(text: str) -> str:
    """Auto-classify a scheme into a category based on keyword analysis."""
    lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return "other"


def extract_eligibility_rules(text: str) -> Dict:
    """Extract structured eligibility rules from free text using keywords."""
    lower = text.lower()
    elig = {}

    for rule_key, keywords in ELIGIBILITY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            elig[rule_key] = True

    # Gender detection
    female_score = sum(1 for kw in GENDER_KEYWORDS["female"] if kw in lower)
    male_score = sum(1 for kw in GENDER_KEYWORDS["male"] if kw in lower)
    if female_score > 0 and male_score == 0:
        elig["gender"] = ["female"]

    # Age extraction
    age_patterns = [
        r"aged?\s+(\d{1,2})\s*[-–to]+\s*(\d{1,2})",
        r"(\d{1,2})\s*to\s*(\d{1,2})\s*years",
        r"above\s+(\d{1,2})\s*years",
        r"below\s+(\d{1,2})\s*years",
        r"minimum\s+age[:\s]+(\d{1,2})",
    ]
    for pattern in age_patterns:
        match = re.search(pattern, lower)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                elig["min_age"] = int(groups[0])
                elig["max_age"] = int(groups[1])
            elif "above" in pattern or "minimum" in pattern:
                elig["min_age"] = int(groups[0])
            elif "below" in pattern:
                elig["max_age"] = int(groups[0])
            break

    # Income extraction
    income_patterns = [
        r"income[^.]*(?:up\s*to|not\s+exceed|below|less\s+than|under)[^.]*?(?:rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)",
        r"income[^.]*(?:up\s*to|not\s+exceed|below|less\s+than|under)[^.]*?(?:rs\.?|₹)\s*([\d,]+)",
    ]
    for pattern in income_patterns:
        match = re.search(pattern, lower)
        if match:
            amt_str = match.group(1).replace(",", "")
            try:
                amt = float(amt_str)
                if "lakh" in lower[match.start():match.end() + 20]:
                    amt *= 100000
                if amt > 1000:  # Sanity check
                    elig["max_annual_income"] = int(amt)
            except ValueError:
                pass
            break

    return elig


def extract_tags(text: str, category: str) -> List[str]:
    """Generate tags from scheme text."""
    lower = text.lower()
    tags = [category] if category != "other" else []

    tag_keywords = {
        "farmer": ["farmer", "agriculture", "kisan", "crop"],
        "student": ["student", "education", "school", "college"],
        "women": ["women", "girl", "female", "mahila"],
        "bpl": ["bpl", "below poverty", "poor"],
        "rural": ["rural", "village", "gram"],
        "urban": ["urban", "city"],
        "sc": ["scheduled caste", " sc "],
        "st": ["scheduled tribe", " st "],
        "obc": [" obc ", "backward class"],
        "minority": ["minority"],
        "disability": ["disabled", "disability", "divyang"],
        "pension": ["pension"],
        "insurance": ["insurance", "bima"],
        "loan": ["loan", "credit", "finance"],
        "subsidy": ["subsidy", "grant"],
        "housing": ["housing", "awas", "home"],
        "health": ["health", "medical", "hospital"],
        "skill": ["skill", "training", "vocational"],
        "employment": ["employment", "job", "rozgar"],
        "food": ["food", "ration", "nutrition"],
        "scholarship": ["scholarship", "fellowship"],
        "startup": ["startup", "entrepreneur", "enterprise"],
        "youth": ["youth", "young"],
        "senior_citizen": ["senior", "old age", "elderly"],
        "widow": ["widow"],
        "maternity": ["maternity", "pregnant", "lactating"],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in lower for kw in keywords) and tag not in tags:
            tags.append(tag)

    return tags[:8]  # Cap at 8 tags


def generate_scheme_id(name: str) -> str:
    """Generate a URL-friendly scheme ID from the name."""
    # Clean and normalize
    slug = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = slug[:50]  # Max length
    # Add hash suffix for uniqueness
    suffix = hashlib.md5(name.encode()).hexdigest()[:4]
    return f"{slug}-{suffix}"


# ──────────────────────────────────────────────
# FULL SCRAPE PIPELINE
# ──────────────────────────────────────────────

def build_scheme_document(raw: Dict) -> Optional[Dict]:
    """Convert raw scraped data into the MongoDB scheme document format
    matching the existing seed_data.py structure exactly.
    """
    name = raw.get("name", "").strip()
    description = raw.get("description", "").strip()

    if not name or not description or len(description) < 30:
        return None

    full_text = f"{name} {description} {raw.get('eligibility_text', '')} {raw.get('benefits', '')}"

    category = classify_category(full_text)
    elig_rules = extract_eligibility_rules(full_text)
    tags = extract_tags(full_text, category)
    scheme_id = generate_scheme_id(name)

    return {
        "scheme_id": scheme_id,
        "name": name,
        "name_hindi": "",
        "description": description,
        "description_hindi": "",
        "category": category,
        "ministry": raw.get("ministry", ""),
        "eligibility_text": raw.get("eligibility_text", ""),
        "eligibility": elig_rules,
        "benefits": raw.get("benefits", ""),
        "benefits_hindi": "",
        "documents_required": [],
        "how_to_apply": "",
        "apply_link": "",
        "official_website": raw.get("source_url", ""),
        "state": raw.get("state", "All India"),
        "last_date": "",
        "tags": tags,
        "source_url": raw.get("source_url", ""),
        "source": raw.get("source", "scraped"),
    }


def run_full_scrape(max_detail_pages: int = 200,
                    delay: float = 0.5) -> List[Dict]:
    """Run the full scraping pipeline:
    1. Get scheme names from Wikipedia list
    2. Fetch details for each scheme
    3. Auto-classify and structure for MongoDB

    Args:
        max_detail_pages: Max number of individual Wikipedia pages to scrape
        delay: Seconds to wait between requests (be polite to Wikipedia)

    Returns:
        List of structured scheme documents ready for MongoDB insertion
    """
    print("  🔄 Starting enhanced scheme scraper...")
    print()

    # Step 1: Get scheme list from Wikipedia
    scheme_refs = scrape_wikipedia_scheme_list()

    # Step 2: Fetch details for each scheme
    print(f"  📥 Fetching details for up to {min(max_detail_pages, len(scheme_refs))} schemes...")
    raw_schemes = []
    fetched = 0

    for ref in scheme_refs[:max_detail_pages]:
        detail = scrape_wikipedia_scheme_detail(ref["wiki_url"], ref["name"])
        if detail and detail.get("description"):
            raw_schemes.append(detail)
            fetched += 1
            if fetched % 20 == 0:
                print(f"    ... fetched {fetched} scheme details")
        time.sleep(delay)

    print(f"  ✅ Fetched details for {len(raw_schemes)} schemes")

    # Step 3: Build structured documents
    print("  🏗️  Building structured scheme documents...")
    structured = []
    for raw in raw_schemes:
        doc = build_scheme_document(raw)
        if doc:
            structured.append(doc)

    print(f"  ✅ Built {len(structured)} structured scheme documents")
    print()

    # Print category breakdown
    from collections import Counter
    cats = Counter(s["category"] for s in structured)
    print("  📊 Category breakdown:")
    for cat, count in cats.most_common():
        print(f"     {cat:20s}: {count}")
    print()

    return structured


def run_quick_scrape() -> List[Dict]:
    """Quick scrape — fetches just the list (no detail pages).
    Uses scheme names + basic Wikipedia summaries.
    Good for testing.
    """
    print("  🔄 Running quick scrape (list only, no detail pages)...")
    refs = scrape_wikipedia_scheme_list()
    results = []
    for ref in refs:
        doc = {
            "scheme_id": generate_scheme_id(ref["name"]),
            "name": ref["name"],
            "name_hindi": "",
            "description": f"Government scheme: {ref['name']}",
            "category": classify_category(ref["name"]),
            "eligibility_text": "",
            "eligibility": {},
            "benefits": "",
            "documents_required": [],
            "how_to_apply": "",
            "apply_link": "",
            "official_website": ref.get("wiki_url", ""),
            "state": "All India",
            "tags": extract_tags(ref["name"], classify_category(ref["name"])),
            "source_url": ref.get("wiki_url", ""),
            "source": "wikipedia_list",
        }
        results.append(doc)
    return results


# ──────────────────────────────────────────────
# CLI INTERFACE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GovScheme Scraper")
    parser.add_argument("--quick", action="store_true",
                        help="Quick scrape (names only, no detail pages)")
    parser.add_argument("--max-pages", type=int, default=200,
                        help="Max detail pages to fetch (default: 200)")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay between requests in seconds (default: 0.5)")
    parser.add_argument("--output", type=str, default=None,
                        help="Save results to JSON file")
    args = parser.parse_args()

    if args.quick:
        results = run_quick_scrape()
    else:
        results = run_full_scrape(
            max_detail_pages=args.max_pages,
            delay=args.delay,
        )

    print(f"\n  📦 Total schemes scraped: {len(results)}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  💾 Saved to {args.output}")
    else:
        # Print first 5 as sample
        for s in results[:5]:
            print(f"\n  --- {s['name']} ---")
            print(f"  Category: {s['category']}")
            print(f"  Description: {s['description'][:100]}...")
            if s.get("eligibility"):
                print(f"  Eligibility rules: {s['eligibility']}")
            print(f"  Tags: {s['tags']}")
