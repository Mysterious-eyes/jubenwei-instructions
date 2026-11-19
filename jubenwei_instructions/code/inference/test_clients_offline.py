"""不连接模型服务的接口与输出格式检查。"""

import os
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import qwen3_client as runner
import qwen25_client as runner25

XML = '<ju><xj><sbj><r>我</r></sbj><prd scp="VO"><v>买</v></prd><obj><n>书</n></obj></xj></ju>'


class FakeAPIError(Exception):
    pass


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def model_dump(self):
        return self.data


def response(content, finish='stop', **extra):
    return FakeResponse({'choices': [{'message': {'content': content, **extra},
                                      'finish_reason': finish}], 'usage': {'completion_tokens': 10}})


class OfflineTests(unittest.TestCase):
    def invoke(self, directory, responses, thinking='on', output='result.txt', system_prompt='共享系统规则'):
        directory = Path(directory).resolve()
        self.assertTrue(directory.is_relative_to(runner.BASE))
        (directory / 'input.txt').write_text('我买书\n我买书\n', encoding='utf-8')
        if system_prompt is not None:
            (directory / 'prompt.txt').write_text(system_prompt, encoding='utf-8')
        calls = []
        pending = iter(responses)

        class Client:
            def __init__(self, **kwargs):
                self.models = SimpleNamespace(list=lambda: FakeResponse({'data': [{'id': 'qwen3-base'}]}))
                self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

            def create(self, **kwargs):
                calls.append(kwargs)
                value = next(pending)
                if isinstance(value, Exception):
                    raise value
                return value

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        sdk = ModuleType('openai')
        sdk.OpenAI, sdk.APIError = Client, FakeAPIError
        progress = ModuleType('tqdm')
        progress.tqdm = lambda items, **kwargs: items
        args = ['--input', str(directory / 'input.txt'), '--output', str(directory / output),
                '--limit', '2', '--thinking', thinking]
        if system_prompt is not None:
            args += ['--system-prompt', str(directory / 'prompt.txt')]
        with patch.dict(os.environ, {'VLLM_BASE_URL': 'http://offline.invalid/v1', 'VLLM_API_KEY': 'offline-test-placeholder'}), patch.dict(sys.modules, {'openai': sdk, 'tqdm': progress}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = runner.main(args)
        return code, calls

    def test_default_shared_prompt_is_sent_unchanged(self):
        expected = runner25.DEFAULT_SYSTEM_PROMPT.read_text(encoding='utf-8-sig').strip()
        for thinking in ['on', 'off']:
            with self.subTest(thinking=thinking), tempfile.TemporaryDirectory(dir=runner.BASE, prefix='.offline_') as temp:
                code, calls = self.invoke(temp, [response(XML), response(XML)], thinking, system_prompt=None)
                self.assertEqual(code, 0)
                self.assertEqual(calls[0]['messages'][0], {'role': 'system', 'content': expected})

    def test_system_prompt_switch_and_all_returned_records_preserved(self):
        for thinking in ['on', 'off']:
            with self.subTest(thinking=thinking), tempfile.TemporaryDirectory(dir=runner.BASE, prefix='.offline_') as temp:
                code, calls = self.invoke(temp, [response(XML, reasoning_content='分析'), response('<ju>', 'length')], thinking)
                self.assertEqual(code, 0)
                self.assertEqual(calls[0]['messages'][0], {'role': 'system', 'content': '共享系统规则'})
                self.assertEqual(calls[0]['extra_body']['chat_template_kwargs']['enable_thinking'], thinking == 'on')
                self.assertEqual(calls[1]['seed'], calls[0]['seed'] + 1)
                root = Path(temp)
                output = (root / 'result.txt').read_text(encoding='utf-8')
                self.assertEqual(output.count('Instruction:'), 2)
                self.assertIn('Output:<ju>\nExpression:无法解析的XML', output)
                meta = json.loads((root / 'result.meta.json').read_text(encoding='utf-8'))
                self.assertEqual((meta['status'], meta['completed'], meta['xml_parse_failures'], meta['truncated']), ('complete', 2, 1, 1))
                self.assertEqual(len((root / 'result.raw.jsonl').read_text(encoding='utf-8').splitlines()), 2)

    def test_network_failure_does_not_fabricate_remaining_records(self):
        with tempfile.TemporaryDirectory(dir=runner.BASE, prefix='.offline_') as temp:
            code, calls = self.invoke(temp, [response(XML), FakeAPIError('network failure')])
            self.assertEqual(code, 1)
            root = Path(temp)
            self.assertEqual((root / 'result.txt').read_text(encoding='utf-8').count('Instruction:'), 1)
            meta = json.loads((root / 'result.meta.json').read_text(encoding='utf-8'))
            self.assertEqual((meta['status'], meta['planned'], meta['completed']), ('incomplete', 2, 1))

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=runner.BASE, prefix='.offline_') as temp:
            path = Path(temp) / 'result.txt'
            path.write_text('keep', encoding='utf-8')
            with self.assertRaises(SystemExit):
                self.invoke(temp, [])
            self.assertEqual(path.read_text(encoding='utf-8'), 'keep')

    def test_reasoning_separation_and_fences(self):
        fence = chr(96) * 3
        for content in [f'<think>分析</think>{fence}xml\n{XML}\n{fence}', f'分析</think>{XML}']:
            self.assertEqual(runner.split_output({'content': content}), ('分析', XML))
        self.assertEqual(runner.split_output({'content': '<think>没有结束'}), ('没有结束', ''))
        self.assertEqual(runner.split_output({'content': XML, 'reasoning': '独立分析'}), ('独立分析', XML))

    def test_reserved_field_on_continuation_line(self):
        self.assertEqual(runner.field_text('第一行\nInstruction:模型复述'), '第一行\n Instruction:模型复述')


