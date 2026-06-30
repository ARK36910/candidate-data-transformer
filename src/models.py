"""
Canonical data model for the candidate data transformer pipeline.
Every module reads from and writes to these models.
"""

from __future__ import annotations
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import uuid


class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None  # ISO 3166-1 alpha-2 code after normalization


class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None   # YYYY-MM after normalization
    end: Optional[str] = None     # YYYY-MM or "present"
    description: Optional[str] = None


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start: Optional[str] = None   # YYYY-MM after normalization
    end: Optional[str] = None     # YYYY-MM after normalization


class ProvenanceEntry(BaseModel):
    field: str
    source: str    # e.g. "recruiter.csv", "resume.pdf"
    method: str    # e.g. "csv_column", "regex", "pdf_heuristic"


class Candidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[Location] = None
    headline: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    provenance: List[ProvenanceEntry] = Field(default_factory=list)
    overall_confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
