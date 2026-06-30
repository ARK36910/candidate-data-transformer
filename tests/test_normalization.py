"""
Tests for individual normalizer modules.
"""

import pytest
from src.normalizers.phone import normalise_phone, normalise_phones
from src.normalizers.email import normalise_email, normalise_emails
from src.normalizers.date import normalise_date, normalise_date_range
from src.normalizers.country import normalise_country
from src.normalizers.skill import normalise_skill, normalise_skills
from src.normalizers.name import normalise_name


# ── Phone ────────────────────────────────────────────────────────────────────

class TestPhoneNormalizer:
    def test_10_digit_indian_number(self):
        assert normalise_phone("9876543210") == "+919876543210"

    def test_already_e164(self):
        assert normalise_phone("+15551234567") == "+15551234567"

    def test_number_with_dashes(self):
        result = normalise_phone("+1-555-123-4567")
        assert result == "+15551234567"

    def test_number_with_spaces(self):
        result = normalise_phone("+91 98765 43210")
        assert result == "+919876543210"

    def test_dedup_in_list(self):
        phones = ["9876543210", "+919876543210"]
        result = normalise_phones(phones)
        assert len(result) == 1


# ── Email ────────────────────────────────────────────────────────────────────

class TestEmailNormalizer:
    def test_uppercase_to_lower(self):
        assert normalise_email("ABC@GMAIL.COM") == "abc@gmail.com"

    def test_spaces_around_at(self):
        assert normalise_email("ABC @ Gmail.com") == "abc@gmail.com"

    def test_mixed_case_domain(self):
        assert normalise_email("User@Work.Org") == "user@work.org"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError):
            normalise_email("not-an-email")

    def test_dedup_list(self):
        emails = ["ABC@gmail.com", "abc@gmail.com", "other@work.com"]
        result = normalise_emails(emails)
        assert result == ["abc@gmail.com", "other@work.com"]

    def test_invalid_silently_dropped_in_list(self):
        emails = ["good@example.com", "bad-email", "another@example.com"]
        result = normalise_emails(emails)
        assert "bad-email" not in result
        assert len(result) == 2


# ── Date ─────────────────────────────────────────────────────────────────────

class TestDateNormalizer:
    def test_full_month_name(self):
        assert normalise_date("January 2023") == "2023-01"

    def test_abbreviated_month(self):
        assert normalise_date("Sep 2021") == "2021-09"

    def test_iso_date_truncated(self):
        assert normalise_date("2023-06-15") == "2023-06"

    def test_present(self):
        assert normalise_date("Present") == "present"

    def test_current(self):
        assert normalise_date("current") == "present"

    def test_bare_year(self):
        assert normalise_date("2020") == "2020"

    def test_mm_yyyy_slash(self):
        assert normalise_date("03/2020") == "2020-03"

    def test_date_range(self):
        start, end = normalise_date_range("Jan 2020", "March 2023")
        assert start == "2020-01"
        assert end == "2023-03"

    def test_date_range_with_present(self):
        start, end = normalise_date_range("June 2022", "Present")
        assert start == "2022-06"
        assert end == "present"

    def test_none_inputs(self):
        start, end = normalise_date_range(None, None)
        assert start is None and end is None


# ── Country ───────────────────────────────────────────────────────────────────

class TestCountryNormalizer:
    def test_full_name_india(self):
        assert normalise_country("India") == "IN"

    def test_full_name_usa(self):
        assert normalise_country("United States") == "US"

    def test_alias_usa(self):
        assert normalise_country("USA") == "US"

    def test_german_name(self):
        assert normalise_country("Deutschland") == "DE"

    def test_already_code(self):
        assert normalise_country("GB") == "GB"

    def test_case_insensitive(self):
        assert normalise_country("india") == "IN"
        assert normalise_country("INDIA") == "IN"


# ── Skill ─────────────────────────────────────────────────────────────────────

class TestSkillNormalizer:
    def test_ml_alias(self):
        assert normalise_skill("ML") == "Machine Learning"

    def test_py_alias(self):
        assert normalise_skill("Py") == "Python"

    def test_cpp_alias(self):
        assert normalise_skill("CPP") == "C++"

    def test_js_alias(self):
        assert normalise_skill("js") == "JavaScript"

    def test_already_canonical(self):
        assert normalise_skill("Python") == "Python"

    def test_dedup_list(self):
        skills = ["ML", "Machine Learning", "Python", "Py"]
        result = normalise_skills(skills)
        assert result.count("Machine Learning") == 1
        assert result.count("Python") == 1

    def test_fuzzy_tensorflow(self):
        # "TensorFlow" should fuzzy-match to "TensorFlow"
        result = normalise_skill("Tensorflow")
        assert result == "TensorFlow"


# ── Name ──────────────────────────────────────────────────────────────────────

class TestNameNormalizer:
    def test_all_caps(self):
        assert normalise_name("ANANYA ROY") == "Ananya Roy"

    def test_extra_whitespace(self):
        assert normalise_name(" ANANYA  roy ") == "Ananya Roy"

    def test_already_correct(self):
        assert normalise_name("Ananya Roy") == "Ananya Roy"

    def test_all_lowercase(self):
        assert normalise_name("john doe") == "John Doe"

    def test_hyphenated_name(self):
        assert normalise_name("anne-marie curie") == "Anne-Marie Curie"

    def test_particle_preservation(self):
        result = normalise_name("ludwig van beethoven")
        assert result == "Ludwig van Beethoven"
