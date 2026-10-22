import json
import subprocess
from pathlib import Path

plan = json.loads(Path("broadcast-plan.json").read_text(encoding="utf-8"))
parts = [Path("rendered") / (part["id"] + ".mp4") for part in plan["segments"]]
for part in parts:
    if not part.is_file():
        raise FileNotFoundError(part)
Path("concat.txt").write_text("".join("file " + str(part.resolve()) + "\n" for part in parts), encoding="utf-8")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "parallel-demo.mp4"], check=True)
print("Assembled", len(parts), "segments")
