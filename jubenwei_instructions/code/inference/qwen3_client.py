"""通过兼容服务测试指定 Qwen3 模型，加载共享提示词并切换思考模式。"""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
RELEASE = BASE.parents[1]
sys.path.insert(0, str(BASE.parent))


def split_output(message):
    content = str(message.get('content') or '').strip()
    reasoning = str(message.get('reasoning_content') or message.get('reasoning') or '').strip()
    if content.startswith('<think>'):
        if '</think>' in content:
            thought, content = content[len('<think>'):].split('</think>', 1)
            reasoning = reasoning or thought.strip()
            content = content.strip()
        else:
            return reasoning or content[len('<think>'):].strip(), ''
    elif '</think>' in content and not content.startswith('<ju'):
        # 部分服务不返回由模板提供的起始 <think>，但保留结束标记。
        thought, content = content.split('</think>', 1)
        reasoning = reasoning or thought.strip()
        content = content.strip()
    fence = chr(96) * 3
    wrapped = re.fullmatch(rf'{fence}(?:xml)?\s*\n?(.*?)\n?{fence}', content,
                           flags=re.DOTALL | re.IGNORECASE)
    if wrapped:
        content = wrapped.group(1).strip()
    return reasoning, content


def expression_for(content, converter):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return '无法解析的XML', str(exc), None
    try:
        return converter.to_linear_expr(root), None, None
    except Exception as exc:
        return '表达式转换失败', None, f'{type(exc).__name__}: {exc}'


def field_text(text):
    # 防止模型正文续行中的字段名被评测读取器误当成下一条记录。
    # 原始内容完整保存在 JSONL；TXT 仅对保留字段起始的续行加一个空格。
    lines = text.splitlines()
    names = ('Instruction:', 'Reasoning:', 'Output:', 'Expression:')
    return '\n'.join((' ' + line if i and line.startswith(names) else line)
                     for i, line in enumerate(lines))


def write_record(handle, instruction, reasoning, output, expression):
    handle.write(f'Instruction:{instruction}\nReasoning:{field_text(reasoning)}\n'
                 f'Output:{field_text(output)}\nExpression:{field_text(expression)}\n\n')
    handle.flush()


def request_args(args, system_prompt, instruction, index):
    return {
        'model': args.model,
        'messages': [{'role': 'system', 'content': system_prompt},
                     {'role': 'user', 'content': instruction}],
        'temperature': args.temperature, 'top_p': args.top_p,
        'max_tokens': args.max_tokens, 'seed': args.seed + index,
        'extra_body': {
            'chat_template_kwargs': {'enable_thinking': args.thinking == 'on'},
            'top_k': args.top_k, 'min_p': 0.0, 'repetition_penalty': 1.0,
        },
    }


