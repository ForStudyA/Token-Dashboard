#!/usr/bin/env python3
"""Test script to verify the Claude Code JSONL parser works against real data.

Run:  .venv/Scripts/python test_parser.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(name)s:%(message)s",
)

from hermes_token_dash.parser_claude import (  # noqa: E402
    aggregate_by_model_date,
    get_available_models,
    parse_jsonl,
    scan_claude_jsonls,
)


def main():
    print("--- Scanning JSONL files ---")
    files = scan_claude_jsonls()
    print(f"  Found {len(files)} files")

    print("--- Parsing all JSONL files ---")
    all_records = []
    for f in files:
        all_records.extend(parse_jsonl(f))
    print(f"  Deduplicated records: {len(all_records)}")

    if not all_records:
        print("No records found.")
        return

    models = get_available_models(all_records)
    print(f"  Models: {models}")

    for tf in ("all", "today", "7d", "30d"):
        print(f"\n--- {tf.upper()} ---")
        stats = aggregate_by_model_date(all_records, tf)
        if not stats:
            print("  No data")
            continue

        total_in = sum(s.total_input for s in stats)
        total_out = sum(s.total_output for s in stats)
        total_req = sum(s.request_count for s in stats)
        total_cost = sum(s.estimated_cost for s in stats)

        print(f"  Total: {total_in:,} in + {total_out:,} out tokens")
        print(f"  Requests: {total_req}, Est. cost: ${total_cost:.4f}")

        for s in stats:
            print(
                f"  {s.model:22s} {s.date:12s}  "
                f"in={s.total_input:>10,}  out={s.total_output:>9,}  "
                f"reqs={s.request_count:>4}  hit={s.cache_hit_rate:.1f}%  "
                f"${s.estimated_cost:.4f}"
            )

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
