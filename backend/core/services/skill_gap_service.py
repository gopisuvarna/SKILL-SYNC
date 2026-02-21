"""Skill gap: Role Skills - User Skills. Returns missing_skills, coverage_percent, learning_priority."""
from typing import List, Dict, Any


def compute_skill_gap(
    user_skill_ids: set,
    role_skill_list: List[Dict[str, Any]],  # [{skill_id, skill_name, importance_weight}]
) -> Dict[str, Any]:
    """
    Skill Gap = Role Skills - User Skills
    Returns: missing_skills, coverage_percent, learning_priority (sorted by importance)
    """
    role_skill_ids = {str(s['skill_id']) for s in role_skill_list}
    missing = [s for s in role_skill_list if str(s['skill_id']) not in user_skill_ids]
    coverage = (len(role_skill_ids) - len(missing)) / len(role_skill_ids) * 100 if role_skill_ids else 100.0

    # learning_priority: sort missing by importance_weight desc
    learning_priority = sorted(
        [{'skill_id': s['skill_id'], 'skill_name': s.get('skill_name', ''), 'importance': s.get('importance_weight', 0.5)} for s in missing],
        key=lambda x: x['importance'],
        reverse=True,
    )

    return {
        'missing_skills': [s.get('skill_name', '') for s in missing],
        'coverage_percent': round(coverage, 2),
        'learning_priority': learning_priority,
    }
