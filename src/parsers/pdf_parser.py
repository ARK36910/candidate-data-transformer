"""
Parses a resume PDF into a Candidate model using regex heuristics.

Extracts:
  - email, phone, name (header heuristic)
  - headline / title
  - skills section
  - experience entries
  - education entries
  - URLs / links
"""

from __future__ import annotations
import re
import PyPDF2
from typing import Optional
from src.models import Candidate, Experience, Education, Location, ProvenanceEntry


# ── Regex patterns ──────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{4,6}"
)
_URL_RE = re.compile(
    r"https?://[^\s\)\]>\"']+"
    r"|(?:www|linkedin\.com|github\.com)[^\s\)\]>\"']+"
)
_SECTION_RE = re.compile(
    r"^(skills?|experience|work experience|employment|education|"
    r"projects?|summary|objective|profile|about)\s*[:\-]?\s*$",
    re.IGNORECASE,
)
_DATE_RANGE_RE = re.compile(
    r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}"
    r"|\b\d{4})\s*[\-–—to]+\s*"
    r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}"
    r"|\b\d{4}|[Pp]resent|[Cc]urrent)",
    re.IGNORECASE,
)


def _extract_text(path: str) -> str:
    text_parts: list[str] = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _split_into_sections(text: str) -> dict[str, str]:
    """Split raw text into named sections by header detection."""
    sections: dict[str, str] = {"header": ""}
    current = "header"
    lines = text.splitlines()
    buf: list[str] = []

    for line in lines:
        if _SECTION_RE.match(line.strip()):
            sections[current] = "\n".join(buf)
            current = line.strip().lower().rstrip(":- ")
            buf = []
        else:
            buf.append(line)

    sections[current] = "\n".join(buf)
    return sections


def _guess_name(header: str) -> Optional[str]:
    """Assume the first non-empty, non-contact line in the header is the name."""
    for line in header.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like contact info
        if _EMAIL_RE.search(line) or _PHONE_RE.search(line) or _URL_RE.search(line):
            continue
        # Likely a name if it's 1-4 words, mostly alphabetic
        words = line.split()
        if 1 <= len(words) <= 5 and all(re.match(r"[A-Za-z\-'\.]+$", w) for w in words):
            return line
    return None


def _parse_experience(text: str) -> list[Experience]:
    entries: list[Experience] = []
    blocks = re.split(r"\n{2,}", text.strip())
    for block in blocks:
        if not block.strip():
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        title: Optional[str] = None
        company: Optional[str] = None
        start: Optional[str] = None
        end: Optional[str] = None

        for line in lines:
            m = _DATE_RANGE_RE.search(line)
            if m:
                start = m.group(1)
                end = m.group(2)
            elif title is None:
                title = line
            elif company is None:
                company = line

        if title:
            entries.append(Experience(title=title, company=company, start=start, end=end))
    return entries


def _parse_education(text: str) -> list[Education]:
    entries: list[Education] = []
    blocks = re.split(r"\n{2,}", text.strip())
    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        degree: Optional[str] = None
        institution: Optional[str] = None
        start: Optional[str] = None
        end: Optional[str] = None

        for line in lines:
            m = _DATE_RANGE_RE.search(line)
            if m:
                start = m.group(1)
                end = m.group(2)
            elif degree is None:
                degree = line
            elif institution is None:
                institution = line

        if degree or institution:
            entries.append(Education(degree=degree, institution=institution, start=start, end=end))
    return entries


def _parse_skills(text: str) -> list[str]:
    skills: list[str] = []
    for line in text.splitlines():
        parts = re.split(r"[,|•\t]+", line)
        for p in parts:
            p = p.strip()
            if p and len(p) < 50:
                skills.append(p)
    return [s for s in skills if s]


def parse_pdf(path: str) -> Candidate:
    """Read the resume PDF and return a partially-filled Candidate."""
    text = _extract_text(path)
    sections = _split_into_sections(text)
    header_text = sections.get("header", "")
    provenance: list[ProvenanceEntry] = []

    candidate = Candidate()

    # --- name ---
    name = _guess_name(header_text)
    if name:
        candidate.full_name = name
        provenance.append(ProvenanceEntry(field="full_name", source="resume.pdf", method="pdf_heuristic"))

    # --- emails ---
    emails = list(dict.fromkeys(_EMAIL_RE.findall(text)))  # unique, order-preserved
    if emails:
        candidate.emails = emails
        provenance.append(ProvenanceEntry(field="emails", source="resume.pdf", method="regex"))

    # --- phones ---
    phones = list(dict.fromkeys(
        m.strip() for m in _PHONE_RE.findall(text) if len(m.replace(" ", "").replace("-", "")) >= 7
    ))
    if phones:
        candidate.phones = phones
        provenance.append(ProvenanceEntry(field="phones", source="resume.pdf", method="regex"))

    # --- headline (first non-name line after name in header) ---
    found_name = False
    for line in header_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if name and line == name:
            found_name = True
            continue
        if found_name and not _EMAIL_RE.search(line) and not _PHONE_RE.search(line):
            candidate.headline = line
            provenance.append(ProvenanceEntry(field="headline", source="resume.pdf", method="pdf_heuristic"))
            break

    # --- links ---
    links = list(dict.fromkeys(_URL_RE.findall(text)))
    if links:
        candidate.links = links
        provenance.append(ProvenanceEntry(field="links", source="resume.pdf", method="regex"))

    # --- skills ---
    skill_text = sections.get("skills", sections.get("skill", ""))
    if skill_text:
        candidate.skills = _parse_skills(skill_text)
        provenance.append(ProvenanceEntry(field="skills", source="resume.pdf", method="pdf_heuristic"))

    # --- experience ---
    exp_text = sections.get("experience", sections.get("work experience", sections.get("employment", "")))
    if exp_text:
        candidate.experience = _parse_experience(exp_text)
        provenance.append(ProvenanceEntry(field="experience", source="resume.pdf", method="pdf_heuristic"))

    # --- education ---
    edu_text = sections.get("education", "")
    if edu_text:
        candidate.education = _parse_education(edu_text)
        provenance.append(ProvenanceEntry(field="education", source="resume.pdf", method="pdf_heuristic"))

    candidate.provenance = provenance
    return candidate
