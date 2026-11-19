"""通过兼容服务测试指定模型，保存 Instruction/Reasoning/Output/Expression。"""

import argparse
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SYSTEM_PROMPT = BASE_DIR / "qwen3_shared_system_prompt.txt"
RELEASE = BASE_DIR.parents[1]
sys.path.insert(0, str(BASE_DIR.parent))


def split_model_output(message):
    """缺少 reasoning 字段时留空；兼容不同字段及正文中的 <think>。"""
    content = (message.content or "").strip()
    reasoning = (
        getattr(message, "reasoning_content", None)
        or getattr(message, "reasoning", None)
        or ""
    )
    think_blocks = re.findall(r"<think>(.*?)</think>", content, flags=re.DOTALL)
    if think_blocks:
        if not reasoning:
            reasoning = "\n".join(block.strip() for block in think_blocks)
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    # 仅去除完整包裹正文的 Markdown 代码围栏，不修补 XML 标签。
    fence = chr(96) * 3
    fenced = re.fullmatch(
        rf"{fence}(?:xml)?\s*\n?(.*?)\n?{fence}",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        content = fenced.group(1).strip()
    return str(reasoning).strip(), content


def convert_expression(content, converter):
    """分别记录 XML 解析错误和表达式转换错误。"""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return "无法解析的XML", f"XML 解析失败：{exc}"
    if root.tag not in {"ju", "jbw"}:
        return "无法解析的XML", f"XML 根标签应为 ju 或 jbw，实际为 {root.tag!r}"
    try:
        return converter.to_linear_expr(root), None
    except Exception as exc:
        return "表达式转换失败", f"{type(exc).__name__}: {exc}"


def write_record(handle, instruction, reasoning, output, expression):
    handle.write(
        f"Instruction:{instruction}\nReasoning:{reasoning}\n"
        f"Output:{output}\nExpression:{expression}\n\n\n"
    )
    handle.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=BASE_DIR / "sentences.txt")
    parser.add_argument("--system-prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--output", type=Path, default=RELEASE / "reproduced" / "inference" / "qwen25_results.txt")
    parser.add_argument("--base-url", default=os.getenv("VLLM_BASE_URL"))
    parser.add_argument("--model", default="qwen25-ft")
    parser.add_argument("--max-tokens", type=int, default=3072)
    parser.add_argument("--limit", type=int, help="只测试前 N 个非空行，例如 --limit 5")
    parser.add_argument("--overwrite", action="store_true", help="明确允许覆盖指定的结果文件")
    args = parser.parse_args(argv)
    if not args.base_url or not os.getenv("VLLM_API_KEY"):
        parser.error("Set VLLM_BASE_URL and VLLM_API_KEY for your model service; use an explicit placeholder key only if your service is unauthenticated.")
    if args.max_tokens < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--max-tokens 和 --limit 必须是正整数")
    if args.output.resolve() in {args.input.resolve(), args.system_prompt.resolve()}:
        parser.error("输出文件不能与输入或系统提示词文件相同")
    if args.output.exists() and not args.overwrite:
        parser.error(f"结果文件已存在：{args.output}。请换 --output，或明确使用 --overwrite。")

    try:
        system_prompt = args.system_prompt.read_text(encoding="utf-8-sig").strip()
    except OSError as exc:
        parser.error(f"读取系统提示词失败：{exc}")
    if not system_prompt:
        parser.error("系统提示词不能为空")

    try:
        from openai import APIError, OpenAI
        from tqdm import tqdm
        from sps_converter import LinearExpr
    except ImportError as exc:
        print(f"缺少测试依赖：{exc}。请先运行 python -m pip install -r requirements.txt", file=sys.stderr)
        return 1

    try:
        sentences = [
            (line_no, line.strip())
            for line_no, line in enumerate(args.input.read_text(encoding="utf-8-sig").splitlines(), 1)
            if line.strip()
        ]
    except OSError as exc:
        print(f"读取输入失败：{exc}", file=sys.stderr)
        return 1
    if args.limit is not None:
        sentences = sentences[:args.limit]
    if not sentences:
        print("输入文件没有可测试的句子。", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    converter = LinearExpr()
    completed = converted = truncated = 0
    try:
        with OpenAI(
            api_key=os.environ["VLLM_API_KEY"],
            base_url=args.base_url,
            timeout=600.0,
            max_retries=2,
        ) as client:
            available_models = [model.id for model in client.models.list().data]
            if args.model not in available_models:
                print(f"服务中没有模型 {args.model!r}；可用模型：{available_models}。请确认 LoRA 已加载。", file=sys.stderr)
                return 1

            # 默认新建，防止重复追加或意外覆盖参考结果；每条完成后立即落盘。
            with args.output.open("w" if args.overwrite else "x", encoding="utf-8", newline="\n") as handle:
                for line_no, sentence in tqdm(sentences, desc="测试句本位模型", unit="句"):
                    instruction = f"给出句子“{sentence}”的句本位标注结果。"
                    try:
                        result = client.chat.completions.create(
                            model=args.model,
                            messages=[{"role": "system", "content": system_prompt},
                                      {"role": "user", "content": instruction}],
                            temperature=0.0,
                            top_p=1.0,
                            max_tokens=args.max_tokens,
                            extra_body={"repetition_penalty": 1.0, "top_k": -1},
                        )
                    except APIError as exc:
                        print(f"\n输入第 {line_no} 行请求失败：{exc}", file=sys.stderr)
                        print(f"已保留前 {completed} 条结果：{args.output}", file=sys.stderr)
                        return 1
                    if not result.choices:
                        print(f"\n输入第 {line_no} 行返回了空 choices；已保留前 {completed} 条结果。", file=sys.stderr)
                        return 1

                    choice = result.choices[0]
                    reasoning, content = split_model_output(choice.message)
                    if choice.finish_reason == "length":
                        truncated += 1
                        expression = "输出被截断，无法完整评估"
                        error = "达到生成或上下文长度上限；原始正文已保存到 Output"
                    else:
                        expression, error = convert_expression(content, converter)
                        if error is None:
                            converted += 1
                    if error:
                        tqdm.write(f"输入第 {line_no} 行：{error}", file=sys.stderr)
                    write_record(handle, instruction, reasoning, content, expression)
                    completed += 1
    except APIError as exc:
        print(f"无法连接或读取模型服务 {args.base_url}：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"文件操作失败：{exc}", file=sys.stderr)
        return 1

    print(f"完成 {completed} 句；XML 及表达式转换成功 {converted} 句；输出截断 {truncated} 句。")
    print(f"结果：{args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
