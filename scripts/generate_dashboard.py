#!/usr/bin/env python3
"""
Generates a daily energy storage news/tech/policy briefing using the
Claude API with web search, and writes it out as JSON for the static
dashboard (docs/index.html) to render.

Requires env var: ANTHROPIC_API_KEY
"""

import os
import json
import datetime
from pathlib import Path

from anthropic import Anthropic
from json_repair import repair_json

MODEL = "claude-sonnet-5"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"
HISTORY_DIR = DATA_DIR / "history"
MANIFEST_PATH = DATA_DIR / "manifest.json"
LATEST_PATH = DATA_DIR / "latest.json"

PROMPT = """You are researching today's most significant energy storage \
industry developments using web search. Cover exactly three categories:

1. "Market & Deployment News" - projects, deals, capacity announcements, \
company/financial news
2. "Technology Developments" - new battery chemistries, R&D breakthroughs, \
manufacturing advances
3. "Regulatory & Policy" - government policy, FERC/state rules, incentives, \
tariffs, permitting

For each category, find 3-5 distinct, genuinely recent items (prioritize \
the last few days). For each item write:
- "title": short headline (under 12 words)
- "summary": 2-3 sentences IN YOUR OWN WORDS, no verbatim quotes from \
sources. Do not use any line breaks or double-quote characters inside \
string values - use single quotes if you need to quote something.
- "source_name": the publication name
- "source_url": the direct URL

Respond with ONLY valid JSON, no markdown code fences, no commentary, in \
exactly this structure:

{
  "date": "YYYY-MM-DD",
  "categories": [
    {
      "name": "Market & Deployment News",
      "items": [
        {"title": "...", "summary": "...", "source_name": "...", "source_url": "..."}
      ]
    },
    {"name": "Technology Developments", "items": [...]},
    {"name": "Regulatory & Policy", "items": [...]}
  ]
}
"""


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output:\n{text}")
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate, strict=False)
    except json.JSONDecodeError:
        repaired = repair_json(candidate)
        return json.loads(repaired, strict=False)


def main():
    api_key = os.environ["ANTHROPIC_API_KEY"]
    client = Anthropic(api_key=api_key)

    today = datetime.date.today().isoformat()

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": PROMPT}],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    raw_text = "\n".join(text_parts)
    data = extract_json(raw_text)
    data["date"] = data.get("date") or today
    data["generated_at_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    history_path = HISTORY_DIR / f"{data['date']}.json"
    history_path.write_text(json.dumps(data, indent=2))
    LATEST_PATH.write_text(json.dumps(data, indent=2))

    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
    else:
        manifest = {"dates": []}

    if data["date"] not in manifest["dates"]:
        manifest["dates"].insert(0, data["date"])
    manifest["dates"] = sorted(set(manifest["dates"]), reverse=True)[:60]
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    print(f"Wrote dashboard data for {data['date']}")


if __name__ == "__main__":
    main()
