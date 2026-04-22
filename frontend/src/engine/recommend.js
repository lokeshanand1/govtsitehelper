/**
 * GovScheme Advisor — Client-side NLP Recommendation Engine
 * A JavaScript implementation of the Python NLP engine for GitHub Pages static deployment.
 * Uses rule-based filtering + keyword similarity scoring.
 */

import { SCHEMES } from '../data/schemes.js';

/**
 * Check rule-based eligibility. Returns { score, reasons }.
 */
function checkEligibility(profile, scheme) {
  const elig = scheme.eligibility || {};
  let score = 0;
  let maxScore = 0;
  const reasons = [];

  // Age check
  if (elig.min_age || elig.max_age) {
    maxScore += 20;
    const age = profile.age || 0;
    const minA = elig.min_age || 0;
    const maxA = elig.max_age || 200;
    if (age && minA <= age && age <= maxA) {
      score += 20;
      reasons.push(`Age ${age} is within ${minA}-${maxA} years`);
    } else if (age) {
      return { score: 0, reasons: ["Age requirement not met"] };
    }
  }

  // Gender check
  if (elig.gender) {
    maxScore += 15;
    const gender = (profile.gender || "").toLowerCase();
    if (elig.gender.map(g => g.toLowerCase()).includes(gender)) {
      score += 15;
      reasons.push(`Gender (${gender}) matches requirement`);
    } else if (gender) {
      return { score: 0, reasons: ["Gender requirement not met"] };
    }
  }

  // Caste check
  if (elig.caste_categories) {
    maxScore += 15;
    const caste = (profile.caste_category || "").toLowerCase();
    if (elig.caste_categories.map(c => c.toLowerCase()).includes(caste)) {
      score += 15;
      reasons.push(`Caste category (${caste.toUpperCase()}) is eligible`);
    } else if (caste) {
      return { score: 0, reasons: ["Caste category not eligible"] };
    }
  }

  // BPL check
  if (elig.bpl_required === true) {
    maxScore += 15;
    if (profile.bpl_status) {
      score += 15;
      reasons.push("BPL status confirmed");
    } else {
      return { score: 0, reasons: ["BPL status required"] };
    }
  }

  // Income check
  if (elig.max_annual_income) {
    maxScore += 15;
    const income = profile.annual_family_income || 0;
    if (income && income <= elig.max_annual_income) {
      score += 15;
      reasons.push(`Income ₹${income.toLocaleString()} within limit of ₹${elig.max_annual_income.toLocaleString()}`);
    } else if (income && income > elig.max_annual_income) {
      return { score: 0, reasons: ["Income exceeds maximum limit"] };
    }
  }

  // State check
  if (elig.states) {
    maxScore += 10;
    const state = (profile.state || "").toLowerCase();
    if (elig.states.map(s => s.toLowerCase()).includes(state)) {
      score += 10;
      reasons.push(`Available in ${state}`);
    } else if (state) {
      return { score: 0, reasons: ["Not available in your state"] };
    }
  }

  // Area type
  if (elig.area_type && elig.area_type !== "both") {
    maxScore += 10;
    const area = (profile.area_type || "").toLowerCase();
    if (area === elig.area_type.toLowerCase()) {
      score += 10;
      reasons.push(`Available in ${area} areas`);
    } else if (area) {
      return { score: 0, reasons: [`Only available in ${elig.area_type} areas`] };
    }
  }

  // Student check
  if (elig.is_student === true) {
    maxScore += 10;
    if (profile.is_student) {
      score += 10;
      reasons.push("Student status confirmed");
    } else {
      return { score: 0, reasons: ["Must be a student"] };
    }
  }

  // Farmer check
  if (elig.is_farmer === true) {
    maxScore += 10;
    if (profile.is_farmer) {
      score += 10;
      reasons.push("Farmer status confirmed");
    } else {
      return { score: 0, reasons: ["Must be a farmer"] };
    }
  }

  // Disability check
  if (elig.is_disabled === true) {
    maxScore += 10;
    if (profile.disability_status) {
      score += 10;
      reasons.push("Disability status confirmed");
    } else {
      return { score: 0, reasons: ["Disability required"] };
    }
  }

  // Widow check
  if (elig.is_widow === true) {
    maxScore += 10;
    if (profile.is_widow) {
      score += 10;
      reasons.push("Widow status confirmed");
    } else {
      return { score: 0, reasons: ["Must be a widow"] };
    }
  }

  // Senior citizen check
  if (elig.is_senior_citizen === true) {
    maxScore += 10;
    if (profile.is_senior_citizen || (profile.age || 0) >= 60) {
      score += 10;
      reasons.push("Senior citizen status confirmed");
    } else {
      return { score: 0, reasons: ["Must be a senior citizen"] };
    }
  }

  // Minority check
  if (elig.is_minority === true) {
    maxScore += 10;
    if (profile.minority_status) {
      score += 10;
      reasons.push("Minority status confirmed");
    } else {
      return { score: 0, reasons: ["Must belong to minority community"] };
    }
  }

  if (maxScore === 0) {
    return { score: 70, reasons: ["Generally eligible — no specific restrictions"] };
  }

  const pct = Math.round((score / maxScore) * 100);
  return { score: pct, reasons: reasons.length ? reasons : ["Eligible based on profile match"] };
}

