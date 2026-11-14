"""Bake demo_data.json into demo.template.html -> demo.html. Run after simulate_month.py."""
import json
from pathlib import Path

HERE = Path(__file__).parent
data = json.dumps(json.loads((HERE / "demo_data.json").read_text()), ensure_ascii=False).replace("</", "<\\/")
(HERE / "demo.html").write_text((HERE / "demo.template.html").read_text().replace("__DATA__", data))
print("wrote demo.html")