class Qwen25OfflineTests(unittest.TestCase):
    def test_reasoning_and_public_conversion(self):
        from sps_converter import LinearExpr
        thought, final = runner25.split_model_output(SimpleNamespace(content='<think>分析</think>' + XML))
        self.assertEqual((thought, final), ('分析', XML))
        expression, error = runner25.convert_expression(final, LinearExpr())
        self.assertIsNone(error)
        self.assertTrue(expression)
        self.assertEqual(runner25.convert_expression('<ju>', LinearExpr())[0], '无法解析的XML')

    def test_mock_request_and_four_field_output(self):
        calls = []
        class Client:
            def __init__(self, **kwargs):
                self.models = SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id='custom-model')]))
                self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
            def create(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=XML), finish_reason='stop')])
            def __enter__(self): return self
            def __exit__(self, *args): return False
        sdk = ModuleType('openai'); sdk.OpenAI, sdk.APIError = Client, FakeAPIError
        progress = ModuleType('tqdm'); progress.tqdm = lambda items, **kwargs: items
        with tempfile.TemporaryDirectory(dir=runner.BASE, prefix='.offline_') as temp:
            directory = Path(temp); (directory / 'input.txt').write_text('我买书', encoding='utf-8')
            output = directory / 'nested' / 'result.txt'
            args = ['--input', str(directory / 'input.txt'), '--output', str(output), '--model', 'custom-model']
            with patch.dict(os.environ, {'VLLM_BASE_URL':'http://offline.invalid/v1','VLLM_API_KEY':'offline-test-placeholder'}), patch.dict(sys.modules, {'openai':sdk,'tqdm':progress}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(runner25.main(args), 0)
                with self.assertRaises(SystemExit): runner25.main(args)
            self.assertEqual(calls[0]['model'], 'custom-model')
            self.assertEqual(calls[0]['messages'], [
                {'role': 'system', 'content': runner25.DEFAULT_SYSTEM_PROMPT.read_text(encoding='utf-8-sig').strip()},
                {'role': 'user', 'content': '给出句子“我买书”的句本位标注结果。'},
            ])
            self.assertEqual((calls[0]['temperature'], calls[0]['top_p'], calls[0]['max_tokens']), (0.0, 1.0, 3072))
            self.assertEqual(output.read_text(encoding='utf-8').count('Instruction:'), 1)
            self.assertIn('Output:' + XML, output.read_text(encoding='utf-8'))

    def test_empty_prompt_and_prompt_output_collision_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=runner.BASE, prefix='.offline_') as temp:
            directory = Path(temp).resolve()
            self.assertTrue(directory.is_relative_to(runner.BASE))
            source = directory / 'input.txt'; source.write_text('我买书', encoding='utf-8')
            prompt = directory / 'prompt.txt'; prompt.write_text('  \n', encoding='utf-8')
            args = ['--input', str(source), '--system-prompt', str(prompt), '--output', str(directory / 'result.txt')]
            with patch.dict(os.environ, {'VLLM_BASE_URL': 'http://offline.invalid/v1', 'VLLM_API_KEY': 'offline-test-placeholder'}), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit): runner25.main(args)
                self.assertFalse((directory / 'result.txt').exists())
                prompt.write_text('keep', encoding='utf-8')
                args = ['--input', str(source), '--system-prompt', str(prompt), '--output', str(prompt), '--overwrite']
                with self.assertRaises(SystemExit): runner25.main(args)
                self.assertEqual(prompt.read_text(encoding='utf-8'), 'keep')

if __name__ == '__main__':
    unittest.main()