/**
 * Build user profile text for keyword matching.
 */
function buildUserText(profile) {
  const parts = [];
  if (profile.gender) parts.push(profile.gender);
  if (profile.age) {
    parts.push(`${profile.age} years old`);
    if (profile.age < 30) parts.push("youth");
    if (profile.age >= 60) parts.push("senior citizen elderly");
  }
  if (profile.caste_category) parts.push(profile.caste_category);
  if (profile.bpl_status) parts.push("BPL below poverty line poor");
  if (profile.is_student) parts.push("student education scholarship");
  if (profile.is_farmer) parts.push("farmer agriculture land crop");
  if (profile.employment_status) parts.push(profile.employment_status);
  if (profile.occupation) parts.push(profile.occupation);
  if (profile.state) parts.push(profile.state);
  if (profile.area_type) parts.push(profile.area_type);
  if (profile.is_widow) parts.push("widow pension");
  if (profile.is_senior_citizen) parts.push("senior citizen pension old age");
  if (profile.disability_status) parts.push("disability disabled handicapped");
  if (profile.minority_status) parts.push("minority");
  if (profile.annual_family_income) {
    const inc = profile.annual_family_income;
    if (inc < 100000) parts.push("low income poor");
    else if (inc < 300000) parts.push("lower income");
    else if (inc < 800000) parts.push("middle income");
  }
  return parts.join(" ").toLowerCase();
}

/**
 * Simple keyword-based similarity score (lightweight TF-IDF approximation).
 */
function keywordSimilarity(userText, schemeText) {
  const userTokens = new Set(userText.toLowerCase().split(/\s+/).filter(t => t.length > 2));
  const schemeTokens = new Set(schemeText.toLowerCase().split(/\s+/).filter(t => t.length > 2));
  if (userTokens.size === 0 || schemeTokens.size === 0) return 0;

  let overlap = 0;
  for (const token of userTokens) {
    if (schemeTokens.has(token)) overlap++;
  }
  return overlap / Math.sqrt(userTokens.size * schemeTokens.size);
}

/**
 * Main recommendation function — mirrors NLPEngine.recommend().
 */
export function recommend(profile, topK = 30) {
  const userText = buildUserText(profile);
  const results = [];

  for (const scheme of SCHEMES) {
    const { score: eligScore, reasons } = checkEligibility(profile, scheme);
    if (eligScore <= 0) continue;

    const schemeText = `${scheme.name} ${scheme.description} ${scheme.eligibility_text} ${scheme.benefits} ${(scheme.tags || []).join(" ")}`;
    const nlpScore = keywordSimilarity(userText, schemeText);

    // Priority boost
    let priority = 0;
    const cat = scheme.category || "";
    if (profile.is_student && cat === "scholarship") priority = 10;
    if (profile.is_farmer && cat === "farmer") priority = 10;
    if (profile.is_widow && (cat === "pension" || cat === "women")) priority = 10;
    if (profile.is_senior_citizen && cat === "pension") priority = 10;

    const total = (eligScore * 0.5) + (nlpScore * 100 * 0.35) + (priority * 0.15);

    results.push({
      scheme_id: scheme.scheme_id,
      name: scheme.name,
      name_hindi: scheme.name_hindi || "",
      category: cat,
      description: scheme.description,
      eligibility_score: Math.round(eligScore * 10) / 10,
      nlp_relevance_score: Math.round(nlpScore * 1000) / 10,
      classifier_score: 0,
      total_score: Math.round(total * 10) / 10,
      why_eligible: reasons.join("; "),
      benefits: scheme.benefits,
      how_to_apply: scheme.how_to_apply,
      documents_required: scheme.documents_required || [],
      apply_link: scheme.apply_link || "",
      official_website: scheme.official_website || "",
      state: scheme.state || "All India",
      eligibility_text: scheme.eligibility_text || "",
    });
  }

  results.sort((a, b) => b.total_score - a.total_score);
  return results.slice(0, topK);
}

/**
 * Semantic search — simple keyword matching.
 */
export function semanticSearch(query, topK = 15) {
  const results = [];
  for (const scheme of SCHEMES) {
    const schemeText = `${scheme.name} ${scheme.description} ${scheme.eligibility_text} ${scheme.benefits} ${(scheme.tags || []).join(" ")}`;
    const score = keywordSimilarity(query, schemeText);
    if (score > 0.01) {
      results.push({ scheme, score });
    }
  }
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, topK);
}
