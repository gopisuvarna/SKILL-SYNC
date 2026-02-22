from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Set

import spacy
from spacy.matcher import PhraseMatcher
from google import genai    

from django.conf import settings


# =====================================================
# CONFIG (LLM - GOOGLE GEMINI)
# =====================================================

client = genai.Client(api_key=settings.GOOGLE_API_KEY)


# =====================================================
# NLP SKILL EXTRACTOR (spaCy + skills.txt)
# Deterministic & Fast
# =====================================================
class SkillExtractor:
    """
    Deterministic skill extraction using spaCy PhraseMatcher
    with predefined skills.txt dataset.
    """

    _nlp = None
    _matcher = None
    _skills_loaded = False

    @classmethod
    def _initialize(cls) -> None:
        """
        Lazy initialization of spaCy and PhraseMatcher
        (Loads only once for performance)
        """
        if cls._nlp is not None:
            return

        try:
            print("🔹 Loading spaCy model...")
            cls._nlp = spacy.load("en_core_web_sm")

            matcher = PhraseMatcher(
                cls._nlp.vocab,
                attr="LOWER"
            )

            # Path to skills.txt (inside resumes folder)
            skills_path = Path(__file__).parent / "skill.txt"

            if not skills_path.exists():
                raise Exception(
                    "skills.txt not found inside resumes folder"
                )

            # Load skills from file
            skills = [
                line.strip().lower()
                for line in skills_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            # Convert skills into spaCy patterns
            patterns = [
                cls._nlp.make_doc(skill)
                for skill in skills
            ]

            # Add patterns to matcher
            matcher.add("SKILLS", patterns)

            cls._matcher = matcher
            cls._skills_loaded = True

            print(f"✅ Skill matcher initialized with {len(skills)} skills.")

        except Exception as e:
            raise Exception(f"Failed to initialize SkillExtractor: {e}")

    @classmethod
    def extract(cls, text: str) -> List[str]:
        """
        Extract skills using spaCy PhraseMatcher + skills.txt
        """
        if not text:
            return []

        cls._initialize()

        doc = cls._nlp(text)
        matches = cls._matcher(doc)

        skills: Set[str] = set()

        for match_id, start, end in matches:
            span = doc[start:end]
            skills.add(span.text.lower())

        return sorted(skills)


# =====================================================
# LLM SKILL EXTRACTOR (GOOGLE GEMINI)
# For unseen/advanced skills not in skills.txt
# =====================================================
class LLMSkillExtractor:
    """
    Uses Google Gemini LLM to extract unseen skills
    """

    def __init__(self):
        self.system_prompt = """
You are an expert resume parser.

Extract ONLY professional technical skills from the resume.

RULES:
- Return JSON only.
- No explanation.
- No markdown.
- No extra text.
- Remove duplicates.
- Lowercase everything.

FORMAT:
{
 "skills": ["python", "machine learning", "sql"]
}
"""

    def extract(self, resume_text: str) -> List[str]:
        if not resume_text:
            return []

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"{self.system_prompt}\n\nResume:\n{resume_text}"
                            }
                        ]
                    }
                ],
                config={
                    "temperature": 0.0
                }
            )

            text = response.text.strip()

            text = re.sub(r"```json|```", "", text).strip()

            match = re.search(r"\{.*\}", text, re.DOTALL)
            json_text = match.group(0) if match else text

            data = json.loads(json_text)

            skills = data.get("skills", [])

            if not isinstance(skills, list):
                return []

            return list(set(skill.lower() for skill in skills))

        except Exception as e:
            print("❌ LLM Skill Extraction Error:", e)
            return []


# =====================================================
# FINAL COMBINED SKILL TOOL (NLP + LLM)
# This is what your project should call
# =====================================================
class SkillTool:
    """
    Main tool to extract skills from resume text.
    Combines:
    1. NLP (spaCy + skills.txt) → Accurate predefined skills
    2. LLM (Gemini) → Unseen skills
    """

    name = "skill_tool"
    description = "Extract candidate skills from resume text."

    rule_extractor = SkillExtractor()
    llm_extractor = LLMSkillExtractor()

    @staticmethod
    def run(text: str):
        """
        Run full skill extraction pipeline
        """

        if not text:
            return {
                "rule_based_skills": [],
                "llm_skills": [],
                "all_skills": []
            }

        print("🚀 Running Skill Extraction Pipeline...")

        # 1️⃣ NLP + skills.txt (deterministic)
        rule_skills: Set[str] = set(
            SkillTool.rule_extractor.extract(text)
        )

        # 2️⃣ LLM (unseen skills)
        llm_skills: Set[str] = set(
            SkillTool.llm_extractor.extract(text)
        )

        # 3️⃣ Combine both
        final_skills = sorted(rule_skills.union(llm_skills))

        return {
            "rule_based_skills": sorted(rule_skills),
            "llm_skills": sorted(llm_skills),
            "all_skills": final_skills
        }
