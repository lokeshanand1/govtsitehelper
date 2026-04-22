"""
GovScheme Advisor — API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os

import time

from models import UserProfile, SearchQuery, UserAuth, Token, SchemeModel
from database import get_db
from nlp.engine import nlp_engine
from nlp.trainer import train_and_save, load_model_meta
from scraper.scraper import run_full_scrape
from seed_data import SCHEMES

router = APIRouter()
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))


# ──────────────────────────────────────────────
# AUTH HELPERS
# ──────────────────────────────────────────────

def create_token(email: str, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION)
    return jwt.encode({"sub": email, "role": role, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ──────────────────────────────────────────────
# AUTH ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/auth/register", response_model=Token)
async def register(user: UserAuth):
    db = get_db()
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = pwd_context.hash(user.password)
    await db.users.insert_one({
        "email": user.email,
        "hashed_password": hashed,
        "role": "user",
        "created_at": datetime.utcnow()
    })
    token = create_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login", response_model=Token)
async def login(user: UserAuth):
    db = get_db()
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.email, db_user.get("role", "user"))
    return {"access_token": token, "token_type": "bearer"}


# ──────────────────────────────────────────────
# RECOMMENDATION ENDPOINT (MAIN) — with timing
# ──────────────────────────────────────────────

@router.post("/recommend")
async def recommend_schemes(profile: UserProfile):
    """Main endpoint: takes user profile form data, returns NLP-ranked scheme recommendations."""
    t_start = time.time()

    profile_dict = profile.model_dump()
    
    # Load schemes from DB
    t_db_start = time.time()
    db = get_db()
    schemes = []
    async for s in db.schemes.find({"status": "active"}):
        s.pop("_id", None)
        schemes.append(s)
    
    if not schemes:
        # Fallback to seed data
        schemes = SCHEMES
    t_db_end = time.time()
    
    # Load into NLP engine and recommend
    t_nlp_start = time.time()
    nlp_engine.load_schemes(schemes)
    results = nlp_engine.recommend(profile_dict, top_k=30)
    t_nlp_end = time.time()
    
    t_end = time.time()

    # Timing metrics (in milliseconds)
    timing = {
        "db_fetch_ms": round((t_db_end - t_db_start) * 1000, 2),
        "nlp_pipeline_ms": round((t_nlp_end - t_nlp_start) * 1000, 2),
        "total_ms": round((t_end - t_start) * 1000, 2),
    }

    # Categorize results
    categorized = {
        "total": len(results),
        "classifier_used": nlp_engine.classifier_available,
        "timing": timing,
        "all": results,
        "scholarship": [r for r in results if r["category"] == "scholarship"],
        "pension": [r for r in results if r["category"] == "pension"],
        "women": [r for r in results if r["category"] == "women"],
        "student": [r for r in results if r["category"] in ["scholarship", "student"]],
        "farmer": [r for r in results if r["category"] == "farmer"],
        "employment": [r for r in results if r["category"] in ["employment", "startup"]],
        "health": [r for r in results if r["category"] in ["health", "insurance"]],
    }
    
    return categorized


@router.post("/recommend/benchmark")
async def benchmark_recommend(profile: UserProfile):
    """Benchmark endpoint: measures exact execution time of the hybrid NLP pipeline."""
    t_total_start = time.time()

    profile_dict = profile.model_dump()

    # --- Phase 1: DB fetch ---
    t_db_start = time.time()
    db = get_db()
    schemes = []
    async for s in db.schemes.find({"status": "active"}):
        s.pop("_id", None)
        schemes.append(s)
    if not schemes:
        schemes = SCHEMES
    t_db_end = time.time()

    # --- Phase 2: Scheme indexing (TF-IDF fit) ---
    t_index_start = time.time()
    nlp_engine.load_schemes(schemes)
    t_index_end = time.time()

    # --- Phase 3: Rule-based + TF-IDF + Classifier scoring ---
    t_rec_start = time.time()
    results = nlp_engine.recommend(profile_dict, top_k=30)
    t_rec_end = time.time()

    t_total_end = time.time()

    return {
        "total_results": len(results),
        "classifier_used": nlp_engine.classifier_available,
        "timing_ms": {
            "db_fetch": round((t_db_end - t_db_start) * 1000, 2),
            "tfidf_indexing": round((t_index_end - t_index_start) * 1000, 2),
            "recommendation_scoring": round((t_rec_end - t_rec_start) * 1000, 2),
            "total_end_to_end": round((t_total_end - t_total_start) * 1000, 2),
        }
    }


# ──────────────────────────────────────────────
# SEARCH ENDPOINT
# ──────────────────────────────────────────────

@router.post("/search")
async def search_schemes(query: SearchQuery):
    """NLP-powered intelligent scheme search."""
    db = get_db()
    schemes = []
    async for s in db.schemes.find({"status": "active"}):
        s.pop("_id", None)
        schemes.append(s)
    
    if not schemes:
        schemes = SCHEMES
    
    nlp_engine.load_schemes(schemes)
    results = nlp_engine.semantic_search(query.query, top_k=15)
    
    return {
        "query": query.query,
        "total": len(results),
        "results": [
            {
                "name": s.get("name", ""),
                "name_hindi": s.get("name_hindi", ""),
                "description": s.get("description", ""),
                "category": s.get("category", ""),
                "relevance_score": round(score * 100, 1),
                "benefits": s.get("benefits", ""),
                "apply_link": s.get("apply_link", ""),
                "eligibility_text": s.get("eligibility_text", ""),
            }
            for s, score in results
        ]
    }


# ──────────────────────────────────────────────
# SCHEME CRUD (for admin)
# ──────────────────────────────────────────────

@router.get("/schemes")
async def list_schemes(category: Optional[str] = None, state: Optional[str] = None):
    db = get_db()
    query = {"status": "active"}
    if category:
        query["category"] = category
    if state:
        query["state"] = {"$in": [state, "All India"]}
    
    schemes = []
    async for s in db.schemes.find(query):
        s["_id"] = str(s["_id"])
        schemes.append(s)
    return {"total": len(schemes), "schemes": schemes}


@router.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    db = get_db()
    scheme = await db.schemes.find_one({"scheme_id": scheme_id})
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    scheme["_id"] = str(scheme["_id"])
    
    # Simplify eligibility text
    if scheme.get("eligibility_text"):
        scheme["eligibility_simple"] = nlp_engine.simplify_text(scheme["eligibility_text"])
    
    return scheme


@router.post("/admin/schemes", dependencies=[Depends(require_admin)])
async def create_scheme(scheme: SchemeModel):
    db = get_db()
    data = scheme.model_dump()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    await db.schemes.insert_one(data)
    return {"message": "Scheme created", "scheme_id": data.get("scheme_id")}


@router.put("/admin/schemes/{scheme_id}", dependencies=[Depends(require_admin)])
async def update_scheme(scheme_id: str, scheme: SchemeModel):
    db = get_db()
    data = scheme.model_dump()
    data["updated_at"] = datetime.utcnow()
    result = await db.schemes.update_one({"scheme_id": scheme_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {"message": "Scheme updated"}


@router.delete("/admin/schemes/{scheme_id}", dependencies=[Depends(require_admin)])
async def delete_scheme(scheme_id: str):
    db = get_db()
    result = await db.schemes.delete_one({"scheme_id": scheme_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {"message": "Scheme deleted"}


# ──────────────────────────────────────────────
# ADMIN: SCRAPER & ANALYTICS
# ──────────────────────────────────────────────

@router.post("/admin/scrape", dependencies=[Depends(require_admin)])
async def trigger_scraper():
    """Trigger web scraper to fetch new schemes."""
    scraped = run_full_scrape()
    db = get_db()
    inserted = 0
    for s in scraped:
        if s.get("name"):
            s["status"] = "pending_review"
            s["created_at"] = datetime.utcnow()
            try:
                await db.scraped_schemes.insert_one(s)
                inserted += 1
            except Exception:
                pass
    return {"message": f"Scraped {len(scraped)} schemes, inserted {inserted} new entries"}


@router.get("/admin/analytics", dependencies=[Depends(require_admin)])
async def get_analytics():
    db = get_db()
    total_schemes = await db.schemes.count_documents({})
    active_schemes = await db.schemes.count_documents({"status": "active"})
    total_users = await db.users.count_documents({})
    total_searches = await db.search_logs.count_documents({})
    
    # Category breakdown
    pipeline_agg = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = []
    async for doc in db.schemes.aggregate(pipeline_agg):
        categories.append({"category": doc["_id"], "count": doc["count"]})
    
    return {
        "total_schemes": total_schemes,
        "active_schemes": active_schemes,
        "total_users": total_users,
        "total_searches": total_searches,
        "categories": categories
    }


@router.post("/admin/train", dependencies=[Depends(require_admin)])
async def train_classifier():
    """Train (or retrain) the NLP scheme classifier on current scheme data.

    Generates synthetic training samples from scheme eligibility rules,
    trains a TF-IDF + LogisticRegression pipeline, and saves to disk.
    Also hot-reloads the classifier into the running NLP engine.
    """
    db = get_db()
    schemes = []
    async for s in db.schemes.find({"status": "active"}):
        s.pop("_id", None)
        schemes.append(s)

    if not schemes:
        raise HTTPException(status_code=400, detail="No schemes found to train on")

    metrics = train_and_save(schemes)
    nlp_engine.reload_classifier()

    return {"status": "trained", "metrics": metrics}


@router.get("/admin/model-info", dependencies=[Depends(require_admin)])
async def get_model_info():
    """Return metadata about the currently saved NLP classifier model.

    Includes training timestamp, sample count, F1 score, and model path.
    """
    meta = load_model_meta()
    if not meta:
        return {
            "status": "not_trained",
            "classifier_loaded": nlp_engine.classifier_available,
            "message": "No trained model found on disk. POST /api/admin/train to train."
        }
    meta["classifier_loaded"] = nlp_engine.classifier_available
    meta["status"] = "trained"
    return meta


@router.get("/admin/users", dependencies=[Depends(require_admin)])
async def list_users():
    db = get_db()
    users = []
    async for u in db.users.find({}, {"hashed_password": 0}):
        u["_id"] = str(u["_id"])
        users.append(u)
    return {"total": len(users), "users": users}


# ──────────────────────────────────────────────
# EXPLAIN ENDPOINT
# ──────────────────────────────────────────────

@router.post("/explain")
async def explain_scheme(data: dict):
    """Simplify scheme text for easy understanding."""
    text = data.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text required")
    simplified = nlp_engine.simplify_text(text)
    return {"original": text, "simplified": simplified}


# ──────────────────────────────────────────────
# CATEGORIES / STATES LISTS
# ──────────────────────────────────────────────

@router.get("/meta/categories")
async def get_categories():
    return {"categories": [
        "scholarship", "pension", "women", "student", "farmer",
        "employment", "health", "housing", "startup", "social_security",
        "insurance", "skill_development", "other"
    ]}

@router.get("/meta/states")
async def get_states():
    return {"states": [
        "All India", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
        "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
        "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
        "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi",
        "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh"
    ]}
