"""
Hybrid skill extraction engine: Rule-based + NLP + LLM.
Production-grade pipeline with deduplication and normalization.
"""
import json
import logging
import re
from typing import List, Set

from flashtext import KeywordProcessor
import spacy
from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy load models
_nlp = None
_keyword_processor = None
_skill_normalization_map = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load('en_core_web_sm')
        except OSError:
            _nlp = spacy.load('en_core_web_trf' if spacy.util.is_package('en_core_web_trf') else 'en_core_web_sm')
    return _nlp


def _get_keyword_processor():
    global _keyword_processor
    if _keyword_processor is None:
        from apps.skills.data.master_skills import MASTER_SKILLS  # noqa
        kp = KeywordProcessor()
        for s in MASTER_SKILLS:
            kp.add_keyword(s, s)
        _keyword_processor = kp
    return _keyword_processor


def _get_normalization_map():
    global _skill_normalization_map
    if _skill_normalization_map is None:
        _skill_normalization_map = {
            'react.js': 'React', 'reactjs': 'React',
            'node.js': 'Node.js', 'nodejs': 'Node.js',
            'vue.js': 'Vue.js', 'vuejs': 'Vue.js',
            'typescript': 'TypeScript', 'javascript': 'JavaScript',
            'python': 'Python', 'java': 'Java', 'go': 'Go', 'rust': 'Rust',
            'c++': 'C++', 'c#': 'C#', 'php': 'PHP', 'kotlin': 'Kotlin', 'swift': 'Swift',
            'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
            'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL',
            'mongodb': 'MongoDB', 'mysql': 'MySQL', 'redis': 'Redis',
            'docker': 'Docker', 'kubernetes': 'Kubernetes',
            'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP',
            'git': 'Git', 'github': 'GitHub', 'gitlab': 'GitLab',
            'rest api': 'REST API', 'rest': 'REST', 'graphql': 'GraphQL',
            'machine learning': 'Machine Learning', 'deep learning': 'Deep Learning',
            'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
            'scikit-learn': 'scikit-learn', 'nlp': 'NLP',
            'html': 'HTML', 'css': 'CSS', 'sass': 'SASS', 'tailwind': 'Tailwind',
            'agile': 'Agile', 'scrum': 'Scrum', 'jira': 'Jira',
            'linux': 'Linux', 'bash': 'Bash', 'testing': 'Testing',
        }
    return _skill_normalization_map


def normalize_skill(raw: str) -> str:
    nmap = _get_normalization_map()
    lower = raw.strip().lower()
    return nmap.get(lower, raw.strip())


def rule_based_extract(text: str) -> List[str]:
    """FlashText deterministic matches from MASTER_SKILLS."""
    kp = _get_keyword_processor()
    matches = kp.extract_keywords(text)
    return list(dict.fromkeys(matches))


def nlp_extract(text: str) -> List[str]:
    """spaCy: noun phrases and skill-like tokens."""
    nlp = _get_nlp()
    doc = nlp(text[:100000])
    skills = set()
    for chunk in doc.noun_chunks:
        tok = chunk.root.lemma_.lower()
        if len(tok) > 2 and tok.isalpha() and tok not in {'the', 'and', 'for', 'with', 'from', 'that'}:
            skills.add(chunk.text.strip())
    for ent in doc.ents:
        if ent.label_ in ('ORG', 'PRODUCT', 'GPE', 'WORK_OF_ART'):
            skills.add(ent.text.strip())
    return [s for s in skills if 2 < len(s) < 50]


def llm_extract(text: str, unseen_candidates: List[str]) -> List[str]:
    """Google AI Studio: extract skills from unseen text/candidates. Use sparingly."""
    if not unseen_candidates:
        return []
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_AI_CONFIG.get('API_KEY'))
        model = genai.GenerativeModel('gemini-pro')
        prompt = (
            "Extract ONLY professional skills from this text. "
            "Return a clean JSON array of skill strings. No explanations.\n\n"
            f"Text: {text[:3000]}\n\n"
            f"Candidate phrases to consider: {unseen_candidates[:30]}\n\n"
            "JSON array:"
        )
        response = model.generate_content(prompt)
        txt = response.text.strip()
        if txt.startswith('```'):
            txt = re.sub(r'^```\w*\n?', '', txt)
            txt = re.sub(r'\n?```$', '', txt)
        arr = json.loads(txt)
        if isinstance(arr, list):
            return [str(x).strip() for x in arr if x and isinstance(x, (str,))]
    except Exception as e:
        logger.warning("LLM extract failed: %s", e)
    return []


def deduplicate_by_similarity(skills: List[str], threshold: float = 0.85) -> List[str]:
    """Remove near-duplicates using simple string similarity."""
    from difflib import SequenceMatcher

    def sim(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    result = []
    for s in skills:
        ns = normalize_skill(s)
        if not ns:
            continue
        if any(sim(ns, r) >= threshold for r in result):
            continue
        result.append(ns)
    return result


def extract_skills(text: str, use_llm: bool = False) -> List[str]:
    """
    Full pipeline: rule-based + NLP + optional LLM.
    Returns normalized, deduplicated skill list.
    """
    if not text or not text.strip():
        return []
    rule_skills = rule_based_extract(text)
    nlp_skills = nlp_extract(text)
    combined = set(rule_skills)
    for s in nlp_skills:
        ns = normalize_skill(s)
        if ns and ns not in combined:
            combined.add(ns)
    if use_llm:
        unseen = [s for s in nlp_skills if s not in combined]
        llm_skills = llm_extract(text, unseen)
        for s in llm_skills:
            ns = normalize_skill(s)
            if ns:
                combined.add(ns)
    return deduplicate_by_similarity(list(combined))
