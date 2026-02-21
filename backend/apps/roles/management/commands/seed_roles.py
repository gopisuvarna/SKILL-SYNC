"""Seed sample roles and skills for development."""
from django.core.management.base import BaseCommand
from apps.roles.models import Role, RoleSkill
from apps.skills.models import Skill
from core.services.skill_extractor import normalize_skill


def get_or_create_skill(name: str):
    nm = normalize_skill(name)
    skill, _ = Skill.objects.get_or_create(normalized_name=nm.lower(), defaults={'name': nm})
    return skill


class Command(BaseCommand):
    help = 'Seed roles and skills'

    def handle(self, *args, **options):
        roles_data = [
            ('Software Engineer', 'Full-stack development', ['Python', 'JavaScript', 'React', 'PostgreSQL', 'Docker', 'Git']),
            ('Data Scientist', 'Data analysis and ML', ['Python', 'Machine Learning', 'Pandas', 'NumPy', 'scikit-learn', 'SQL']),
            ('DevOps Engineer', 'Infrastructure and CI/CD', ['Docker', 'Kubernetes', 'AWS', 'Terraform', 'Jenkins', 'Linux']),
            ('Frontend Developer', 'Client-side development', ['React', 'TypeScript', 'HTML', 'CSS', 'Tailwind', 'JavaScript']),
            ('Backend Developer', 'Server-side development', ['Python', 'Django', 'PostgreSQL', 'REST API', 'Docker', 'Redis']),
        ]
        for title, desc, skill_names in roles_data:
            role, _ = Role.objects.get_or_create(
                title=title,
                defaults={'description': desc}
            )
            for sn in skill_names:
                skill = get_or_create_skill(sn)
                RoleSkill.objects.get_or_create(role=role, skill=skill, defaults={'importance_weight': 1.0})
        self.stdout.write(self.style.SUCCESS('Seeded roles'))
