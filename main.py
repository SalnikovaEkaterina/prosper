from __future__ import annotations

import argparse
import json

from agent import run


def main() -> None:
    parser = argparse.ArgumentParser(description="PROSPER engineering agent demo")
    parser.add_argument("request", nargs="*", help="Инженерный запрос на русском")
    parser.add_argument("--offline", action="store_true", help="Не обращаться к LLM; использовать fallback-parser")
    parser.add_argument("--strict-llm", action="store_true", help="Не использовать fallback при ошибке LLM")
    args = parser.parse_args()

    request = " ".join(args.request).strip() if args.request else input("Инженерный запрос: ").strip()
    result = run(request, {"use_llm": not args.offline, "strict_llm": args.strict_llm})

    print("\n=== AGENT RESULT ===")
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    print("\nЖурнал: logs/llm_calls.jsonl и logs/agent_runs.jsonl; MCP: logs/mcp_calls.jsonl")


if __name__ == "__main__":
    main()
