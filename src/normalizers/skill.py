"""
Skill normalizer.

Maps common abbreviations, aliases, and typos to canonical skill names.

Examples:
  ML   → Machine Learning
  Py   → Python
  CPP  → C++
  JS   → JavaScript
"""

from __future__ import annotations
from rapidfuzz import process, fuzz

# Canonical skill names (used as the target set for fuzzy matching)
CANONICAL_SKILLS: list[str] = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C",
    "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    "MATLAB", "Bash", "Shell Scripting", "PowerShell",
    "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
    "Django", "Flask", "FastAPI", "Spring Boot", "Ruby on Rails",
    "SQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis",
    "Cassandra", "Elasticsearch", "DynamoDB",
    "Machine Learning", "Deep Learning", "Natural Language Processing",
    "Computer Vision", "Reinforcement Learning", "Data Science",
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "XGBoost",
    "Pandas", "NumPy", "Matplotlib", "Seaborn",
    "AWS", "Google Cloud", "Azure", "Docker", "Kubernetes",
    "Git", "Linux", "REST API", "GraphQL", "Microservices",
    "Agile", "Scrum", "DevOps", "CI/CD",
]

# Explicit alias map (checked before fuzzy matching)
_ALIAS_MAP: dict[str, str] = {
    # Languages
    "py": "Python",
    "python3": "Python",
    "python2": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "cpp": "C++",
    "c plus plus": "C++",
    "csharp": "C#",
    "c sharp": "C#",
    "golang": "Go",
    "rb": "Ruby",
    # ML / AI
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "ai": "Machine Learning",
    "rl": "Reinforcement Learning",
    "ds": "Data Science",
    "data sci": "Data Science",
    # Frameworks / libs
    "tf": "TensorFlow",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "pytorch": "PyTorch",
    "reactjs": "React",
    "react.js": "React",
    "vuejs": "Vue.js",
    "nodejs": "Node.js",
    "node": "Node.js",
    "expressjs": "Express.js",
    # Cloud
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "amazon web services": "AWS",
    "microsoft azure": "Azure",
    # Databases
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "elastic": "Elasticsearch",
    # DevOps
    "k8s": "Kubernetes",
    "cicd": "CI/CD",
    "ci/cd": "CI/CD",
    # Other
    "rest": "REST API",
    "restful": "REST API",
    "restful api": "REST API",
}

_FUZZY_THRESHOLD = 82  # minimum score for a fuzzy match to be accepted


def normalise_skill(raw: str) -> str:
    """
    Map a raw skill string to its canonical form.
    Checks alias map first, then fuzzy-matches against canonical skill names.
    Returns the raw string (title-cased) if no match is found.
    """
    key = raw.strip().lower()

    if key in _ALIAS_MAP:
        return _ALIAS_MAP[key]

    # Fuzzy match against canonical list
    match = process.extractOne(raw, CANONICAL_SKILLS, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= _FUZZY_THRESHOLD:
        return match[0]

    return raw.strip().title()


def normalise_skills(skills: list[str]) -> list[str]:
    """Normalise a list of skills, deduplicating canonical results."""
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        normalised = normalise_skill(s)
        if normalised not in seen:
            seen.add(normalised)
            result.append(normalised)
    return result
