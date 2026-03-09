"""
Resume & text skill extraction: spaCy phrase matcher + Groq LLM.

This module is the **single source of truth** for skill extraction across the
project. It is used for:
- Uploaded resume/document skills
- User skills (manual skills, jobs ingestion, role seeding)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Set

import spacy
from spacy.matcher import PhraseMatcher
from groq import Groq

from django.conf import settings


# ---------------------------------------------------------------------------
# PUBLIC HELPERS (used by views, jobs, roles)
# ---------------------------------------------------------------------------
_SKILL_NORMALIZATION_MAP = {
    "react.js": "React",
    "reactjs": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "python": "Python",
    "java": "Java",
    "go": "Go",
    "rust": "Rust",
    "c++": "C++",
    "c#": "C#",
    "php": "PHP",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mysql": "MySQL",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "rest api": "REST API",
    "rest": "REST",
    "graphql": "GraphQL",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "nlp": "NLP",
    "html": "HTML",
    "css": "CSS",
    "sass": "SASS",
    "tailwind": "Tailwind",
    "agile": "Agile",
    "scrum": "Scrum",
    "jira": "Jira",
    "linux": "Linux",
    "bash": "Bash",
    "testing": "Testing",
}


def normalize_skill(raw: str) -> str:
    """
    Normalize a raw skill string into a canonical form.
    """
    if not raw:
        return ""
    lower = raw.strip().lower()
    return _SKILL_NORMALIZATION_MAP.get(lower, raw.strip())


def extract_skills(text: str, use_llm: bool = False) -> List[str]:
    """
    Unified extraction API used across the app.

    For both:
      - user skills (skills views, jobs ingestion, role seeding)
      - uploaded document skills (resume upload)

    It delegates to SkillTool.run(...) and returns the final normalized list.
    The use_llm flag is kept for backwards compatibility; SkillTool already
    combines rule-based and LLM signals.
    """
    if not text or not text.strip():
        return []
    data = SkillTool.run(text)
    raw_skills = data.get("all_skills") or []
    seen = set()
    result: List[str] = []
    for s in raw_skills:
        ns = normalize_skill(s)
        if not ns:
            continue
        key = ns.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(ns)
    return result


# ---------------------------------------------------------------------------
# CONFIG (LLM - GROQ)
# ---------------------------------------------------------------------------
client = Groq(api_key=settings.GROQ_API_KEY)


# ---------------------------------------------------------------------------
# NLP SKILL EXTRACTOR (spaCy + skill.txt)
# ---------------------------------------------------------------------------
class SkillExtractor:
    _nlp = None
    _matcher = None

    @classmethod
    def _initialize(cls) -> None:
        if cls._nlp is not None:
            return
        try:
            print("🔹 Loading spaCy model...")
            cls._nlp = spacy.load("en_core_web_sm")
            matcher = PhraseMatcher(cls._nlp.vocab, attr="LOWER")
            # Skills list lives in skills app data
            skills_path = Path(__file__).resolve().parent.parent / "data" / "skill.txt"
            if not skills_path.exists():
                raise Exception("skill.txt not found in apps/skills/data/")
            skills = [
                line.strip().lower()
                for line in skills_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            patterns = [cls._nlp.make_doc(skill) for skill in skills]
            matcher.add("SKILLS", patterns)
            cls._matcher = matcher
            print(f"✅ Skill matcher initialized with {len(skills)} skills.")
        except Exception as e:
            raise Exception(f"Failed to initialize SkillExtractor: {e}") from e

    @classmethod
    def extract(cls, text: str) -> List[str]:
        if not text:
            return []
        cls._initialize()
        doc = cls._nlp(text)
        matches = cls._matcher(doc)
        skills: Set[str] = set()
        for _, start, end in matches:
            span = doc[start:end]
            skills.add(span.text.lower())
        return sorted(skills)


# ---------------------------------------------------------------------------
# LLM SKILL EXTRACTOR (GROQ)
# ---------------------------------------------------------------------------
class LLMSkillExtractor:
    system_prompt = """
You are an expert resume parsing system.

Your task is to extract ALL professional technical skills from the provided resume text.

INCLUDE:
- Programming languages
- Frameworks and libraries
- Databases
- Cloud platforms
- DevOps tools
- Machine learning tools
- Data science tools
- Web technologies
- Operating systems
- Version control tools
- Software tools and platforms
- Technical methodologies

EXCLUDE:
- Soft skills (e.g., communication, leadership, teamwork)
- Personal traits
- Hobbies
- Certifications (unless they are technologies like AWS, Azure, etc.)
- Company names (unless they are technologies)

RULES:
- Return ONLY valid JSON.
- No explanation.
- No markdown.
- No extra text.
- Lowercase everything.
- Remove duplicates.
- Extract both explicitly mentioned and strongly implied technical skills.
- If a skill appears multiple times, return it only once.

FORMAT:
{
  "skills": ["python", "django", "aws", "machine learning"]
}

If no skills are found, return:
{
  "skills": []
}
"""

    def extract(self, resume_text: str) -> List[str]:
        if not resume_text:
            return []
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Resume:\n{resume_text}"},
                ],
                temperature=0.0,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            json_text = match.group(0) if match else text
            data = json.loads(json_text)
            skills = data.get("skills", [])
            if not isinstance(skills, list):
                return []
            return list(set(skill.lower() for skill in skills))
        except Exception as e:
            print("❌ Groq Skill Extraction Error:", e)
            return []


# ---------------------------------------------------------------------------
# COMBINED SKILL TOOL (resume upload flow)
# ---------------------------------------------------------------------------
class SkillTool:
    rule_extractor = SkillExtractor()
    llm_extractor = LLMSkillExtractor()

    @staticmethod
    def run(text: str):
        if not text:
            return {
                "rule_based_skills": [],
                "llm_skills": [],
                "all_skills": [],
            }
        #print("🚀 Running Skill Extraction Pipeline...")
        rule_skills: Set[str] = set(SkillTool.rule_extractor.extract(text))
        llm_skills: Set[str] = set(SkillTool.llm_extractor.extract(text))
        final_skills = sorted(rule_skills.union(llm_skills))
        return {
            "rule_based_skills": sorted(rule_skills),
            "llm_skills": sorted(llm_skills),
            "all_skills": final_skills,
        }
