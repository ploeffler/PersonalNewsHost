"""Review pending model-level evidence without external calls."""
import json
from pathlib import Path

from scripts.model_residency import validate_candidate


def report(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for candidate in data["candidates"]:
        result = validate_candidate(candidate, set())
        rows.append({"id": candidate["id"], "missing": result["missing"], "approved": False})
    return {"method": "offline", "candidates": rows}


if __name__ == "__main__":
    print(json.dumps(report(Path(__file__).resolve().parents[1] / "docs/provider-research.json"), indent=2))