def save_metadata(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BASE / 'sentences.txt')
    parser.add_argument('--system-prompt', type=Path, default=BASE / 'qwen3_shared_system_prompt.txt')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--base-url', default=os.getenv('VLLM_BASE_URL'))
    parser.add_argument('--model', default='qwen3-base')
    parser.add_argument('--thinking', choices=['on', 'off'], default='on')
    parser.add_argument('--temperature', type=float, default=0.6)
    parser.add_argument('--top-p', type=float, default=0.95)
    parser.add_argument('--top-k', type=int, default=20)
    parser.add_argument('--max-tokens', type=int, default=8192)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--limit', type=int, help='仅测试前 N 条；未提供时必须有完整 1200 条')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    if not args.base_url or not os.getenv("VLLM_API_KEY"):
        parser.error("Set VLLM_BASE_URL and VLLM_API_KEY for your model service; use an explicit placeholder key only if your service is unauthenticated.")
    if args.max_tokens < 1 or (args.limit is not None and args.limit < 1):
        parser.error('--max-tokens 和 --limit 必须为正整数')
    if not 0 <= args.temperature <= 2 or not 0 < args.top_p <= 1 or (args.top_k != -1 and args.top_k < 1):
        parser.error('temperature 应在 [0,2]，top-p 应在 (0,1]，top-k 应为 -1 或正整数')
    args.output = (args.output or RELEASE / 'reproduced' / 'inference' / f'qwen3_thinking_{args.thinking}.txt').resolve()
    raw_path = args.output.with_suffix('.raw.jsonl')
    meta_path = args.output.with_suffix('.meta.json')
    outputs = [args.output, raw_path, meta_path]
    inputs = {args.input.resolve(), args.system_prompt.resolve()}
    if len(set(outputs)) != 3 or any(path in inputs for path in outputs):
        parser.error('输入、结果、原始响应日志和元数据文件路径必须互不相同')
    if any(path.exists() for path in outputs) and not args.overwrite:
        parser.error('输出文件已存在；换一个 --output，或明确使用 --overwrite')
    system_prompt = args.system_prompt.read_text(encoding='utf-8-sig').strip()
    sentences = [line.strip() for line in args.input.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if not system_prompt:
        parser.error('系统提示词不能为空')
    if args.limit is None and len(sentences) != 1200:
        parser.error(f'完整测试应为 1200 条，实际为 {len(sentences)}；冒烟测试请使用 --limit')
    if args.limit is not None:
        sentences = sentences[:args.limit]
    if not sentences:
        parser.error('输入文件没有句子')
    try:
        from openai import APIError, OpenAI
        from tqdm import tqdm
        from sps_converter import LinearExpr
    except ImportError as exc:
        print(f'缺少依赖：{exc}；请安装 requirements.txt。', file=sys.stderr)
        return 1
    packages = {}
    for name in ['openai', 'tqdm']:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = 'unknown'
    meta = {
        'status': 'starting', 'planned': len(sentences), 'completed': 0,
        'xml_parse_failures': 0, 'conversion_failures': 0, 'truncated': 0,
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'client_packages': packages,
        'input_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'system_prompt_sha256': hashlib.sha256(args.system_prompt.read_bytes()).hexdigest(),
        'system_prompt_file': str(args.system_prompt.resolve()),
        'settings': {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        'seed_policy': 'request seed = seed + zero-based test index',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with OpenAI(base_url=args.base_url, api_key=os.environ['VLLM_API_KEY'],
                    timeout=600.0, max_retries=2) as client:
            models = client.models.list().model_dump()
            ids = [item['id'] for item in models['data']]
            if args.model not in ids:
                raise ValueError(f'服务没有模型 {args.model!r}；可用模型：{ids}')
            meta['server_models'] = models
            meta['status'] = 'running'
            save_metadata(meta_path, meta)
            converter = LinearExpr()
            mode = 'w' if args.overwrite else 'x'
            with args.output.open(mode, encoding='utf-8', newline='\n') as output, raw_path.open(mode, encoding='utf-8', newline='\n') as raw:
                for index, sentence in enumerate(tqdm(sentences, desc=f'Qwen3 {args.model} / thinking={args.thinking}', unit='句')):
                    instruction = f'给出句子“{sentence}”的句本位标注结果。'
                    response = client.chat.completions.create(**request_args(args, system_prompt, instruction, index))
                    payload = response.model_dump()
                    # 原始响应先落盘，包括 finish_reason 与 token 使用信息。
                    raw.write(json.dumps({'row_1based': index + 1, 'instruction': instruction,
                                          'response': payload}, ensure_ascii=False) + '\n')
                    raw.flush()
                    if not payload.get('choices'):
                        raise ValueError(f'第 {index + 1} 条返回空 choices；本次运行未完成')
                    choice = payload['choices'][0]
                    reasoning, content = split_output(choice['message'])
                    expression, parse_error, conversion_error = expression_for(content, converter)
                    # 无论 XML 是否可解析、是否截断，每个成功返回的请求均保留一条记录。
                    write_record(output, instruction, reasoning, content, expression)
                    meta['completed'] += 1
                    meta['xml_parse_failures'] += parse_error is not None
                    meta['conversion_failures'] += conversion_error is not None
                    meta['truncated'] += choice.get('finish_reason') == 'length'
                    save_metadata(meta_path, meta)
            meta['status'] = 'complete'
            meta['output_sha256'] = hashlib.sha256(args.output.read_bytes()).hexdigest()
            meta['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
            save_metadata(meta_path, meta)
    except (APIError, OSError, ValueError, KeyboardInterrupt) as exc:
        meta['status'] = 'incomplete'
        meta['error'] = f'{type(exc).__name__}: {exc}'
        save_metadata(meta_path, meta)
        print(f'运行未完成：{exc}\n只完成 {meta["completed"]}/{meta["planned"]} 条；不能将剩余未执行记录当成 XML 失败。', file=sys.stderr)
        return 1
    print(f'完成 {meta["completed"]}/{meta["planned"]} 条；XML 失败 {meta["xml_parse_failures"]} 条；'
          f'转换失败 {meta["conversion_failures"]} 条；截断 {meta["truncated"]} 条。')
    print(f'结果：{args.output}\n原始响应：{raw_path}\n运行配置：{meta_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
