#!/usr/bin/env python3
"""
Evaluation harness for the Contextual Post Explainer.

This is intentionally lightweight:
- Runs 10+ fixed test posts.
- Checks for basic output shape: 3-5 bullets and at least one citation token like [S1].
- Checks that a handful of expected key facts appear somewhere in the explanation.

It does not attempt to do exact string matching of full bullets (LLMs are stochastic).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


RE_CITATION = re.compile(r"\\[S\\d+\\]")


def _load_cases(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    cases = data.get("cases", [])
    if not isinstance(cases, list) or len(cases) < 10:
        raise ValueError(f"Expected >= 10 cases in {path}, got {len(cases)}")
    return cases


def _normalize(s: str) -> str:
    return re.sub(r"\\s+", " ", (s or "").lower()).strip()


def _contains_all(text: str, needles: List[str]) -> Tuple[bool, List[str]]:
    missing = []
    t = _normalize(text)
    for n in needles:
        if _normalize(n) not in t:
            missing.append(n)
    return (len(missing) == 0, missing)


async def _run() -> int:
    # Ensure backend is importable.
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    sys.path.insert(0, str(backend_dir))

    from app.agents.post_explainer_agent import PostExplainerAgent  # noqa
    from app.config import settings  # noqa

    # Basic config sanity: we need *some* provider key.
    if not (settings.openai_api_key or settings.gemini_api_key):
        print("ERROR: No API key configured. Set OPENAI_API_KEY or GEMINI_API_KEY.")
        return 2

    cases_path = Path(__file__).resolve().parent / "test_posts.json"
    cases = _load_cases(cases_path)

    agent = PostExplainerAgent()
    await agent.initialize()

    failures: List[str] = []

    for case in cases:
        cid = case.get("id")
        post = case.get("post_content", "")
        expected = case.get("expected_contains", [])

        try:
            result = await agent.explain_post(post)
        except Exception as e:
            failures.append(f"{cid}: exception: {e}")
            continue

        bullets = result.get("explanation") or []
        text = "\n".join(bullets)

        if not (3 <= len(bullets) <= 5):
            failures.append(f"{cid}: expected 3-5 bullets, got {len(bullets)}")

        if not RE_CITATION.search(text):
            failures.append(f"{cid}: expected at least one [S#] citation token")

        ok, missing = _contains_all(text, expected)
        if not ok:
            failures.append(f"{cid}: missing expected facts: {missing}")

    total = len(cases)
    passed = total - len({f.split(':', 1)[0] for f in failures})

    print(f"Eval cases: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"- {f}")
        return 1

    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
