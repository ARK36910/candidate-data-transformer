"""
Tests for the merger module.
"""

import pytest
from src.models import Candidate, Experience, Education, Location, ProvenanceEntry
from src.merge.merger import merge


def _make_csv_candidate(**kwargs) -> Candidate:
    defaults = dict(
        candidate_id="csv-001",
        full_name="Ananya Roy",
        emails=["ananya.roy@gmail.com"],
        phones=["+919876543210"],
        headline="Senior Data Scientist",
        skills=["Python", "Machine Learning"],
        location=Location(city="Bengaluru", country="IN"),
        links=["https://linkedin.com/in/ananya-roy"],
        provenance=[ProvenanceEntry(field="full_name", source="recruiter.csv", method="csv_column")],
    )
    defaults.update(kwargs)
    return Candidate(**defaults)


def _make_pdf_candidate(**kwargs) -> Candidate:
    defaults = dict(
        candidate_id="pdf-001",
        full_name="Ananya Roy",
        emails=["ananya@work.com"],
        phones=["+919876543210", "+918888888888"],
        headline="ML Engineer",
        skills=["TensorFlow", "Python", "SQL"],
        experience=[Experience(title="ML Engineer", company="Acme Corp", start="2021-01", end="present")],
        education=[Education(degree="B.Tech Computer Science", institution="IIT Delhi", start="2015-07", end="2019-05")],
        links=["https://github.com/ananya-roy"],
        provenance=[ProvenanceEntry(field="full_name", source="resume.pdf", method="pdf_heuristic")],
    )
    defaults.update(kwargs)
    return Candidate(**defaults)


class TestMerger:
    def test_emails_are_unioned(self):
        csv_c = _make_csv_candidate()
        pdf_c = _make_pdf_candidate()
        merged = merge(csv_c, pdf_c)
        assert "ananya.roy@gmail.com" in merged.emails
        assert "ananya@work.com" in merged.emails

    def test_duplicate_emails_not_repeated(self):
        csv_c = _make_csv_candidate(emails=["shared@example.com"])
        pdf_c = _make_pdf_candidate(emails=["shared@example.com", "other@example.com"])
        merged = merge(csv_c, pdf_c)
        assert merged.emails.count("shared@example.com") == 1

    def test_phones_are_unioned(self):
        csv_c = _make_csv_candidate()
        pdf_c = _make_pdf_candidate()
        merged = merge(csv_c, pdf_c)
        assert "+919876543210" in merged.phones
        assert "+918888888888" in merged.phones

    def test_skills_are_unioned(self):
        csv_c = _make_csv_candidate(skills=["Python", "Machine Learning"])
        pdf_c = _make_pdf_candidate(skills=["TensorFlow", "SQL", "Python"])
        merged = merge(csv_c, pdf_c)
        assert "Python" in merged.skills
        assert "Machine Learning" in merged.skills
        assert "TensorFlow" in merged.skills
        assert merged.skills.count("Python") == 1  # no duplicates

    def test_duplicate_skills_removed(self):
        csv_c = _make_csv_candidate(skills=["Python", "SQL"])
        pdf_c = _make_pdf_candidate(skills=["python", "SQL", "TensorFlow"])
        merged = merge(csv_c, pdf_c)
        # "Python" and "python" are deduped case-insensitively
        sql_count = sum(1 for s in merged.skills if s.lower() == "sql")
        assert sql_count == 1

    def test_scalar_name_prefers_csv(self):
        csv_c = _make_csv_candidate(full_name="Ananya Roy (CSV)")
        pdf_c = _make_pdf_candidate(full_name="Ananya Roy (PDF)")
        merged = merge(csv_c, pdf_c)
        assert merged.full_name == "Ananya Roy (CSV)"

    def test_scalar_name_falls_back_to_pdf(self):
        csv_c = _make_csv_candidate(full_name=None)
        pdf_c = _make_pdf_candidate(full_name="Ananya Roy (PDF)")
        merged = merge(csv_c, pdf_c)
        assert merged.full_name == "Ananya Roy (PDF)"

    def test_conflicting_headline_prefers_csv(self):
        csv_c = _make_csv_candidate(headline="Senior Data Scientist")
        pdf_c = _make_pdf_candidate(headline="ML Engineer")
        merged = merge(csv_c, pdf_c)
        assert merged.headline == "Senior Data Scientist"

    def test_experience_combined(self):
        csv_c = _make_csv_candidate(experience=[])
        pdf_c = _make_pdf_candidate()
        merged = merge(csv_c, pdf_c)
        assert len(merged.experience) == 1
        assert merged.experience[0].title == "ML Engineer"

    def test_experience_duplicates_removed(self):
        exp = Experience(title="ML Engineer", company="Acme Corp", start="2021-01", end="present")
        csv_c = _make_csv_candidate(experience=[exp])
        pdf_c = _make_pdf_candidate(experience=[exp])
        merged = merge(csv_c, pdf_c)
        # Same title+company → deduped to 1
        assert len(merged.experience) == 1

    def test_education_combined(self):
        csv_c = _make_csv_candidate(education=[])
        pdf_c = _make_pdf_candidate()
        merged = merge(csv_c, pdf_c)
        assert len(merged.education) == 1

    def test_education_duplicates_removed(self):
        edu = Education(degree="B.Tech Computer Science", institution="IIT Delhi")
        csv_c = _make_csv_candidate(education=[edu])
        pdf_c = _make_pdf_candidate(education=[edu])
        merged = merge(csv_c, pdf_c)
        assert len(merged.education) == 1

    def test_links_unioned(self):
        csv_c = _make_csv_candidate(links=["https://linkedin.com/in/ananya-roy"])
        pdf_c = _make_pdf_candidate(links=["https://github.com/ananya-roy"])
        merged = merge(csv_c, pdf_c)
        assert "https://linkedin.com/in/ananya-roy" in merged.links
        assert "https://github.com/ananya-roy" in merged.links

    def test_provenance_combined_from_both(self):
        csv_c = _make_csv_candidate()
        pdf_c = _make_pdf_candidate()
        merged = merge(csv_c, pdf_c)
        sources = {p.source for p in merged.provenance}
        assert "recruiter.csv" in sources
        assert "resume.pdf" in sources

    def test_candidate_id_from_csv(self):
        csv_c = _make_csv_candidate(candidate_id="the-csv-id")
        pdf_c = _make_pdf_candidate(candidate_id="the-pdf-id")
        merged = merge(csv_c, pdf_c)
        assert merged.candidate_id == "the-csv-id"
