# Inference clients retained with the study

This directory makes the two client implementations saved in the local project portable. `qwen25_client.py` is the Qwen2.5-oriented client; `qwen3_client.py` uses the shared system prompt and exposes the Qwen3 thinking switch. Both accept `--model` to select a model served by the user.

These files are not presented as a complete execution log for all six historical conditions. The six archived prediction files and the offline evaluator are sufficient to recalculate the reported metrics without running a model. This package does not infer undocumented historical settings from a client default.

## Files and dependencies

- `sentences.txt` is supplied separately with the study data. It is not included in this code repository; provide the sentence file explicitly with `--input`.
- `qwen3_shared_system_prompt.txt`: the unchanged shared prompt supplied with the Qwen3 client.
- `qwen25_client.py`, `qwen3_client.py`: request construction, response separation and four-field TXT output.
- `test_clients_offline.py`: checks using a simulated SDK; it never calls a model service.

Install `requirements.txt` in the environment used for the client. The existing `../sps_converter/` converts final XML to the linear representation used by offline scoring. No database helper or database credentials are included.

Training remains a separate cloud operation using the configurations in `../../configs/`. To run inference, serve your own original or adapted checkpoint through an OpenAI-compatible endpoint. The clients neither train nor download models.

## Credentials and execution

Set `VLLM_BASE_URL` to your service endpoint and `VLLM_API_KEY` to its key in the environment. There is no built-in endpoint or key. If your service is explicitly unauthenticated, set a placeholder key yourself. A `--base-url` option can override the endpoint; keys are read only from the environment.

From the release root:

```text
python -B code/inference/qwen25_client.py --help
python -B code/inference/qwen3_client.py --help
python -B code/inference/qwen25_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking off
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking on
```

Choose a distinct `--output` for each condition when reusing a client. Defaults write under `reproduced/inference/`; they do not overwrite the archived predictions. Existing output is refused unless `--overwrite` is explicit. `--limit` supports a short trial. The numerical request defaults are retained from the local source implementations, not relabelled as the confirmed settings of every archived experiment.

The Qwen2.5 client sends the sentence annotation request as a user message. The Qwen3 client adds the supplied system prompt and controls `enable_thinking` through the request. The prompt, response-splitting logic, numerical request defaults and per-record output behavior are retained. No reference XML is sent.

Both clients write `Instruction`, `Reasoning`, `Output` and `Expression`. Qwen3 additionally writes raw response JSONL and run metadata beside its TXT. Analysis fields are separated from the final answer, complete Markdown XML fences are removed, and XML tags are not repaired. XML failures remain in the output. API failure stops the run and retains completed records.

To rescore a newly generated complete TXT:

```text
python -B code/evaluate.py --prediction reproduced/inference/YOUR_RESULT.txt
```

To verify the six archived conditions directly, run `python -B code/evaluate.py --all`.

## Offline checks

```text
python -B -m unittest discover -s code/inference -p test_clients_offline.py
```

The tests substitute SDK responses and use temporary local files. They check prompt/thinking propagation, reasoning separation, malformed XML preservation, interrupted batches, output protection and conversion through the public module. They do not assert model quality or the provenance of historical runs.
