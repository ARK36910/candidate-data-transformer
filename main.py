"""
Candidate Data Transformer — Entry Point

Usage:
  python main.py [--csv PATH] [--pdf PATH] [--config PATH] [--schema PATH]
                 [--out-canonical PATH] [--out-projected PATH]

Defaults:
  --csv           input/recruiter.csv
  --pdf           input/resume.pdf      (optional — skipped if file not found)
  --config        config/output_config.json
  --schema        config/schema.json
  --out-canonical output/canonical_output.json
  --out-projected output/projected_output.json
"""

import argparse
import sys
from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform recruiter CSV + resume PDF into a canonical candidate JSON."
    )
    parser.add_argument("--csv",           default="input/recruiter.csv",          help="Path to recruiter CSV")
    parser.add_argument("--pdf",           default="input/resume.pdf",             help="Path to resume PDF (optional)")
    parser.add_argument("--config",        default="config/output_config.json",    help="Path to output config")
    parser.add_argument("--schema",        default="config/schema.json",           help="Path to JSON schema")
    parser.add_argument("--out-canonical", default="output/canonical_output.json", help="Path for canonical output")
    parser.add_argument("--out-projected", default="output/projected_output.json", help="Path for projected output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        run_pipeline(
            csv_path=args.csv,
            pdf_path=args.pdf,           # pipeline handles missing file gracefully
            output_canonical=args.out_canonical,
            output_projected=args.out_projected,
            output_config_path=args.config,
            schema_path=args.schema,
        )
    except FileNotFoundError as exc:
        print(f"Error: Input file not found — {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
