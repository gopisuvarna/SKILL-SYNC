"""
Re-ranking engine with weighted formula:
FINAL_SCORE = 0.5 * Skill Coverage + 0.3 * Skill Importance Weight + 0.2 * TF-IDF

- Skill Coverage: (matched skills / total role skills) — how many role skills user has
- Skill Importance Weight: avg importance_weight of matched skills
- TF-IDF: cosine similarity of skill text vectors (approximated via embedding cosine)
"""
from collections import Counter
from typing import List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def compute_skill_coverage(user_skill_ids: set, role_skill_ids: set) -> float:
    """matched / total role skills. 0-1."""
    if not role_skill_ids:
        return 0.0
    matched = len(user_skill_ids & role_skill_ids)
    return matched / len(role_skill_ids)


def compute_importance_weight(
    user_skill_ids: set,
    role_skill_weights: Dict[str, float],
) -> float:
    """Average importance of matched skills. 0-1, default 0.5 if no matches."""
    matched = [role_skill_weights.get(sid, 0) for sid in user_skill_ids if sid in role_skill_weights]
    if not matched:
        return 0.0
    return sum(matched) / len(matched)


def compute_tfidf_score(user_skill_names: List[str], role_skill_names: List[str]) -> float:
    """TF-IDF cosine similarity between user skills and role skills. 0-1."""
    if not user_skill_names or not role_skill_names:
        return 0.0
    user_text = ' '.join(user_skill_names)
    role_text = ' '.join(role_skill_names)
    vectorizer = TfidfVectorizer()
    try:
        matrix = vectorizer.fit_transform([user_text, role_text])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return max(0.0, min(1.0, float(sim)))
    except Exception:
        return 0.0


def re_rank(
    candidate_roles: List[Dict[str, Any]],
    user_skill_ids: set,
    user_skill_names: List[str],
    role_skills_map: Dict[str, List[Dict]],  # role_id -> [{skill_id, skill_name, importance_weight}]
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Re-rank candidate roles and return top_k with scores.
    """
    scored = []
    for role in candidate_roles:
        rid = str(role.get('id', ''))
        rs_list = role_skills_map.get(rid, [])
        role_skill_ids = {str(s['skill_id']) for s in rs_list}
        role_skill_names = [s.get('skill_name', '') for s in rs_list]
        role_weights = {str(s['skill_id']): s.get('importance_weight', 1.0) for s in rs_list}

        cov = compute_skill_coverage(user_skill_ids, role_skill_ids)
        imp = compute_importance_weight(user_skill_ids, role_weights)
        tfidf = compute_tfidf_score(user_skill_names, role_skill_names)

        final = 0.5 * cov + 0.3 * imp + 0.2 * tfidf
        scored.append({
            **role,
            'match_score': round(final, 4),
            'skill_coverage': round(cov, 4),
            'importance_score': round(imp, 4),
            'tfidf_score': round(tfidf, 4),
        })

    scored.sort(key=lambda x: x['match_score'], reverse=True)
    return scored[:top_k]
