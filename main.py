import json
import os
from glob import glob

from analysis.parser import parse_demo
from analysis.bad_peek import find_bad_peeks

DEMOS_DIR = "demos"
OUTPUT_DIR = "output"


def collect_demo_paths() -> list[str]:
    return sorted(glob(os.path.join(DEMOS_DIR, "*.dem")))


def output_path_for(demo_path: str) -> str:
    name = os.path.splitext(os.path.basename(demo_path))[0]
    return os.path.join(OUTPUT_DIR, f"{name}_bad_peeks.json")


def process_demo(demo_path: str) -> dict:
    print(f"\n--- {demo_path} ---")
    print("Parsing demo...")
    parsed = parse_demo(demo_path)

    print("Finding bad peeks...")
    bad_peeks = find_bad_peeks(parsed)

    summary = {
        "demoFile": os.path.basename(demo_path),
        "mapName": parsed["map_name"],
        "tickrate": parsed["tickrate"],
        "tickrateSource": parsed["tickrate_source"],
        "totalKills": len(parsed["kills"]),
        "suspiciousMoments": len(bad_peeks),
    }

    print(f"  map: {summary['mapName']}, kills: {summary['totalKills']}")
    print(f"  found {summary['suspiciousMoments']} suspicious moments")

    result = {"summary": summary, "moments": bad_peeks}

    out_path = output_path_for(demo_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  saved to {out_path}")
    return summary


def main() -> None:
    demo_paths = collect_demo_paths()
    if not demo_paths:
        raise FileNotFoundError(f"No .dem files found in '{DEMOS_DIR}/'.")

    os.makedirs(DEMOS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Processing {len(demo_paths)} demo(s)...")
    summaries = [process_demo(path) for path in demo_paths]

    total_moments = sum(s["suspiciousMoments"] for s in summaries)
    print(f"\nDone. {len(summaries)} demo(s), {total_moments} suspicious moment(s) total.")


if __name__ == "__main__":
    main()
