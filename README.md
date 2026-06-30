# Candidate Data Transformer

A modular Python pipeline that ingests a **recruiter-supplied CSV** and a **resume PDF**, normalizes and merges the data into a canonical candidate record, and outputs both a full canonical JSON and a configurable projected JSON.

---

## Overview

Recruiters and applicants describe the same person in different formats. This tool bridges that gap by:

1. **Parsing** both sources into a shared `Candidate` model
2. **Normalizing** every field (phones → E.164, emails → lowercase, dates → YYYY-MM, skills → canonical names, countries → ISO codes, names → title case)
3. **Merging** the two records with an explicit policy (union for lists, structured source preference for scalars)
4. **Scoring confidence** per field and overall
5. **Tracking provenance** (which field came from which source and how)
6. **Projecting** the output to a custom shape via `output_config.json`
7. **Validating** the result against `schema.json`

---

## Architecture

```text
input/recruiter.csv ──┐
                      ├──► Parse ──► Normalize ──► Merge ──► Confidence
input/resume.pdf ─────┘                                           │
                                                                  ▼
                                                             Provenance
                                                                  │
                                                                  ▼
                                                            Projection
                                                                  │
                                                                  ▼
                                                            Validation
                                                                  │
                                              ┌───────────────────┘
                                              ▼                   ▼
                               output/canonical_output.json   output/projected_output.json
```

### Module map

| Module | Responsibility |
|---|---|
| `src/parsers/csv_parser.py` | Read recruiter CSV → `Candidate` |
| `src/parsers/pdf_parser.py` | Read resume PDF with regex heuristics → `Candidate` |
| `src/normalizers/phone.py` | Raw phone → E.164 (`+919876543210`) |
| `src/normalizers/email.py` | Raw email → lowercase, stripped |
| `src/normalizers/date.py` | Human dates → `YYYY-MM` |
| `src/normalizers/country.py` | Country name → ISO 3166-1 alpha-2 |
| `src/normalizers/skill.py` | Aliases & abbreviations → canonical skill names |
| `src/normalizers/name.py` | Raw name → title-cased, trimmed |
| `src/merge/merger.py` | Merge CSV + PDF candidates |
| `src/confidence/confidence.py` | Assign per-field and overall confidence score |
| `src/provenance/provenance.py` | Finalize provenance records |
| `src/projection/projector.py` | Apply `output_config.json` to produce projected output |
| `src/validation/validator.py` | Validate output against `schema.json` |
| `src/pipeline.py` | Orchestrate all stages |
| `main.py` | CLI entry point |

---

## Installation

```bash
# Clone / unzip the project
cd candidate-data-transformer

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Libraries used

| Library | Purpose |
|---|---|
| `pandas` | Read and parse recruiter CSV |
| `pydantic` | Typed `Candidate` data model with validation |
| `phonenumbers` | Parse and format phone numbers to E.164 |
| `python-dateutil` | Flexible date parsing (`January 2023`, `03/2020`, …) |
| `PyPDF2` | Extract text from resume PDFs |
| `jsonschema` | Validate final output against JSON Schema |
| `rapidfuzz` | Fuzzy-match skill names to canonical list |

---

## Folder structure

```text
candidate-data-transformer/
├── README.md
├── requirements.txt
├── main.py
├── input/
│   ├── recruiter.csv        ← sample recruiter CSV
│   └── resume.pdf           ← place your resume PDF here
├── output/
│   ├── canonical_output.json
│   └── projected_output.json
├── config/
│   ├── output_config.json   ← controls which fields appear in projected output
│   └── schema.json          ← JSON Schema for validation
├── src/
│   ├── models.py
│   ├── pipeline.py
│   ├── parsers/
│   ├── normalizers/
│   ├── merge/
│   ├── confidence/
│   ├── provenance/
│   ├── projection/
│   └── validation/
└── tests/
    ├── test_normalization.py
    ├── test_merge.py
    └── test_projection.py
```

---

## Example command

```bash
# Run with defaults (reads input/, writes to output/)
python main.py

# Custom paths
python main.py \
  --csv   path/to/recruiter.csv \
  --pdf   path/to/resume.pdf \
  --config  config/output_config.json \
  --schema  config/schema.json \
  --out-canonical output/canonical_output.json \
  --out-projected output/projected_output.json
```

---

## Sample output

### canonical_output.json (excerpt)

```json
{
  "candidate_id": "a1b2c3d4-...",
  "full_name": "Ananya Roy",
  "emails": ["ananya.roy@gmail.com"],
  "phones": ["+919876543210"],
  "location": {
    "city": "Bengaluru, Karnataka",
    "state": null,
    "country": "IN"
  },
  "headline": "Senior Data Scientist",
  "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Pandas"],
  "experience": [
    {
      "title": "ML Engineer",
      "company": "Acme Corp",
      "start": "2021-01",
      "end": "present",
      "description": null
    }
  ],
  "education": [
    {
      "degree": "B.Tech Computer Science",
      "institution": "IIT Delhi",
      "start": "2015-07",
      "end": "2019-05"
    }
  ],
  "links": [
    "https://linkedin.com/in/ananya-roy",
    "https://github.com/ananya-roy"
  ],
  "overall_confidence": 0.893,
  "provenance": [
    { "field": "full_name", "source": "recruiter.csv", "method": "csv_column" },
    { "field": "phones",    "source": "resume.pdf",    "method": "regex" }
  ]
}
```

### projected_output.json (with default config)

```json
{
  "candidate_id": "a1b2c3d4-...",
  "full_name": "Ananya Roy",
  "emails": ["ananya.roy@gmail.com"],
  "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Pandas"],
  "overall_confidence": 0.893
}
```

---

## Configuring the projection

Edit `config/output_config.json`:

```json
{
  "fields": ["full_name", "emails", "skills"],
  "rename": { "full_name": "name" },
  "include_confidence": true,
  "include_provenance": false,
  "missing_values": "null"
}
```

| Key | Values | Effect |
|---|---|---|
| `fields` | list of field names | Only these fields appear in the projected output. Omit the key to include all. |
| `rename` | `{ "original": "new_name" }` | Rename fields in the output |
| `include_confidence` | `true` / `false` | Include `overall_confidence` |
| `include_provenance` | `true` / `false` | Include `provenance` array |
| `missing_values` | `"null"` / `"omit"` | Keep missing fields as `null` or drop them entirely |

---

## Running tests

```bash
pytest tests/ -v
```

---

## Assumptions

- The recruiter CSV has **one row per candidate**. Only the first data row is processed.
- CSV column headers are flexible — common synonyms (`email` / `emails`, `phone` / `mobile`, `name` / `full_name`, etc.) are all recognized automatically.
- The PDF parser uses **regex heuristics**, not an ML model. Unusual resume formats may not parse perfectly; the canonical output will still be valid — just less complete.
- Phone numbers without an explicit country code are assumed to be **Indian (+91)**. Pass a different `default_region` inside `normalise_phone()` to change this.
- The confidence score is a **heuristic estimate**, not a statistically calibrated probability.
- A valid candidate must have at least a `candidate_id`, a `full_name`, and at least one `email` — these are the `required` fields in `schema.json`.
