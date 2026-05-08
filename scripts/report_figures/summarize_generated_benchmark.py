"""Summarize the generated Tracks benchmark used by the report and docs."""

from __future__ import annotations

import argparse
import json

from common import DIFFICULTIES, benchmark_summary, load_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize the generated Tracks benchmark CSV.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    # The summary keeps report numbers consistent with the benchmark CSV.
    summary = benchmark_summary(load_rows())
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    print(f"total_instances: {summary['total_instances']}")
    print(f"generated_instances: {summary['generated_instances']}")
    print(f"solved_instances: {summary['solved_instances']}")
    print(f"validated_instances: {summary['validated_instances']}")
    for difficulty in DIFFICULTIES:
        solve_time = summary["average_solve_time_by_difficulty"][difficulty]
        generation_time = summary["average_generation_time_by_difficulty"][difficulty]
        print(f"{difficulty.lower()}_average_solve_time_s: {solve_time:.6f}")
        print(f"{difficulty.lower()}_average_generation_time_ms: {generation_time:.6f}")
    print(f"hard_generation_min_ms: {summary['hard_generation_min_ms']:.6f}")
    print(f"hard_generation_max_ms: {summary['hard_generation_max_ms']:.6f}")


if __name__ == "__main__":
    main()
