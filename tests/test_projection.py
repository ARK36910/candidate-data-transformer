"""
Tests for the projector module.
"""

import pytest
from src.projection.projector import project


_CANONICAL = {
    "candidate_id": "abc-123",
    "full_name": "Ananya Roy",
    "emails": ["ananya.roy@gmail.com"],
    "phones": ["+919876543210"],
    "location": {"city": "Bengaluru", "state": None, "country": "IN"},
    "headline": "Senior Data Scientist",
    "skills": ["Python", "Machine Learning", "TensorFlow"],
    "experience": [
        {"title": "ML Engineer", "company": "Acme Corp", "start": "2021-01", "end": "present", "description": None}
    ],
    "education": [
        {"degree": "B.Tech", "institution": "IIT Delhi", "start": "2015-07", "end": "2019-05"}
    ],
    "links": ["https://github.com/ananya-roy"],
    "provenance": [
        {"field": "full_name", "source": "recruiter.csv", "method": "csv_column"}
    ],
    "overall_confidence": 0.91,
}


class TestProjectorFieldSelection:
    def test_only_selected_fields_present(self):
        config = {
            "fields": ["full_name", "emails"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert set(result.keys()) == {"full_name", "emails"}

    def test_all_fields_when_no_fields_key(self):
        config = {
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        # Should include everything except confidence and provenance (handled separately)
        assert "full_name" in result
        assert "emails" in result
        assert "skills" in result


class TestProjectorRenaming:
    def test_renamed_field(self):
        config = {
            "fields": ["full_name", "emails"],
            "rename": {"full_name": "name"},
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "name" in result
        assert "full_name" not in result
        assert result["name"] == "Ananya Roy"

    def test_multiple_renames(self):
        config = {
            "fields": ["full_name", "emails", "skills"],
            "rename": {"full_name": "name", "emails": "email_addresses"},
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "name" in result
        assert "email_addresses" in result
        assert "skills" in result  # not renamed


class TestProjectorConfidence:
    def test_confidence_included(self):
        config = {
            "fields": ["full_name"],
            "include_confidence": True,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "overall_confidence" in result
        assert result["overall_confidence"] == 0.91

    def test_confidence_excluded(self):
        config = {
            "fields": ["full_name"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "overall_confidence" not in result

    def test_confidence_renamed(self):
        config = {
            "fields": ["full_name"],
            "rename": {"overall_confidence": "score"},
            "include_confidence": True,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "score" in result
        assert "overall_confidence" not in result


class TestProjectorProvenance:
    def test_provenance_included(self):
        config = {
            "fields": ["full_name"],
            "include_confidence": False,
            "include_provenance": True,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "provenance" in result
        assert isinstance(result["provenance"], list)

    def test_provenance_excluded(self):
        config = {
            "fields": ["full_name"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(_CANONICAL, config)
        assert "provenance" not in result


class TestProjectorMissingValues:
    def test_missing_as_null(self):
        canonical = dict(_CANONICAL, headline=None)
        config = {
            "fields": ["full_name", "headline"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(canonical, config)
        assert "headline" in result
        assert result["headline"] is None

    def test_missing_omitted(self):
        canonical = dict(_CANONICAL, headline=None)
        config = {
            "fields": ["full_name", "headline"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "omit",
        }
        result = project(canonical, config)
        assert "headline" not in result

    def test_empty_list_treated_as_missing_null(self):
        canonical = dict(_CANONICAL, links=[])
        config = {
            "fields": ["full_name", "links"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "null",
        }
        result = project(canonical, config)
        assert result["links"] is None

    def test_empty_list_omitted(self):
        canonical = dict(_CANONICAL, links=[])
        config = {
            "fields": ["full_name", "links"],
            "include_confidence": False,
            "include_provenance": False,
            "missing_values": "omit",
        }
        result = project(canonical, config)
        assert "links" not in result
