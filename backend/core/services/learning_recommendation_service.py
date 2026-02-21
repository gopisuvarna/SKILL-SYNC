"""Map missing skills to courses. Return top recommendations per missing skill."""
from typing import List, Dict

from apps.recommendations.models import Course


def get_courses_for_skills(skill_names: List[str], limit_per_skill: int = 3) -> List[Dict]:
    """Return courses that teach any of the given skills. skills_taught is JSON list of skill names."""
    if not skill_names:
        return []
    skill_lower = {s.lower(): s for s in skill_names}
    courses = Course.objects.all()[:50]
    result = []
    for c in courses:
        taught = c.skills_taught or []
        taught_str = ' '.join(str(x).lower() for x in taught)
        matched = [skill_lower[s] for s in skill_lower if s in taught_str or any(s in str(t).lower() for t in taught)]
        if not matched:
            continue
        result.append({
            'id': str(c.id),
            'title': c.title,
            'provider': c.provider,
            'url': c.url,
            'skills_taught': c.skills_taught,
            'matched_skills': matched,
        })
    return result[:limit_per_skill * len(skill_names)] if skill_names else result
