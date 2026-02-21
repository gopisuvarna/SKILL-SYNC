"""Job ingestion service: fetch from Adzuna, store in DB, expand skills."""
import logging
from django.db import transaction
from core.services.adzuna_service import fetch_jobs
from core.services.skill_extractor import extract_skills

from apps.jobs.models import Job, JobSkill
from apps.skills.models import Skill

logger = logging.getLogger(__name__)


def _get_or_create_skill(name: str) -> Skill:
    from core.services.skill_extractor import normalize_skill
    nm = normalize_skill(name)
    skill, _ = Skill.objects.get_or_create(normalized_name=nm.lower(), defaults={'name': nm})
    return skill


def sync_jobs(country: str = 'us', max_pages: int = 5):
    """Ingest jobs from Adzuna and store in DB."""
    seen = set()
    created = 0
    for page in range(1, max_pages + 1):
        results = fetch_jobs(country=country, page=page)
        if not results:
            break
        for r in results:
            ext_id = r.get('id')
            if not ext_id or str(ext_id) in seen:
                continue
            seen.add(str(ext_id))
            with transaction.atomic():
                job, created_flag = Job.objects.get_or_create(
                    external_id=str(ext_id),
                    defaults={
                        'title': r.get('title', '')[:512],
                        'company': r.get('company', {}).get('display_name', '')[:256],
                        'location': r.get('location', {}).get('display_name', '')[:256],
                        'description': r.get('description', '')[:10000],
                        'url': r.get('redirect_url', ''),
                        'salary_min': r.get('salary_min'),
                        'salary_max': r.get('salary_max'),
                    }
                )
                if created_flag:
                    created += 1
                    text = f"{job.title} {job.description}"
                    skills = extract_skills(text, use_llm=False)
                    for s in skills[:20]:
                        skill = _get_or_create_skill(s)
                        JobSkill.objects.get_or_create(job=job, skill=skill)
    logger.info("Job sync: %d new jobs", created)
    return created
