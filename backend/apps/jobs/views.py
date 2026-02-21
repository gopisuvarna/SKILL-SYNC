"""Job listing and matching views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch
from django.db.models import Count, Q

from apps.jobs.models import Job, JobSkill
from apps.skills.models import UserSkill


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_jobs(request):
    """Paginated job list."""
    page = int(request.query_params.get('page', 1))
    per_page = min(int(request.query_params.get('per_page', 20)), 50)
    offset = (page - 1) * per_page
    qs = Job.objects.prefetch_related(
        Prefetch('skills', queryset=JobSkill.objects.select_related('skill'))
    ).order_by('-created_at')[offset:offset + per_page]
    data = []
    for j in qs:
        data.append({
            'id': str(j.id),
            'title': j.title,
            'company': j.company,
            'location': j.location,
            'url': j.url,
            'salary_min': float(j.salary_min) if j.salary_min else None,
            'salary_max': float(j.salary_max) if j.salary_max else None,
            'skills': [js.skill.name for js in j.skills.all()],
        })
    return Response({'results': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def matched_jobs(request):
    """Jobs whose skills overlap with user skills. Order by match count."""
    user_skill_ids = set(UserSkill.objects.filter(user=request.user).values_list('skill_id', flat=True))
    if not user_skill_ids:
        return Response({'results': []})

    job_ids = JobSkill.objects.filter(skill_id__in=user_skill_ids).values_list('job_id', flat=True).distinct()
    qs = Job.objects.filter(id__in=job_ids).prefetch_related(
        Prefetch('skills', queryset=JobSkill.objects.select_related('skill'))
    ).order_by('-created_at')[:20]

    data = []
    for j in qs:
        skills = list(j.skills.all())
        matched = [s.skill.name for s in skills if s.skill_id in user_skill_ids]
        data.append({
            'id': str(j.id),
            'title': j.title,
            'company': j.company,
            'location': j.location,
            'url': j.url,
            'matched_skills': matched,
            'all_skills': [s.skill.name for s in skills],
        })
    return Response({'results': data})
