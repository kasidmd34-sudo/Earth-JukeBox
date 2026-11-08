"""Generate evaluation audit report across all applicable modules and save artifacts."""
import asyncio
import json
import os
import sys

# Ensure repository root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.evaluation_service import EvaluationService
from app.config import settings


async def main():
    os.makedirs(settings.EVALUATION_DIR, exist_ok=True)
    report = {}
    print("=======================================================")
    print("Evaluating Earth Jukebox Models Against Baselines...")
    print("=======================================================")

    for cat in ["temperature", "rain", "wind"]:
        print(f"\nEvaluating {cat.upper()}...")
        try:
            res = await EvaluationService.evaluate_module(cat)
            report[cat] = res
            print(f"  Validation Method: {res.get('validation_method')}")
            print(f"  Metrics: {res.get('metrics')}")
            print(f"  Beats Seasonal Baseline: {res.get('beats_baseline')}")
        except Exception as e:
            report[cat] = {"status": "error", "message": str(e)}
            print(f"  Error: {e}")

    out_file = os.path.join(settings.EVALUATION_DIR, "evaluation_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=======================================================")
    print(f"Saved evaluation artifact to {out_file}")
    print("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())
