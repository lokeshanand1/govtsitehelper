# 🏛️ GovScheme Advisor - NLP Recommendation Chatbot

GovScheme Advisor is a complete full-stack web application that uses Natural Language Processing to match Indian citizens with government schemes they are eligible for. Instead of a standard chat interface, users fill out a structured form (grid layout) with their details, and the backend engine calculates eligibility using a hybrid approach.

## 🚀 Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, React Router DOM, Lucide Icons.
- **Backend**: Python FastAPI.
- **Database**: MongoDB (via Motor async driver).
- **NLP Engine**: `scikit-learn` (TF-IDF Vectorization & Cosine Similarity) + Rule-Based Engine.
- **Web Scraper**: `BeautifulSoup`, `Requests`.

## 🧠 Recommendation Logic & Training Data

The NLP engine is **not** a large pre-trained LLM (like GPT or Llama). Instead, it uses a highly efficient, deterministic hybrid approach to rank schemes:

1. **Rule-Based Filters**: The system strictly checks hard constraints. If a scheme requires a female applicant, it explicitly filters out males. It checks exact parameters like:
   - Age limits
   - Income limits (e.g., `< 2.5 Lakhs/yr`)
   - Caste categories
   - BPL status
   - Specific tags (Widow, Student, Farmer, etc.)

2. **Semantic Matching (TF-IDF)**: After rule-based filtering, the engine converts the user's profile into a descriptive natural language string. It uses a **TF-IDF Vectorizer** (Term Frequency-Inverse Document Frequency) trained dynamically on the loaded scheme dataset to calculate **Cosine Similarity** between the user's profile text and the scheme's text (description, eligibility text, benefits, and tags).

3. **Scoring System**: The final rank is calculated by weighting the rule-based eligibility score, the NLP relevance score, and priority boosts for specific categories (e.g., student scholarships, farmer aids).

### What data is it trained/seeded on?

The system is seeded with **25 real Indian Government Schemes**. When the backend starts up, it automatically inserts these schemes into the database and trains the TF-IDF vectorizer on them. 

Some of the seeded schemes include:
- PM-KISAN Samman Nidhi
- Pradhan Mantri Awas Yojana (PMAY)
- Pradhan Mantri Jan Dhan Yojana (PMJDY)
- Ayushman Bharat PM-JAY
- Mahatma Gandhi National Rural Employment Guarantee (MGNREGA)
- Pradhan Mantri Ujjwala Yojana
- Various Post Matric Scholarships (SC/ST/OBC/Minority)
- Sukanya Samriddhi Yojana
- MUDRA Loan Yojana

Additionally, the project includes a **Web Scraper** (`backend/scraper/scraper.py`) capable of extracting new schemes from sources like:
- `myscheme.gov.in`
- `scholarships.gov.in`
- Wikipedia pages

## 📦 How to Run

1. Ensure you have **MongoDB** running locally on port `27017` (default).
2. Ensure you have **Node.js** and **Python 3.9+** installed.
3. Run the startup script from the root directory:

```bash
chmod +x start.sh
./start.sh
```

This script will automatically:
- Create a Python virtual environment and install backend dependencies (`pip install -r requirements.txt`).
- Install React dependencies (`npm install`).
- Boot the FastAPI backend on `http://localhost:8000`.
- Boot the Vite React frontend on `http://localhost:5173`.

## 📂 Project Structure

```
govtsitehelper/
├── start.sh                      # Unified startup script
├── backend/                      # FastAPI Backend
│   ├── main.py                   # App entrypoint & Lifespan events
│   ├── database.py               # MongoDB connection
│   ├── models.py                 # Pydantic schemas
│   ├── seed_data.py              # 25 real Government Schemes
│   ├── nlp/
│   │   └── engine.py             # Rule-based + TF-IDF Recommendation logic
│   ├── api/
│   │   └── routes.py             # API Endpoints (Auth, Recommend, Search, Admin)
│   └── scraper/
│       └── scraper.py            # Web Scraper (BeautifulSoup)
└── frontend/                     # React Frontend
    ├── index.html
    ├── vite.config.js            # Vite config with Proxy to Backend
    └── src/
        ├── App.jsx               # Routing
        ├── index.css             # Tailwind setup & theme
        ├── components/
        │   └── Navbar.jsx        # Navigation bar
        └── pages/
            ├── Home.jsx          # Multi-column form UI
            ├── Search.jsx        # NLP Semantic Search UI
            └── Dashboard.jsx     # Result ranking & details UI
```
