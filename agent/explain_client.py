"""Call local llama-server (OpenAI-compatible) to explain PdM structured results.

Does NOT predict RUL. LLM only explains provided JSON.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path


SYSTEM_PROMPT = (
    "你是工业预测性维护助手。你不得重新计算或改写 RUL 数值。"
    "只根据给定 JSON 解释风险含义，并给出可执行的排查建议（3-6 条）。"
    "若信息不足，明确说明不确定性。使用简体中文。"
)


def build_user_prompt(payload: dict) -> str:
    return (
        "以下是端侧模型给出的结构化诊断结果（JSON）。"
        "请基于该结果给出维护解释与建议，不要编造传感器数值。\n\n"
        f"JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def chat(base_url: str, model: str, payload: dict, temperature: float = 0.3, max_tokens: int = 400) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(payload)},
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    p.add_argument("--model", default="qwen2.5-0.5b")
    p.add_argument("--json", type=Path, required=True, help="structured result json file")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    payload = json.loads(args.json.read_text(encoding="utf-8"))
    try:
        text = chat(args.base_url, args.model, payload)
    except urllib.error.URLError as e:
        raise SystemExit(f"Cannot reach llama-server at {args.base_url}: {e}") from e

    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
