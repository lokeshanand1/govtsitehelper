"""
GovScheme Advisor — Web Scraper
Scrapes government scheme data from official portals.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import time


HEADERS = {
    "User-Agent": "GovSchemeAdvisor/1.0 (Educational Research Bot)"
}


def scrape_myscheme_gov() -> List[Dict]:
    """Scrape scheme listings from myscheme.gov.in search results."""
    schemes = []
    base_url = "https://www.myscheme.gov.in"
    
    try:
        resp = requests.get(f"{base_url}/find-scheme", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        cards = soup.select(".scheme-card, .card, article")
        for card in cards[:50]:
            title_el = card.select_one("h2, h3, .title, .scheme-name")
            desc_el = card.select_one("p, .description, .scheme-desc")
            link_el = card.select_one("a[href]")
            
            if title_el:
                scheme = {
                    "name": title_el.get_text(strip=True),
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                    "source_url": base_url + link_el["href"] if link_el and link_el.get("href", "").startswith("/") else "",
                    "source": "myscheme.gov.in"
                }
                schemes.append(scheme)
        
    except Exception as e:
        print(f"  ⚠️  Scraper error (myscheme.gov.in): {e}")
    
    return schemes


def scrape_scholarship_portal() -> List[Dict]:
    """Scrape from National Scholarship Portal."""
    schemes = []
    
    try:
        resp = requests.get(
            "https://scholarships.gov.in/public/schemeList",
            headers=HEADERS, timeout=30
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        rows = soup.select("table tr, .scheme-item, li")
        for row in rows[:30]:
            text = row.get_text(strip=True)
            if len(text) > 20:
                schemes.append({
                    "name": text[:200],
                    "category": "scholarship",
                    "source": "scholarships.gov.in"
                })
    except Exception as e:
        print(f"  ⚠️  Scraper error (scholarships.gov.in): {e}")
    
    return schemes


def scrape_wikipedia_scheme(url: str, scheme_name: str) -> Dict:
    """Scrape scheme details from Wikipedia page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        paragraphs = []
        for p in soup.select("div.mw-parser-output > p"):
            text = p.get_text(strip=True)
            if len(text) >= 50:
                paragraphs.append(text)
            if len(paragraphs) >= 5:
                break
        
        description = " ".join(paragraphs[:2]) if paragraphs else ""
        full_text = " ".join(paragraphs)
        
        # Extract eligibility from text
        eligibility = ""
        for p in paragraphs:
            lower = p.lower()
            if any(kw in lower for kw in ["eligible", "eligibility", "beneficiar", "target"]):
                eligibility = p
                break
        
        return {
            "name": scheme_name,
            "description": description[:500],
            "eligibility_text": eligibility[:500],
            "full_text": full_text,
            "source_url": url,
            "source": "wikipedia"
        }
    except Exception as e:
        print(f"  ⚠️  Scraper error ({url}): {e}")
        return {}


def run_full_scrape() -> List[Dict]:
    """Run all scrapers and return combined results."""
    print("  🔄 Starting scheme scraper...")
    all_schemes = []
    
    # Wikipedia schemes
    wiki_schemes = {
        "MGNREGA": "https://en.wikipedia.org/wiki/National_Rural_Employment_Guarantee_Act,_2005",
        "PM Ujjwala Yojana": "https://en.wikipedia.org/wiki/Pradhan_Mantri_Ujjwala_Yojana",
        "Ayushman Bharat": "https://en.wikipedia.org/wiki/Ayushman_Bharat_Yojana",
        "PM-KISAN": "https://en.wikipedia.org/wiki/PM-KISAN",
        "Beti Bachao Beti Padhao": "https://en.wikipedia.org/wiki/Beti_Bachao,_Beti_Padhao_Yojana",
    }
    
    for name, url in wiki_schemes.items():
        result = scrape_wikipedia_scheme(url, name)
        if result:
            all_schemes.append(result)
        time.sleep(1)
    
    print(f"  ✅ Scraped {len(all_schemes)} schemes total")
    return all_schemes
