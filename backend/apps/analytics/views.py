"""Analytics API: skill distribution, match score, top roles, skill gaps, learning plan, job matches."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch, Count

from apps.skills.models import UserSkill
from apps.roles.models import Role, RoleSkill
from apps.jobs.models import Job, JobSkill
from apps.recommendations.models import Course
from core.services.embedding_service import encode_single
from core.services.faiss_service import get_faiss_index
from core.services.ranking_service import re_rank
from core.services.skill_gap_service import compute_skill_gap
from core.services.learning_recommendation_service import get_courses_for_skills


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Optimized analytics: select_related / prefetch_related."""
    user = request.user
    user_skills = list(UserSkill.objects.filter(user=user).select_related('skill').values('skill_id', 'skill__name'))
    user_skill_ids = {str(s['skill_id']) for s in user_skills}
    user_skill_names = [s['skill__name'] for s in user_skills]

    # Skill distribution
    skill_distribution = [{'skill': s['skill__name']} for s in user_skills]

    # Top roles (FAISS + re-rank)
    top_roles = []
    if user_skill_names:
        user_vec = encode_single(' '.join(user_skill_names))
        faiss_index = get_faiss_index()
        candidates = faiss_index.search(user_vec, k=30)
        if candidates:
            role_ids = [rid for rid, _ in candidates]
            roles = Role.objects.filter(id__in=role_ids).prefetch_related(
                Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
            )
            role_map = {str(r.id): r for r in roles}
            role_list = [{'id': str(rid), 'title': role_map[rid].title} for rid in role_ids if rid in role_map]
            role_skills_map = {}
            for r in roles:
                rs_list = [{'skill_id': str(rs.skill_id), 'skill_name': rs.skill.name, 'importance_weight': rs.importance_weight} for rs in r.skills.all()]
                role_skills_map[str(r.id)] = rs_list
            top_roles = re_rank(role_list, user_skill_ids, user_skill_names, role_skills_map, top_k=5)
        else:
            for r in Role.objects.prefetch_related('skills').order_by('?')[:5]:
                rs_list = [{'skill_id': str(rs.skill_id), 'skill_name': rs.skill.name, 'importance_weight': rs.importance_weight} for rs in r.skills.all()]
                top_roles.append({'id': str(r.id), 'title': r.title, 'match_score': 0.0})

    # Skill gaps for top role
    skill_gaps = []
    if top_roles:
        rid = top_roles[0].get('id')
        role = Role.objects.prefetch_related(Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))).filter(id=rid).first()
        if role:
            rs_list = [{'skill_id': str(rs.skill_id), 'skill_name': rs.skill.name, 'importance_weight': rs.importance_weight} for rs in role.skills.all()]
            skill_gaps = compute_skill_gap(user_skill_ids, rs_list)

    # Learning plan
    learning_plan = []
    if skill_gaps and skill_gaps.get('missing_skills'):
        learning_plan = get_courses_for_skills(skill_gaps['missing_skills'][:5], limit_per_skill=2)

    # Job matches
    job_ids = JobSkill.objects.filter(skill_id__in=user_skill_ids).values_list('job_id', flat=True).distinct()[:10]
    jobs = Job.objects.filter(id__in=job_ids).prefetch_related(Prefetch('skills', queryset=JobSkill.objects.select_related('skill')))[:5]
    job_matches = [{'id': str(j.id), 'title': j.title, 'company': j.company, 'url': j.url, 'matched_skills': [js.skill.name for js in j.skills.all() if js.skill_id in user_skill_ids]} for j in jobs]

    return Response({
        'skill_distribution': skill_distribution,
        'match_score': top_roles[0]['match_score'] if top_roles else 0.0,
        'top_roles': top_roles,
        'skill_gaps': skill_gaps,
        'learning_plan': learning_plan,
        'job_matches': job_matches,
    })
