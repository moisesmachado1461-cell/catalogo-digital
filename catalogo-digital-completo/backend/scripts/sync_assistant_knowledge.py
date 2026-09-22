from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "backend" / "app" / "assistant_knowledge.json"
TARGET = REPO_ROOT / "frontend" / "js" / "assistant-knowledge.js"


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    content = (
        "(function () {\n"
        "  'use strict';\n\n"
        "  // Arquivo gerado a partir de backend/app/assistant_knowledge.json.\n"
        "  // Edite a fonte JSON e execute backend/scripts/sync_assistant_knowledge.py.\n"
        f"  window.CatalogoAssistantKnowledge = {payload};\n"
        "})();\n"
    )
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding="utf-8")
    print(f"Base do assistente sincronizada: {data.get('version')} · {len(data.get('entries', []))} tópicos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
