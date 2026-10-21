"""Daily run: Scout -> Verifier -> Publisher. Writes site/data/deals.json."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from agents import publisher, scout, verifier
from agents.schemas import PublisherReport, ScoutReport, VerifierReport

RUNS_DIR = Path(__file__).resolve().parent / "runs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-run", type=Path, help="Publish from a runs/<stamp> directory holding scout.json, verifier.json and optionally publisher.json, without calling the API")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    report = None
    if args.from_run:
        # publisher.json is optional: when present (e.g. written by the Claude Code
        # deal-publisher subagent) it is used instead of calling the API.
        report_path = args.from_run / "publisher.json"
        if report_path.exists():
            report = PublisherReport.model_validate_json(report_path.read_text())
        found = ScoutReport.model_validate_json((args.from_run / "scout.json").read_text())
        checked = VerifierReport.model_validate_json((args.from_run / "verifier.json").read_text())
    else:
        run_dir = RUNS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir.mkdir(parents=True)

        seen = list(publisher._load_previous())
        found = scout.run(seen, list(publisher.load_rejected()))
        (run_dir / "scout.json").write_text(found.model_dump_json(indent=2))
        logging.info("Scout found %d candidates", len(found.candidates))

        checked = verifier.run(found.candidates) if found.candidates else VerifierReport(verifications=[])
        (run_dir / "verifier.json").write_text(checked.model_dump_json(indent=2))

    rejected = sum(v.verdict == "rejected" for v in checked.verifications)
    payload = publisher.run(found.candidates, checked.verifications, rejected, report)
    logging.info("Published %d deals: %s", len(payload["deals"]), json.dumps(payload["stats"]))


if __name__ == "__main__":
    main()
